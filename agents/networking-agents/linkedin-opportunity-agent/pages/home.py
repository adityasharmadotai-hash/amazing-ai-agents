"""home.py — Daily opportunity feed, KPIs and the scan trigger."""

import streamlit as st

from modules import analytics, config, database as db, monitor, ui

ui.hero(
    "Today's Opportunities",
    "Your LinkedIn signal radar — hiring, buying intent, funding, partnerships & leads, scored and ready to action.",
)

keywords = st.session_state.get("keywords", [])
industries = st.session_state.get("industries", [])

# ── Action bar ───────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([1.4, 1, 1])
with c1:
    scan = st.button("🔍 Scan LinkedIn now", type="primary", use_container_width=True)
with c2:
    limit = st.selectbox("Posts per scan", [6, 12, 20, 30], index=1, label_visibility="collapsed")
with c3:
    st.caption(f"Engine: **{'OpenAI' if config.ai_enabled() else 'Keyword fallback'}**")

if scan:
    with st.spinner("Fetching posts and analysing opportunities…"):
        summary = monitor.run_scan(keywords, industries, limit=limit)
        analytics.save_today_snapshot()
    if summary["fetched"] == 0 and summary["opportunities"] == 0:
        st.info(
            "No new posts in this batch (the sample source is exhausted — every demo post "
            "is already ingested). Paste a real post on the Settings page, or wire in a live "
            "data source via `monitor.set_source`."
        )
    else:
        st.success(
            f"Scan complete · {summary['fetched']} new posts · "
            f"{summary['opportunities']} opportunities "
            f"({summary['high']} High / {summary['medium']} Medium / {summary['low']} Low)",
            icon="✅",
        )

# ── KPIs ─────────────────────────────────────────────────────────────────────────
k = analytics.kpis()
ui.kpi_row(
    [
        (k["total"], "Opportunities", f"avg score {k['avg_score']}"),
        (k["high"], "High value", "score ≥ 75"),
        (k["medium"], "Medium", "score 50-74"),
        (analytics.top_industry(), "Top industry", ""),
    ]
)

# ── Feed ─────────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>Top opportunities</div>", unsafe_allow_html=True)

colf1, colf2 = st.columns([1, 1])
with colf1:
    type_filter = st.selectbox("Type", ["All"] + db.distinct_values("opp_type"), index=0)
with colf2:
    label_filter = st.selectbox("Score", ["All", "High", "Medium", "Low"], index=0)

opps = db.list_opportunities(
    opp_type=type_filter, score_label=label_filter, order="score"
)

if not opps:
    st.info("No opportunities yet. Click **Scan LinkedIn now** above to populate the feed.")
else:
    for o in opps[:12]:
        ui.opportunity_card(o)
    if len(opps) > 12:
        st.caption(f"+ {len(opps) - 12} more on the Opportunities page →")
