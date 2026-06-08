"""analytics.py — Analytics dashboard: KPIs, distributions, trends & digests."""

import plotly.express as px
import streamlit as st

from modules import alerts, analytics, config, ui

ui.hero("Analytics", "Opportunity trends, top industries, hiring & funding signals, and history.")

PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#dbe5f1",
    margin=dict(l=10, r=10, t=40, b=10),
)

k = analytics.kpis()
ui.kpi_row(
    [
        (k["total"], "Total opportunities", ""),
        (k["high"], "High value", ""),
        (f"{k['avg_score']}", "Avg score", ""),
        (f"{k['avg_confidence']}%", "Avg confidence", ""),
    ]
)

# ── Distributions ────────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)
with c1:
    st.markdown("<div class='section-title'>By opportunity type</div>", unsafe_allow_html=True)
    df_type = analytics.by_type()
    if df_type.empty:
        st.caption("No data yet.")
    else:
        fig = px.bar(df_type, x="Count", y="Type", orientation="h",
                     color="Count", color_continuous_scale="Blues")
        fig.update_layout(**PLOTLY_THEME, height=320, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

with c2:
    st.markdown("<div class='section-title'>By lead score</div>", unsafe_allow_html=True)
    df_score = analytics.by_score_label()
    if df_score["Count"].sum() == 0:
        st.caption("No data yet.")
    else:
        fig = px.pie(df_score, names="Score", values="Count", hole=0.55,
                     color="Score",
                     color_discrete_map={"High": "#16a34a", "Medium": "#d97706", "Low": "#64748b"})
        fig.update_layout(**PLOTLY_THEME, height=320)
        st.plotly_chart(fig, use_container_width=True)

# ── Industries + companies ───────────────────────────────────────────────────────
c3, c4 = st.columns(2)
with c3:
    st.markdown("<div class='section-title'>Top industries</div>", unsafe_allow_html=True)
    df_ind = analytics.by_industry()
    if df_ind.empty:
        st.caption("No data yet.")
    else:
        fig = px.bar(df_ind, x="Count", y="Industry", orientation="h",
                     color="Count", color_continuous_scale="Teal")
        fig.update_layout(**PLOTLY_THEME, height=320, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
with c4:
    st.markdown("<div class='section-title'>Top companies</div>", unsafe_allow_html=True)
    df_co = analytics.top_companies()
    if df_co.empty:
        st.caption("No data yet.")
    else:
        st.dataframe(df_co, use_container_width=True, hide_index=True)

# ── Trends ───────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>Trends over time</div>", unsafe_allow_html=True)
t1, t2 = st.columns(2)
with t1:
    df_hire = analytics.hiring_trends()
    if df_hire.empty:
        st.caption("No hiring-signal history yet.")
    else:
        fig = px.area(df_hire, x="date", y="count", title="Hiring signals")
        fig.update_traces(line_color="#0a66c2", fillcolor="rgba(10,102,194,0.25)")
        fig.update_layout(**PLOTLY_THEME, height=280)
        st.plotly_chart(fig, use_container_width=True)
with t2:
    df_fund = analytics.funding_trends()
    if df_fund.empty:
        st.caption("No funding-signal history yet.")
    else:
        fig = px.area(df_fund, x="date", y="count", title="Funding signals")
        fig.update_traces(line_color="#16a34a", fillcolor="rgba(22,163,74,0.25)")
        fig.update_layout(**PLOTLY_THEME, height=280)
        st.plotly_chart(fig, use_container_width=True)

df_all = analytics.opportunities_over_time()
if not df_all.empty:
    fig = px.line(df_all, x="date", y="count", markers=True, title="Opportunities found per day")
    fig.update_traces(line_color="#7ab8f5")
    fig.update_layout(**PLOTLY_THEME, height=280)
    st.plotly_chart(fig, use_container_width=True)

# ── Alerts / Digests ─────────────────────────────────────────────────────────────
st.divider()
st.markdown("<div class='section-title'>Alerts & digests</div>", unsafe_allow_html=True)
period = st.radio("Digest period", ["daily", "weekly"], horizontal=True,
                  format_func=lambda p: "Daily digest" if p == "daily" else "Weekly digest")
digest = alerts.build_digest(period)

d1, d2 = st.columns([1, 1])
with d1:
    st.markdown(f"**Preview** — {digest['count']} opportunities")
    st.markdown(digest["html"], unsafe_allow_html=True)
with d2:
    if config.smtp_configured():
        if st.button(f"📧 Send {period} digest", type="primary"):
            ok, message = alerts.send_digest(period)
            (st.success if ok else st.error)(message)
    else:
        st.info("Configure email (SMTP) on the **Settings** page to send digests. "
                "The preview works without any setup.")
    st.download_button(
        "⬇ Download digest (.txt)",
        digest["text"].encode("utf-8"),
        file_name=f"opportunity_digest_{period}.txt",
    )
