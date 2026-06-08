"""opportunities.py — Full opportunity explorer with search & filters."""

from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

from modules import database as db, ui

ui.hero("Opportunities", "Search, filter and triage every opportunity the agent has found.")

# ── Filters ──────────────────────────────────────────────────────────────────────
with st.container():
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        opp_type = st.selectbox("Type", ["All"] + db.distinct_values("opp_type"))
    with f2:
        score = st.selectbox("Score", ["All", "High", "Medium", "Low"])
    with f3:
        industry = st.selectbox("Industry", ["All"] + db.distinct_values("industry"))
    with f4:
        date_range = st.selectbox(
            "Date", ["All time", "Last 24h", "Last 7 days", "Last 30 days"]
        )

    g1, g2, g3, g4 = st.columns(4)
    with g1:
        company = st.text_input("Company contains", "")
    with g2:
        person = st.text_input("Person contains", "")
    with g3:
        min_score = st.slider("Min score", 0, 100, 0, 5)
    with g4:
        order = st.selectbox("Sort by", ["score", "recent", "confidence"])

since = None
if date_range != "All time":
    days = {"Last 24h": 1, "Last 7 days": 7, "Last 30 days": 30}[date_range]
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

opps = db.list_opportunities(
    opp_type=opp_type,
    score_label=score,
    industry=industry,
    company=company or None,
    person=person or None,
    since=since,
    min_score=min_score,
    order=order,
)

st.caption(f"**{len(opps)}** opportunities match your filters.")

tab_cards, tab_table = st.tabs(["🃏 Cards", "📋 Table"])

with tab_cards:
    if not opps:
        st.info("No matches. Loosen the filters or run a new scan from the Home page.")
    for o in opps:
        ui.opportunity_card(o)
        a1, a2, a3, a4 = st.columns([1, 1, 1, 3])
        with a1:
            if st.button("⭐ Save", key=f"save{o['id']}"):
                db.update_opportunity_status(o["id"], "saved")
                st.rerun()
        with a2:
            if st.button("📨 Contacted", key=f"contacted{o['id']}"):
                db.update_opportunity_status(o["id"], "contacted")
                st.rerun()
        with a3:
            if st.button("🗄 Archive", key=f"arch{o['id']}"):
                db.update_opportunity_status(o["id"], "archived")
                st.rerun()
        with a4:
            st.caption(f"Status: **{o.get('status','new')}** · ✍️ Draft outreach on the Outreach page")

with tab_table:
    if opps:
        df = pd.DataFrame(opps)[
            ["score_value", "score_label", "opp_type", "person_name", "company",
             "industry", "confidence", "status", "summary"]
        ].rename(
            columns={
                "score_value": "Score",
                "score_label": "Tier",
                "opp_type": "Type",
                "person_name": "Person",
                "company": "Company",
                "industry": "Industry",
                "confidence": "Conf%",
                "status": "Status",
                "summary": "Summary",
            }
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button(
            "⬇ Export CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name="linkedin_opportunities.csv",
            mime="text/csv",
        )
    else:
        st.info("Nothing to show.")
