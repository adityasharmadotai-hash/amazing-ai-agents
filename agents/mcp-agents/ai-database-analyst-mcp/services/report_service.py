"""AI report service.

Generates executive reports (Executive Summary, Business Insights, Key Metrics,
Recommendations, Anomalies, Opportunities) from a query result using the LLM.
"""

from __future__ import annotations

import json
from typing import Optional

from agents.gemini_client import GeminiClient
from core.logging_config import get_logger
from core.models import QueryResult
from prompts.templates import REPORT_PROMPT, SYSTEM_PROMPT

logger = get_logger(__name__)


class ReportService:
    """Builds AI-written reports from result sets."""

    def __init__(self, llm: Optional[GeminiClient]) -> None:
        self.llm = llm

    def generate(self, question: str, result: QueryResult, sample_rows: int = 30) -> str:
        """Return a markdown executive report for the result."""
        if self.llm is None:
            return self._fallback(question, result)

        sample = json.dumps(result.to_records()[:sample_rows], default=str)
        prompt = REPORT_PROMPT.format(
            system=SYSTEM_PROMPT,
            question=question,
            columns=", ".join(result.columns),
            row_count=result.row_count,
            sample=sample,
        )
        try:
            response = self.llm.complete(prompt, temperature=0.3)
            return response.strip_code_fences()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Report generation failed: %s", exc)
            return self._fallback(question, result)

    def _fallback(self, question: str, result: QueryResult) -> str:
        """A deterministic report when no LLM is available."""
        return (
            f"## Executive Summary\n"
            f"Query for '{question}' returned {result.row_count} rows in "
            f"{result.execution_time_ms} ms.\n\n"
            f"## Business Insights\n- Columns analysed: {', '.join(result.columns)}.\n\n"
            f"## Key Metrics\n- Rows: {result.row_count}\n- "
            f"Execution time: {result.execution_time_ms} ms\n\n"
            f"## Recommendations\n- Configure a Gemini API key to enable AI-written insights.\n\n"
            f"## Anomalies\n- None detected automatically.\n\n"
            f"## Opportunities\n- Add an API key for deeper, automated analysis."
        )
