"""Chart rendering component."""

from __future__ import annotations

from typing import Optional

import streamlit as st

from app.context import AnalystContext
from core.models import ChartSpec, ChartType, QueryResult


def render_chart(ctx: AnalystContext, result: QueryResult, spec: Optional[ChartSpec], key: str) -> None:
    """Render a Plotly chart with a small control to switch chart type."""
    if result is None or not result.rows:
        return

    spec = spec or ctx.chart_service.recommend(result)
    chart_types = [c.value for c in ChartType]
    current = spec.chart_type.value if spec else ChartType.BAR.value

    col1, col2 = st.columns([3, 1])
    with col2:
        chosen = st.selectbox(
            "Chart type",
            chart_types,
            index=chart_types.index(current) if current in chart_types else 0,
            key=f"charttype_{key}",
        )
    spec.chart_type = ChartType(chosen)

    if spec.chart_type == ChartType.TABLE:
        with col1:
            st.dataframe(ctx.chart_service.to_dataframe(result), use_container_width=True)
        return

    figure = ctx.chart_service.build_figure(result, spec)
    with col1:
        if figure is not None:
            st.plotly_chart(figure, use_container_width=True, key=f"plot_{key}")
            if spec.reason:
                st.caption(f"💡 {spec.reason}")
        else:
            st.info("No suitable chart could be generated for this result.")
