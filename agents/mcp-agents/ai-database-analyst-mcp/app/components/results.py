"""Results panel: SQL, metrics, table, charts, insights, recommendations, exports."""

from __future__ import annotations

import streamlit as st

from app.components.charts import render_chart
from app.context import AnalystContext
from core.exceptions import DatabaseAnalystError
from core.models import AnalysisResult
from utils.formatting import format_duration
from utils.sql_utils import format_sql


def render_analysis(ctx: AnalystContext, analysis: AnalysisResult, key: str) -> None:
    """Render a full analysis result block."""
    if analysis.error and analysis.result is None:
        if analysis.plan.needs_confirmation:
            _render_write_confirmation(ctx, analysis, key)
        else:
            st.error(analysis.error)
        if analysis.plan.sql:
            _render_sql(ctx, analysis, key)
        return

    _render_sql(ctx, analysis, key)

    result = analysis.result
    if result is None:
        return

    # Metrics row
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(_metric("Rows", str(result.row_count)), unsafe_allow_html=True)
    m2.markdown(_metric("Execution", format_duration(result.execution_time_ms)), unsafe_allow_html=True)
    m3.markdown(_metric("Columns", str(len(result.columns))), unsafe_allow_html=True)
    m4.markdown(
        _metric("Mode", "Write" if not ctx.guard.read_only else "Read-only"),
        unsafe_allow_html=True,
    )

    if result.truncated:
        st.warning(f"Result truncated to {result.row_count} rows for display.")

    tabs = st.tabs(["📋 Results", "📊 Chart", "🧠 Insights", "🛠 Recommendations", "🔎 SQL & Plan"])

    with tabs[0]:
        if result.rows:
            st.dataframe(ctx.chart_service.to_dataframe(result), use_container_width=True, height=360)
        else:
            st.info("Query executed successfully; no rows returned.")
        _render_downloads(ctx, analysis, key)

    with tabs[1]:
        render_chart(ctx, result, analysis.chart_spec, key)

    with tabs[2]:
        if analysis.insights:
            st.markdown(f'<div class="insight-box">{analysis.insights}</div>', unsafe_allow_html=True)
        else:
            st.caption("No AI insights (configure a Gemini API key to enable).")

    with tabs[3]:
        if analysis.recommendations:
            for rec in analysis.recommendations:
                st.markdown(f"- {rec}")
        else:
            st.caption("No recommendations for this query.")

    with tabs[4]:
        _render_sql_and_plan(ctx, analysis, key)


def _metric(label: str, value: str) -> str:
    return f'<div class="metric-card"><div class="label">{label}</div><div class="value">{value}</div></div>'


def _render_sql(ctx: AnalystContext, analysis: AnalysisResult, key: str) -> None:
    if not analysis.plan.sql:
        return
    st.markdown('<div class="sql-label">Generated SQL</div>', unsafe_allow_html=True)
    st.code(format_sql(analysis.plan.sql), language="sql")
    cols = st.columns([1, 1, 4])
    with cols[0]:
        with st.popover("💾 Save"):
            name = st.text_input("Name", key=f"savename_{key}")
            if st.button("Save query", key=f"savebtn_{key}") and name.strip():
                ctx.memory.save_query(name, analysis.plan.sql)
                st.success("Saved.")
    with cols[1]:
        if st.button("🔁 Re-run", key=f"rerun_{key}"):
            st.session_state.pending_sql = analysis.plan.sql
            st.rerun()


def _render_sql_and_plan(ctx: AnalystContext, analysis: AnalysisResult, key: str) -> None:
    if analysis.sql_explanation:
        st.markdown("**Explanation**")
        st.markdown(analysis.sql_explanation)
    if analysis.plan.assumptions:
        st.markdown("**Assumptions**")
        for a in analysis.plan.assumptions:
            st.markdown(f"- {a}")
    if st.button("Show execution plan", key=f"plan_{key}"):
        try:
            plan = ctx.agent.explain_plan(analysis.plan.sql)
            if plan and plan.rows:
                st.dataframe(ctx.chart_service.to_dataframe(plan), use_container_width=True)
            else:
                st.info("No execution plan available for this query.")
        except DatabaseAnalystError as exc:
            st.error(str(exc))


def _render_downloads(ctx: AnalystContext, analysis: AnalysisResult, key: str) -> None:
    result = analysis.result
    if result is None or not result.rows:
        return
    st.markdown("##### ⬇️ Download")
    c1, c2, c3, c4, c5 = st.columns(5)
    try:
        c1.download_button(
            "CSV", ctx.export_service.to_csv(result, persist=False),
            file_name="result.csv", mime="text/csv", key=f"dl_csv_{key}", use_container_width=True,
        )
        c2.download_button(
            "Excel", ctx.export_service.to_excel(result, persist=False),
            file_name="result.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"dl_xlsx_{key}", use_container_width=True,
        )
        c3.download_button(
            "JSON", ctx.export_service.to_json(result, persist=False),
            file_name="result.json", mime="application/json", key=f"dl_json_{key}", use_container_width=True,
        )
    except DatabaseAnalystError as exc:
        st.error(f"Export error: {exc}")

    if c4.button("📄 PDF Report", key=f"dl_pdf_{key}", use_container_width=True):
        _build_and_offer_report(ctx, analysis, key, fmt="pdf")
    if c5.button("📝 MD Report", key=f"dl_md_{key}", use_container_width=True):
        _build_and_offer_report(ctx, analysis, key, fmt="md")


def _build_and_offer_report(ctx: AnalystContext, analysis: AnalysisResult, key: str, fmt: str) -> None:
    result = analysis.result
    if result is None:
        return
    with st.spinner("Generating report…"):
        report_md = ctx.report_service.generate(analysis.question, result)
    try:
        if fmt == "pdf":
            data = ctx.export_service.to_pdf("AI Database Report", report_md, result=result, persist=True)
            st.download_button(
                "Download PDF", data, file_name="report.pdf", mime="application/pdf",
                key=f"dl_pdf_final_{key}", use_container_width=True,
            )
        else:
            data = ctx.export_service.to_markdown("AI Database Report", report_md, result=result, persist=True)
            st.download_button(
                "Download Markdown", data, file_name="report.md", mime="text/markdown",
                key=f"dl_md_final_{key}", use_container_width=True,
            )
        with st.expander("Preview report"):
            st.markdown(report_md)
    except DatabaseAnalystError as exc:
        st.error(f"Report error: {exc}")


def _render_write_confirmation(ctx: AnalystContext, analysis: AnalysisResult, key: str) -> None:
    st.warning(
        "⚠️ This request would modify data and is blocked in read-only mode. "
        "Review the SQL below. Enable **Write mode** in Settings to run it."
    )
    if st.session_state.get("write_mode_enabled"):
        st.info("Write mode is enabled. Confirm to execute this statement.")
        if st.button("✅ Confirm and execute", key=f"confirm_write_{key}", type="primary"):
            try:
                ctx.set_read_only(False)
                result = ctx.agent.run_sql(analysis.plan.sql, analysis.question)
                ctx.set_read_only(not st.session_state.get("write_mode_enabled", False))
                st.session_state.setdefault("forced_results", []).append(result)
                st.rerun()
            except DatabaseAnalystError as exc:
                st.error(str(exc))
