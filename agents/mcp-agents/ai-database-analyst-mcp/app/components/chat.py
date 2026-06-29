"""Chat interface: natural-language questions and a manual-SQL escape hatch."""

from __future__ import annotations

from typing import Optional

import streamlit as st

from app.components.results import render_analysis
from app.context import AnalystContext
from core.exceptions import DatabaseAnalystError
from core.models import AnalysisResult, ChatRole

_EXAMPLES = [
    "Show today's sales",
    "Top 20 customers by revenue",
    "Revenue by month",
    "Find duplicate users",
    "Most profitable products",
    "Which tables contain email?",
]


def render_chat() -> None:
    """Render the full chat experience."""
    ctx: Optional[AnalystContext] = st.session_state.get("ctx")
    if ctx is None:
        st.info("👈 Connect to a database from the sidebar to start chatting with your data.")
        _render_examples(disabled=True)
        return

    _render_examples(disabled=False)
    _render_history(ctx)

    # Handle queued SQL (from saved queries / re-run buttons).
    pending_sql = st.session_state.pop("pending_sql", None)
    if pending_sql:
        _run_manual_sql(ctx, pending_sql)

    # Manual SQL editor.
    with st.expander("⌨️ Run SQL manually"):
        sql_text = st.text_area("SQL", height=120, key="manual_sql_input", placeholder="SELECT * FROM ...")
        if st.button("Execute SQL", key="manual_sql_run") and sql_text.strip():
            _run_manual_sql(ctx, sql_text.strip())

    # Chat input (or a queued example question).
    queued = st.session_state.pop("queued_question", None)
    question = st.chat_input("Ask a question about your data…")
    if queued:
        question = queued
    if question:
        _ask(ctx, question)


def _render_examples(disabled: bool) -> None:
    st.caption("Try an example:")
    cols = st.columns(3)
    for i, example in enumerate(_EXAMPLES):
        if cols[i % 3].button(example, key=f"ex_{i}", disabled=disabled, use_container_width=True):
            st.session_state.queued_question = example
            st.rerun()


def _render_history(ctx: AnalystContext) -> None:
    for idx, msg in enumerate(ctx.memory.messages):
        role = "user" if msg.role == ChatRole.USER else "assistant"
        with st.chat_message(role):
            st.markdown(msg.content)
            if msg.analysis is not None:
                render_analysis(ctx, msg.analysis, key=f"hist_{idx}")


def _ask(ctx: AnalystContext, question: str) -> None:
    ctx.memory.add_user_message(question)
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Analysing your database…"):
            try:
                analysis = ctx.agent.answer(question, ctx.memory)
            except DatabaseAnalystError as exc:
                analysis = AnalysisResult(question=question, plan=_empty_plan(), error=str(exc))
        summary = _summary_text(analysis)
        st.markdown(summary)
        render_analysis(ctx, analysis, key=f"live_{len(ctx.memory.messages)}")
    ctx.memory.add_assistant_message(summary, analysis=analysis)


def _run_manual_sql(ctx: AnalystContext, sql: str) -> None:
    label = f"Run SQL: `{sql[:60]}`"
    ctx.memory.add_user_message(label)
    with st.chat_message("user"):
        st.markdown(label)
    with st.chat_message("assistant"):
        with st.spinner("Executing…"):
            try:
                analysis = ctx.agent.run_sql(sql)
            except DatabaseAnalystError as exc:
                analysis = AnalysisResult(question=sql, plan=_empty_plan(), error=str(exc))
        summary = _summary_text(analysis)
        st.markdown(summary)
        render_analysis(ctx, analysis, key=f"manual_{len(ctx.memory.messages)}")
    ctx.memory.add_assistant_message(summary, analysis=analysis)


def _summary_text(analysis: AnalysisResult) -> str:
    if analysis.error and analysis.result is None:
        if analysis.plan.needs_confirmation:
            return "⚠️ This looks like a data-modifying request — see the confirmation below."
        return f"❌ {analysis.error}"
    if analysis.result is not None:
        intent = analysis.plan.intent or "Here are your results"
        return f"✅ {intent} — {analysis.result.row_count} row(s)."
    return "Done."


def _empty_plan():
    from core.models import QueryPlan

    return QueryPlan()
