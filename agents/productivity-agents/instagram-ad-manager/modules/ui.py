"""
ui.py — reusable Streamlit + Plotly rendering helpers.

Keeps `app.py` declarative: one call to render the theme, hero headers, KPI rows,
consistently-styled charts, the health gauge, forecast chart, and notifications.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from . import theme

_FONT = "Inter, sans-serif"

# Per-run, per-session counter so every chart gets a unique, stable key (avoids
# StreamlitDuplicateElementId when a page renders several similar charts). Stored
# in session_state so concurrent users on the same server don't collide.
_KEY = "_chart_key_n"


def reset_keys() -> None:
    """Call once at the top of each script run before rendering charts."""
    st.session_state[_KEY] = 0


def _next_key(prefix: str = "chart") -> str:
    st.session_state[_KEY] = st.session_state.get(_KEY, 0) + 1
    return f"{prefix}_{st.session_state[_KEY]}"


def inject_theme() -> None:
    st.markdown(theme.CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str, chip: str = "") -> None:
    st.markdown(theme.hero(title, subtitle, chip), unsafe_allow_html=True)


def section(title: str, desc: str = "", icon: str = "✨") -> None:
    st.markdown(theme.section(title, desc, icon), unsafe_allow_html=True)


def kpis(cards: list[str]) -> None:
    st.markdown(theme.kpi_grid(cards), unsafe_allow_html=True)


# ── Plotly styling ────────────────────────────────────────────────────────────
def style_fig(fig: go.Figure, height: int = 300, legend: bool = False) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=_FONT, size=12, color="#4b5563"),
        colorway=theme.GRADIENT_SEQ,
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        hoverlabel=dict(bgcolor="white", font_size=12, font_family=_FONT),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, showline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(131,58,180,0.10)", zeroline=False)
    return fig


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def area(df: pd.DataFrame, x: str, y: str, color: str = theme.PURPLE, height: int = 280) -> None:
    if df.empty:
        st.caption("No data in range.")
        return
    fig = go.Figure(
        go.Scatter(
            x=df[x], y=df[y], mode="lines", line=dict(color=color, width=2.5, shape="spline"),
            fill="tozeroy", fillcolor=_hex_to_rgba(color, 0.16),
        )
    )
    st.plotly_chart(style_fig(fig, height), width="stretch", key=_next_key("area"),
                    config={"displayModeBar": False})


def line(df: pd.DataFrame, x: str, y: str, color: str = theme.PINK, height: int = 280) -> None:
    if df.empty:
        st.caption("No data in range.")
        return
    fig = go.Figure(
        go.Scatter(x=df[x], y=df[y], mode="lines+markers",
                   line=dict(color=color, width=2.5, shape="spline"),
                   marker=dict(size=6, color=color))
    )
    st.plotly_chart(style_fig(fig, height), width="stretch", key=_next_key("line"),
                    config={"displayModeBar": False})


def bars(df: pd.DataFrame, x: str, y: str, color: str = theme.ORANGE, height: int = 280) -> None:
    if df.empty:
        st.caption("No data in range.")
        return
    fig = go.Figure(go.Bar(x=df[x], y=df[y], marker=dict(color=color, line=dict(width=0)),
                           marker_line_width=0))
    fig.update_traces(marker_cornerradius=6)
    st.plotly_chart(style_fig(fig, height), width="stretch", key=_next_key("bars"),
                    config={"displayModeBar": False})


def hbar_gradient(df: pd.DataFrame, value: str, label: str, height: int = 300, reverse=False) -> None:
    if df.empty:
        st.caption("No data.")
        return
    d = df.sort_values(value, ascending=not reverse)
    fig = go.Figure(go.Bar(
        x=d[value], y=d[label], orientation="h",
        marker=dict(color=d[value], colorscale=theme.CONTINUOUS, showscale=False),
    ))
    fig.update_traces(marker_cornerradius=6)
    st.plotly_chart(style_fig(fig, height), width="stretch", key=_next_key("hbar"),
                    config={"displayModeBar": False})


def donut(labels: list[str], values: list[float], height: int = 300) -> None:
    if not values:
        st.caption("No data.")
        return
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.55,
                           marker=dict(colors=theme.GRADIENT_SEQ),
                           textinfo="percent", sort=True))
    st.plotly_chart(style_fig(fig, height, legend=True), width="stretch", key=_next_key("donut"),
                    config={"displayModeBar": False})


def gauge(score: float, height: int = 260) -> None:
    """Marketing-health gauge (0–100)."""
    score = max(0, min(100, float(score)))
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(score),
        number=dict(font=dict(size=40, family="Sora, sans-serif", color=theme.MAGENTA)),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor="#cbb5e6"),
            bar=dict(color=theme.PINK, thickness=0.28),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            steps=[
                {"range": [0, 40], "color": "rgba(220,38,38,0.14)"},
                {"range": [40, 70], "color": "rgba(217,119,6,0.14)"},
                {"range": [70, 100], "color": "rgba(22,163,74,0.16)"},
            ],
        ),
    ))
    fig.update_layout(height=height, margin=dict(l=20, r=20, t=10, b=0),
                      paper_bgcolor="rgba(0,0,0,0)", font=dict(family=_FONT))
    st.plotly_chart(fig, width="stretch", key=_next_key("gauge"), config={"displayModeBar": False})


def forecast_chart(history: list[dict], forecast: list[dict], y: str = "value", height: int = 300) -> None:
    """history/forecast: lists of {date, value[, lower, upper]}."""
    if not history and not forecast:
        st.caption("Not enough data to forecast.")
        return
    fig = go.Figure()
    if history:
        hx = [h["date"] for h in history]
        hy = [h[y] for h in history]
        fig.add_trace(go.Scatter(x=hx, y=hy, mode="lines", name="Actual",
                                 line=dict(color=theme.PURPLE, width=2.5, shape="spline")))
    if forecast:
        fx = [f["date"] for f in forecast]
        fy = [f[y] for f in forecast]
        if all("upper" in f and "lower" in f for f in forecast):
            fig.add_trace(go.Scatter(x=fx + fx[::-1],
                                     y=[f["upper"] for f in forecast] + [f["lower"] for f in forecast][::-1],
                                     fill="toself", fillcolor=_hex_to_rgba(theme.ORANGE, 0.12),
                                     line=dict(width=0), hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=fx, y=fy, mode="lines+markers", name="Forecast",
                                 line=dict(color=theme.ORANGE, width=2.5, dash="dash"),
                                 marker=dict(size=5)))
    st.plotly_chart(style_fig(fig, height, legend=True), width="stretch", key=_next_key("forecast"),
                    config={"displayModeBar": False})


# ── Health + notifications ────────────────────────────────────────────────────
def health_components(components: list[dict]) -> None:
    html = '<div class="glass">'
    for c in components:
        pct = max(0, min(100, c.get("score", 0)))
        html += (
            f'<div class="comp"><div class="cn">{c.get("name","")}</div>'
            f'<div class="bar"><div class="fill" style="width:{pct}%"></div></div>'
            f'<div class="cv">{round(pct)}</div></div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def notifications(items: list[dict]) -> None:
    if not items:
        st.caption("You're all caught up — no notifications.")
        return
    st.markdown("".join(theme.notification_html(n) for n in items), unsafe_allow_html=True)
