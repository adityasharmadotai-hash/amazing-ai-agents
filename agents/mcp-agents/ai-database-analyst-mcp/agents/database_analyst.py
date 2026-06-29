"""The AI Database Analyst agent.

Orchestrates the full natural-language-to-insight pipeline:
understand intent -> inspect schema -> identify tables -> generate SQL ->
validate -> optimise -> execute -> summarise -> recommend -> visualise ->
explain SQL / execution plan.
"""

from __future__ import annotations

import json
from typing import Optional

from agents.gemini_client import GeminiClient
from core.exceptions import (
    AIAgentError,
    DatabaseAnalystError,
    UnsafeSQLError,
)
from core.logging_config import get_logger
from core.models import (
    AnalysisResult,
    ChartSpec,
    ChartType,
    QueryPlan,
    QueryResult,
    SchemaInfo,
)
from core.session import SessionMemory
from database.repository import DatabaseRepository
from database.safe_sql import SafeSQLGuard
from prompts.templates import (
    CHART_RECOMMENDATION_PROMPT,
    INSIGHTS_PROMPT,
    SQL_EXPLAIN_PROMPT,
    SQL_GENERATION_PROMPT,
    SYSTEM_PROMPT,
)
from services.chart_service import ChartService
from services.optimization_service import OptimizationService

logger = get_logger(__name__)


class DatabaseAnalystAgent:
    """End-to-end natural-language database analyst."""

    def __init__(
        self,
        repository: DatabaseRepository,
        llm: Optional[GeminiClient],
        chart_service: ChartService,
        optimization_service: OptimizationService,
        guard: SafeSQLGuard,
        *,
        auto_explain: bool = True,
        auto_charts: bool = True,
    ) -> None:
        self.repo = repository
        self.llm = llm
        self.charts = chart_service
        self.optimizer = optimization_service
        self.guard = guard
        self.auto_explain = auto_explain
        self.auto_charts = auto_charts

    # --- public entry point ----------------------------------------------
    def answer(self, question: str, memory: SessionMemory) -> AnalysisResult:
        """Answer a natural-language question end to end."""
        logger.info("Question: %s", question)
        schema = self._ensure_schema(memory)

        if self.llm is None:
            return AnalysisResult(
                question=question,
                plan=QueryPlan(intent="(no LLM configured)"),
                error="No Gemini API key configured. Add one in Settings to ask questions.",
            )

        try:
            plan = self._plan(question, schema, memory)
        except DatabaseAnalystError as exc:
            return AnalysisResult(question=question, plan=QueryPlan(), error=str(exc))

        analysis = AnalysisResult(question=question, plan=plan)

        # Safety gate: write statements require explicit write mode.
        try:
            self.guard.validate(plan.sql)
        except UnsafeSQLError as exc:
            plan.is_write = True
            plan.needs_confirmation = True
            analysis.error = str(exc)
            return analysis

        # Execute.
        try:
            result = self.repo.execute(plan.sql)
        except DatabaseAnalystError as exc:
            analysis.error = str(exc)
            return analysis

        analysis.result = result
        memory.last_sql = plan.sql
        memory.last_result = result

        # Post-processing: insights, recommendations, chart, explanation.
        self._enrich(question, analysis)
        return analysis

    def run_sql(self, sql: str, question: str = "(manual SQL)") -> AnalysisResult:
        """Execute a user-provided SQL string with the same safety/enrichment."""
        plan = QueryPlan(intent="Manual SQL execution", sql=sql, explanation="User-supplied SQL.")
        analysis = AnalysisResult(question=question, plan=plan)
        try:
            self.guard.validate(sql)
            analysis.result = self.repo.execute(sql)
        except DatabaseAnalystError as exc:
            analysis.error = str(exc)
            return analysis
        self._enrich(question, analysis)
        return analysis

    # --- pipeline steps ---------------------------------------------------
    def _ensure_schema(self, memory: SessionMemory) -> SchemaInfo:
        schema = memory.get_schema()
        if schema is None:
            schema = self.repo.get_schema(include_row_counts=True)
            memory.set_schema(schema)
        return schema

    def _plan(self, question: str, schema: SchemaInfo, memory: SessionMemory) -> QueryPlan:
        """Ask the LLM to produce a structured query plan (intent + SQL)."""
        prompt = SQL_GENERATION_PROMPT.format(
            system=SYSTEM_PROMPT,
            dialect=self.repo.dialect,
            schema=schema.to_prompt_text(),
            history=memory.recent_dialogue(turns=6) or "(none)",
            last_sql=memory.last_sql or "(none)",
            question=question,
        )
        response = self.llm.complete(prompt)
        data = response.extract_json()

        sql = (data.get("sql") or "").strip().rstrip(";")
        if not sql:
            raise AIAgentError("The AI did not produce a SQL statement for this question.")

        is_write = bool(data.get("is_write")) or self.guard.is_write(sql)
        return QueryPlan(
            intent=str(data.get("intent", "")),
            relevant_tables=list(data.get("relevant_tables", []) or []),
            sql=sql,
            explanation=str(data.get("explanation", "")),
            is_write=is_write,
            needs_confirmation=is_write,
            assumptions=list(data.get("assumptions", []) or []),
        )

    def _enrich(self, question: str, analysis: AnalysisResult) -> None:
        result = analysis.result
        if result is None or not result.success:
            return

        # SQL optimisation feeds recommendations.
        try:
            schema = self.repo.get_schema(include_row_counts=False)
            opt = self.optimizer.analyze(analysis.plan.sql, schema)
            analysis.recommendations.extend(opt.suggestions)
            analysis.recommendations.extend(f"Index suggestion: {m}" for m in opt.missing_indexes)
            analysis.recommendations.extend(f"Warning: {w}" for w in opt.warnings)
        except DatabaseAnalystError as exc:
            logger.debug("Optimisation skipped: %s", exc)

        if not result.rows:
            analysis.insights = "The query executed successfully but returned no rows."
            return

        # Insights (LLM).
        analysis.insights = self._insights(question, result)

        # Auto-explain SQL.
        if self.auto_explain:
            analysis.sql_explanation = self.explain_sql(analysis.plan.sql)

        # Auto chart.
        if self.auto_charts:
            analysis.chart_spec = self._chart_spec(result)

    def _insights(self, question: str, result: QueryResult) -> str:
        if self.llm is None:
            return ""
        sample = json.dumps(result.to_records()[:30], default=str)
        prompt = INSIGHTS_PROMPT.format(
            system=SYSTEM_PROMPT,
            question=question,
            row_count=result.row_count,
            columns=", ".join(result.columns),
            sample=sample,
        )
        try:
            return self.llm.complete(prompt, temperature=0.3).strip_code_fences()
        except DatabaseAnalystError as exc:
            logger.warning("Insight generation failed: %s", exc)
            return ""

    def _chart_spec(self, result: QueryResult) -> Optional[ChartSpec]:
        """Pick a chart: ask the LLM, fall back to heuristic recommendation."""
        heuristic = self.charts.recommend(result)
        if self.llm is None or not result.rows:
            return heuristic
        sample = json.dumps(result.to_records()[:20], default=str)
        prompt = CHART_RECOMMENDATION_PROMPT.format(
            columns=", ".join(result.columns), sample=sample
        )
        try:
            data = self.llm.complete(prompt, temperature=0.0).extract_json()
            return ChartSpec(
                chart_type=ChartType(str(data.get("chart_type", "bar")).lower()),
                x=data.get("x") or heuristic.x,
                y=list(data.get("y") or []) or heuristic.y,
                color=data.get("color"),
                title=str(data.get("title") or heuristic.title),
                reason=str(data.get("reason") or heuristic.reason),
            )
        except (DatabaseAnalystError, ValueError) as exc:
            logger.debug("LLM chart recommendation failed (%s); using heuristic", exc)
            return heuristic

    # --- standalone capabilities -----------------------------------------
    def explain_sql(self, sql: str) -> str:
        """Explain a SQL statement in plain language."""
        if self.llm is None:
            return ""
        prompt = SQL_EXPLAIN_PROMPT.format(
            system=SYSTEM_PROMPT, dialect=self.repo.dialect, sql=sql
        )
        try:
            return self.llm.complete(prompt, temperature=0.2).strip_code_fences()
        except DatabaseAnalystError as exc:
            logger.warning("SQL explanation failed: %s", exc)
            return ""

    def explain_plan(self, sql: str) -> Optional[QueryResult]:
        """Return the database execution plan for a query."""
        try:
            return self.repo.explain(sql)
        except DatabaseAnalystError as exc:
            logger.warning("EXPLAIN failed: %s", exc)
            return None
