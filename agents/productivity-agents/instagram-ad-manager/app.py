"""
app.py — Instagram AI Ad Manager · Premium AI Marketing Assistant

A polished Streamlit dashboard over the live Meta Marketing API + Gemini 2.5 Pro:
campaign monitoring, AI analysis, forecasting, a marketing health score, audience
insights, creative ideas, a notification center, and continuous-learning
recommendations. Heavy work runs in the background sync job (see sync.py); this
app displays the latest synchronized data and offers a manual "Sync Now".
"""

import os
import sys
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

from modules import (  # noqa: E402
    agent, analytics, config, database as db, demo_seed, meta_api, sync_service, theme, ui,
)

st.set_page_config(page_title=config.APP_NAME, page_icon="📈", layout="wide",
                   initial_sidebar_state="expanded")
ui.inject_theme()
ui.reset_keys()  # stable, unique chart keys per run (prevents DuplicateElementId)
db.init_db()

# ── Runtime API keys (entered on the Settings page) ───────────────────────────
_KEY_ENV = {"k_gemini": "GEMINI_API_KEY", "k_meta_token": "META_ACCESS_TOKEN",
            "k_meta_acct": "META_AD_ACCOUNT_ID"}


def _apply_session_keys():
    for sk, env in _KEY_ENV.items():
        val = st.session_state.get(sk)
        if val:
            os.environ[env] = val.strip()


_apply_session_keys()

# ── Filters (§8) ──────────────────────────────────────────────────────────────
PRESETS = ["Today", "Yesterday", "Last 7 days", "Last 30 days", "Last 10 weeks", "All time", "Custom range"]


def resolve_range(preset, custom):
    today = date.today()
    ranges = {
        "Today": (today, today),
        "Yesterday": (today - timedelta(days=1), today - timedelta(days=1)),
        "Last 7 days": (today - timedelta(days=6), today),
        "Last 30 days": (today - timedelta(days=29), today),
        "Last 10 weeks": (today - timedelta(weeks=10), today),
    }
    if preset in ranges:
        return ranges[preset]
    if preset == "Custom range" and custom and len(custom) == 2:
        return custom[0], custom[1]
    return None, None


# ── Cached data access (keyed on data version → auto-invalidates on writes) ────
@st.cache_data(show_spinner=False)
def load_bundle(version, s, e, campaign, status, ad):
    return (db.get_metrics(s, e, campaign), db.get_campaigns(), db.get_leads(s, e, campaign, status, ad))


@st.cache_data(show_spinner=False)
def load_stats(version, s, e, campaign):
    return analytics.build_stats_payload(db.get_metrics(s, e, campaign), db.get_campaigns(),
                                         db.get_leads(s, e, campaign))


def fmt_money(x):
    return f"${x:,.0f}" if x is not None else "—"


def wow_delta(pct, invert=False):
    """Format a week-over-week delta arrow; invert=True means 'down is good' (e.g. CPL)."""
    if pct is None:
        return None
    arrow = "▲" if pct > 0 else "▼" if pct < 0 else "■"
    return f"{arrow} {abs(pct):.0f}% WoW"


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
# Lean navigation (kept simple on purpose). The page code for Audience, Creative
# Studio, Forecast, Health Score, Executive Brief, and Notifications still exists
# below — to bring any back, just add its label to this list.
NAV = ["🏠 Dashboard", "📣 Campaigns", "👥 Leads",
       "🧠 AI Analysis", "💡 Recommendations", "💬 AI Assistant", "⚙️ Settings"]

with st.sidebar:
    st.markdown(
        f'<div style="font-family:Sora;font-weight:800;font-size:20px;line-height:1.1;'
        f'background:{theme.HERO_GRADIENT};-webkit-background-clip:text;background-clip:text;'
        f'-webkit-text-fill-color:transparent;">📈 Instagram AI</div>'
        f'<div style="color:#e7d6ff;font-weight:600;margin-bottom:2px;">Ad Manager</div>'
        f'<div style="color:#c9b3e6;font-size:12px;">{config.APP_TAGLINE}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    page = st.radio("Navigate", NAV, label_visibility="collapsed")

    st.markdown("---")
    st.markdown("#### 🔎 Filters")
    preset = st.selectbox("Date range", PRESETS, index=3)
    custom = None
    if preset == "Custom range":
        lo, hi = db.date_bounds()
        ds = date.fromisoformat(lo) if lo else date.today() - timedelta(days=30)
        de = date.fromisoformat(hi) if hi else date.today()
        custom = st.date_input("Pick dates", (ds, de))

    camp_map = db.campaign_name_map()
    camp_pick = st.selectbox("Campaign", ["All"] + list(camp_map.keys()),
                             format_func=lambda c: "All campaigns" if c == "All" else camp_map.get(c, c))
    status_pick = st.selectbox("Lead status", ["All"] + db.LEAD_STATUSES)
    ad_pick = st.selectbox("Advertisement", ["All"] + db.ad_names())

    st.markdown("---")
    meta_ok, gem_ok = meta_api.is_configured(), agent.is_configured()
    st.markdown(f"**Meta API** {'🟢' if meta_ok else '⚪'}  ·  **Gemini** {'🟢' if gem_ok else '⚪'}")

    ls = db.last_sync()
    if ls and ls.get("finished_at"):
        st.caption(f"Last sync: {ls['finished_at'][:16].replace('T',' ')} · {ls['status']}")
    else:
        st.caption("Last sync: never")

    # ── Sync Now ──────────────────────────────────────────────────────────────
    can_sync = meta_ok or db.has_data()
    if st.button("🔄 Sync Now", type="primary", disabled=not can_sync, width="stretch"):
        prog = st.progress(0.0, "Starting…")
        res = sync_service.run_sync(
            source="manual",
            run_ai=gem_ok,
            skip_fetch=not meta_ok,   # refresh insights on existing/sample data when Meta isn't connected
            on_progress=lambda m, p: prog.progress(min(p, 1.0), m),
        )
        prog.empty()
        st.session_state["sync_result"] = res
        st.rerun()
    if not can_sync:
        st.caption("Connect Meta or load sample data to sync.")

# Surface the sync result once after rerun.
if "sync_result" in st.session_state:
    r = st.session_state.pop("sync_result")
    if r.get("ok"):
        st.toast(f"Sync {r['status']} — {r['counts']['leads']} leads · "
                 f"health {r['health']['score']}/100 · {r['notifications']} alerts", icon="✅")
    else:
        st.toast(f"Sync failed: {r.get('error','error')}", icon="⚠️")

# ── Load data (cached) ────────────────────────────────────────────────────────
version = db.get_version()
start, end = resolve_range(preset, custom)
s_iso = start.isoformat() if start else None
e_iso = end.isoformat() if end else None
metrics, campaigns, leads = load_bundle(version, s_iso, e_iso, camp_pick, status_pick, ad_pick)
has_data = db.has_data()

if not has_data and page != "⚙️ Settings":
    ui.hero("📈 Instagram AI Ad Manager", config.APP_TAGLINE, "Get started")
    st.info("No campaign data yet. Open **⚙️ Settings** to **Sync from Meta** or **Load sample data** "
            "to explore the full experience.")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    kpis = analytics.dashboard_kpis(metrics, leads, campaigns)
    health = analytics.marketing_health(metrics, campaigns, leads)
    wow = analytics.week_over_week(metrics)["delta_pct"]
    ui.hero("Marketing Command Center",
            "Live spend, leads, and campaign health for the selected range.",
            f"Health {health['score']}/100 · {health['label']}")

    best = kpis["best_campaign"]["name"] if kpis["best_campaign"] else "—"
    worst = kpis["worst_campaign"]["name"] if kpis["worst_campaign"] else "—"
    ui.kpis([
        theme.kpi_card("Total Spend", fmt_money(kpis["total_spend"]), "in range", "💸", wow_delta(wow.get("spend"))),
        theme.kpi_card("Total Leads", f"{kpis['total_leads']:,}", "CRM records", "🎯", wow_delta(wow.get("leads"))),
        theme.kpi_card("Avg Cost / Lead", f"${kpis['avg_cpl']:,.2f}", "spend ÷ leads", "🧮", wow_delta(wow.get("cpl"))),
        theme.kpi_card("Qualified", f"{kpis['qualified_leads']:,}", "quality leads", "✅"),
        theme.kpi_card("Avg CTR", f"{kpis['avg_ctr']:.2f}%", "click-through", "👆", wow_delta(wow.get("ctr"))),
        theme.kpi_card("Active Campaigns", f"{kpis['active_campaigns']}", "running now", "📣"),
        theme.kpi_card("Best Campaign", best[:20], f"CPL ${kpis['best_campaign']['cpl']:.2f}" if kpis["best_campaign"] else "", "🏆"),
        theme.kpi_card("Needs Attention", worst[:20], f"CPL ${kpis['worst_campaign']['cpl']:.2f}" if kpis["worst_campaign"] else "", "⚠️"),
    ])

    ts = pd.DataFrame(analytics.time_series(metrics))
    lead_days = pd.DataFrame(analytics.leads_by_day(leads))

    c1, c2 = st.columns(2)
    with c1:
        ui.section("Spend over time", "Daily ad spend", "💸"); ui.area(ts, "date", "spend", theme.PURPLE)
    with c2:
        ui.section("Leads over time", "Daily lead volume", "🎯"); ui.bars(lead_days, "date", "leads", theme.PINK)

    c3, c4 = st.columns(2)
    with c3:
        ui.section("Cost per lead", "Lower is better", "🧮"); ui.line(ts, "date", "cpl", theme.ORANGE)
    with c4:
        ui.section("Click-through rate", "Creative appeal", "👆"); ui.line(ts, "date", "ctr", theme.MAGENTA)

    c5, c6 = st.columns(2)
    with c5:
        ui.section("Lead quality mix", "By team-assigned status", "🥧")
        qvr = analytics.qualified_vs_rejected(leads)
        ui.donut(list(qvr.keys()), list(qvr.values()))
    with c6:
        ui.section("Campaign comparison", "Cost per lead by campaign", "📊")
        comp = pd.DataFrame(analytics.campaign_comparison(metrics, campaigns, leads))
        ui.hbar_gradient(comp[comp["leads"] > 0], "cpl", "name") if not comp.empty else st.caption("No data.")

    pl = analytics.placement_breakdown(metrics)
    if pl:
        ui.section("Placement performance", "Reels vs Feed vs Stories", "📱")
        st.dataframe(pd.DataFrame(pl).rename(columns={
            "placement": "Placement", "spend": "Spend", "impressions": "Impressions",
            "clicks": "Clicks", "leads": "Leads", "ctr": "CTR %", "cpl": "CPL $"}),
            width="stretch", hide_index=True,
            column_config={"Spend": st.column_config.NumberColumn(format="$%.0f"),
                           "CPL $": st.column_config.NumberColumn(format="$%.2f"),
                           "CTR %": st.column_config.NumberColumn(format="%.2f%%")})

# ══════════════════════════════════════════════════════════════════════════════
# CAMPAIGNS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📣 Campaigns":
    ui.hero("Campaigns", "Every campaign with its latest performance metrics.")
    table = analytics.campaign_table(metrics, campaigns, leads)
    if not table:
        st.caption("No campaigns in range.")
    else:
        df = pd.DataFrame(table)[["name", "status", "budget", "spend", "reach", "impressions",
                                  "clicks", "ctr", "cpc", "cpl", "leads", "qualified_leads", "conversion_rate"]]
        df.columns = ["Campaign", "Status", "Budget $", "Spend $", "Reach", "Impressions",
                      "Clicks", "CTR %", "CPC $", "CPL $", "Leads", "Qualified", "Conv %"]
        st.dataframe(df, width="stretch", hide_index=True, column_config={
            "Budget $": st.column_config.NumberColumn(format="$%.0f"),
            "Spend $": st.column_config.NumberColumn(format="$%.0f"),
            "CPC $": st.column_config.NumberColumn(format="$%.2f"),
            "CPL $": st.column_config.NumberColumn(format="$%.2f"),
            "CTR %": st.column_config.NumberColumn(format="%.2f%%"),
            "Conv %": st.column_config.NumberColumn(format="%.2f%%")})

# ══════════════════════════════════════════════════════════════════════════════
# LEADS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👥 Leads":
    ui.hero("Leads", "Update each lead's status — the AI learns from your feedback.")
    if not leads:
        st.caption("No leads match the current filters.")
    else:
        q = analytics.qualified_vs_rejected(leads)
        qn = sum(v for k, v in q.items() if k in db.QUALIFIED_STATUSES)
        rn = sum(v for k, v in q.items() if k in db.REJECTED_STATUSES)
        ui.kpis([
            theme.kpi_card("Leads shown", f"{len(leads):,}", "in range", "👥"),
            theme.kpi_card("Qualified", f"{qn:,}", "great fit", "✅"),
            theme.kpi_card("Rejected", f"{rn:,}", "not a fit", "🚫"),
            theme.kpi_card("Qualified rate", f"{analytics.safe_div(qn, len(leads))*100:.0f}%", "of shown", "📈"),
        ])
        name_map = db.campaign_name_map()
        rows = [{"id": ld["id"], "Name": ld["name"], "Email": ld["email"], "Phone": ld["phone"],
                 "Campaign": name_map.get(ld["campaign_id"], ld["campaign_id"]), "Ad": ld["ad_name"],
                 "Received": (ld["received_at"] or "")[:16].replace("T", " "),
                 "Audience": ld["audience"], "Age": ld["age_range"], "Status": ld["status"]} for ld in leads]
        df = pd.DataFrame(rows)
        edited = st.data_editor(df, width="stretch", hide_index=True, key="lead_editor",
            column_config={"id": None,
                "Status": st.column_config.SelectboxColumn("Status", options=db.LEAD_STATUSES, required=True)},
            disabled=["Name", "Email", "Phone", "Campaign", "Ad", "Received", "Audience", "Age"])
        orig = {r["id"]: r["Status"] for r in rows}
        changed = sum(1 for _, r in edited.iterrows() if orig.get(r["id"]) != r["Status"]
                      and (db.update_lead_status(r["id"], r["Status"]) or True))
        if changed:
            st.success(f"Updated {changed} lead status(es).")

# ══════════════════════════════════════════════════════════════════════════════
# AUDIENCE INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🎯 Audience":
    ui.hero("Audience Insights", "Which audiences, ages, and ads produce your best candidates.")
    ins = analytics.audience_insights(leads)
    if ins["best_audience"]:
        ui.kpis([
            theme.kpi_card("Best audience", ins["best_audience"][:20], "highest qualified rate", "🏅"),
            theme.kpi_card("Weakest audience", (ins["worst_audience"] or "—")[:20], "lowest qualified rate", "🧹"),
        ])
    c1, c2 = st.columns(2)
    with c1:
        ui.section("Qualified rate by audience", "Min 3 leads", "🎯")
        aud = pd.DataFrame(analytics.lead_quality(leads)["by_audience"])
        ui.hbar_gradient(aud.rename(columns={"group": "audience"}), "qualified_rate", "audience", reverse=True) \
            if not aud.empty else st.caption("No data.")
    with c2:
        ui.section("Qualified rate by age", "Age bands", "🎂")
        age = pd.DataFrame(analytics.lead_quality(leads)["by_age_range"])
        ui.hbar_gradient(age.rename(columns={"group": "age"}), "qualified_rate", "age", reverse=True) \
            if not age.empty else st.caption("No data.")

    ui.section("Best ads for lead quality", "By qualified rate", "🖼️")
    ad = pd.DataFrame(analytics.lead_quality(leads)["by_ad"])
    if not ad.empty:
        st.dataframe(ad.rename(columns={"group": "Ad", "total": "Leads", "qualified": "Qualified",
                                        "rejected": "Rejected", "qualified_rate": "Qualified %"}),
                     width="stretch", hide_index=True,
                     column_config={"Qualified %": st.column_config.NumberColumn(format="%.0f%%")})

    st.markdown("---")
    ui.section("AI targeting recommendations", "Where to shift budget", "🧠")
    if not gem_ok:
        st.warning("Add your **GEMINI_API_KEY** to generate targeting recommendations.")
    elif st.button("✨ Generate targeting plan", type="primary"):
        with st.spinner("Analyzing audiences with Gemini 2.5 Pro…"):
            try:
                st.session_state["aud_rec"] = agent.audience_recommendations(ins)
            except agent.AgentError as e:
                st.error(str(e))
    rec = st.session_state.get("aud_rec")
    if rec:
        cc1, cc2 = st.columns(2)
        cc1.success("**Scale up**\n\n" + "\n".join(f"- {x}" for x in rec.get("scale_up", [])) or "—")
        cc2.error("**Scale down**\n\n" + "\n".join(f"- {x}" for x in rec.get("scale_down", [])) or "—")
        if rec.get("test_ideas"):
            st.info("**Worth testing**\n\n" + "\n".join(f"- {x}" for x in rec["test_ideas"]))
        if rec.get("summary"):
            st.caption("💡 " + rec["summary"])

# ══════════════════════════════════════════════════════════════════════════════
# CREATIVE STUDIO
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🎨 Creative Studio":
    ui.hero("Creative Studio", "AI-generated ad concepts tuned to your best-performing data.")
    if not gem_ok:
        st.warning("Add your **GEMINI_API_KEY** to generate creative ideas.")
    else:
        n = st.slider("How many concepts?", 2, 6, 4)
        if st.button("🎨 Generate creative concepts", type="primary"):
            with st.spinner("Brainstorming with Gemini 2.5 Pro…"):
                try:
                    stats = load_stats(version, s_iso, e_iso, camp_pick)
                    st.session_state["creatives"] = agent.creative_suggestions(stats, n)
                except agent.AgentError as e:
                    st.error(str(e))
        creatives = st.session_state.get("creatives", [])
        for i, c in enumerate(creatives, 1):
            st.markdown(
                f'<div class="glass"><div class="sec"><div class="ic">🎬</div>'
                f'<div><div class="t">Concept {i}: {c.get("angle","")}</div>'
                f'<div class="d">{c.get("format","")}</div></div></div>'
                f'<p><b>Hook:</b> {c.get("hook","")}</p>'
                f'<p><b>Caption:</b> {c.get("caption","")}</p>'
                f'<p><b>CTA:</b> {c.get("cta","")}</p>'
                f'<p style="color:#6b7280;"><b>Why it works:</b> {c.get("why","")}</p></div>',
                unsafe_allow_html=True)
        if not creatives:
            st.caption("Generate concepts to see ideas tailored to your campaigns.")

# ══════════════════════════════════════════════════════════════════════════════
# AI ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🧠 AI Analysis":
    ui.hero("AI Performance Analysis", "Gemini reads the numbers and explains them in plain English.")
    if not gem_ok:
        st.warning("Add your **GEMINI_API_KEY** to run AI analysis.")
    elif st.button("🔁 Run analysis", type="primary"):
        with st.spinner("Analyzing campaigns with Gemini 2.5 Pro…"):
            try:
                stats = load_stats(version, s_iso, e_iso, camp_pick)
                res = agent.analyze_performance(stats)
                db.save_analysis("performance", res)
                st.session_state["last_perf"] = res
                st.rerun()
            except agent.AgentError as e:
                st.error(str(e))

    latest = st.session_state.get("last_perf") or (db.latest_analysis("performance") or {}).get("payload")
    if latest:
        if latest.get("headline"):
            st.markdown(f'<div class="glass"><div style="font-size:16px;font-weight:600;color:#2b0a3d;">'
                        f'💡 {latest["headline"]}</div></div>', unsafe_allow_html=True)

        working = (latest.get("best_performing", []) + latest.get("improving", []))[:5]
        fixing = (latest.get("worst_performing", []) + latest.get("declining", [])
                  + latest.get("anomalies", []))[:5]
        todo = (latest.get("lead_quality_opportunities", []) + latest.get("cost_opportunities", []))[:5]

        c1, c2 = st.columns(2)
        with c1:
            ui.section("What's working", "", "✅")
            for x in working:
                st.markdown(f"- {x}")
            if not working:
                st.caption("Nothing notable yet.")
        with c2:
            ui.section("What needs fixing", "", "⚠️")
            for x in fixing:
                st.markdown(f"- {x}")
            if not fixing:
                st.caption("Nothing urgent.")

        ui.section("What to do next", "", "🎯")
        for x in todo:
            st.markdown(f"- {x}")
        if not todo:
            st.caption("No actions right now.")

        if latest.get("observations"):
            with st.expander("More detail"):
                for x in latest["observations"]:
                    st.markdown(f"- {x}")
    else:
        st.caption("Run an analysis to see insights.")

# ══════════════════════════════════════════════════════════════════════════════
# RECOMMENDATIONS (continuous learning)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💡 Recommendations":
    ui.hero("Daily Recommendations", "Actions with confidence, expected impact, and outcome tracking.")
    c1, c2 = st.columns(2)
    gen = c1.button("✨ Generate recommendations", type="primary", disabled=not gem_ok)
    learn_click = c2.button("🧪 Learn from lead feedback", disabled=not gem_ok)
    if not gem_ok:
        st.warning("Add your **GEMINI_API_KEY** to generate recommendations.")

    if gen and gem_ok:
        with st.spinner("Thinking with Gemini 2.5 Pro…"):
            try:
                stats = load_stats(version, s_iso, e_iso, camp_pick)
                recs = agent.daily_recommendations(stats, db.get_recommendations(limit=20))
                for r in recs:
                    db.add_recommendation(r.get("type", "Action"), r.get("target", ""), r.get("rationale", ""),
                                          confidence=r.get("confidence", 0),
                                          expected_impact=r.get("expected_impact", ""),
                                          priority=r.get("priority", "medium"))
                st.success(f"Added {len(recs)} recommendations."); st.rerun()
            except agent.AgentError as e:
                st.error(str(e))

    if learn_click and gem_ok:
        with st.spinner("Studying lead quality…"):
            try:
                learning = agent.learn_from_leads(analytics.lead_quality(leads))
                db.save_analysis("lead_learning", learning)
                st.session_state["last_learn"] = learning
            except agent.AgentError as e:
                st.error(str(e))

    learn = st.session_state.get("last_learn") or (db.latest_analysis("lead_learning") or {}).get("payload")
    if learn:
        with st.expander("🧠 What the AI learned from your lead feedback", expanded=True):
            st.markdown("**Insights**")
            for i in learn.get("insights", []):
                st.markdown(f"- {i}")
            st.markdown("**Recommendations from feedback**")
            for i in learn.get("recommendations", []):
                st.markdown(f"- {i}")

    ui.section("Recommendation history", "Track what worked", "📋")
    recs = db.get_recommendations()
    if not recs:
        st.caption("No recommendations yet.")
    for r in recs:
        pri = (r.get("priority") or "medium").lower()
        pills = theme.confidence_pill(r.get("confidence")) + " " + theme.impact_pill(r.get("expected_impact") or "")
        st.markdown(
            f'<div class="rec-card"><span class="rt">{r["type"]}</span> — <b>{r["target"]}</b>'
            f'<div style="margin:6px 0;">{r["rationale"]}</div>{pills}'
            f'<div class="rec-meta">{r["date"]} · '
            f'priority <span class="pri-{pri}">{pri}</span> · status <b>{r["status"]}</b> · outcome <b>{r["outcome"]}</b></div></div>',
            unsafe_allow_html=True)
        cols = st.columns(5)
        if cols[0].button("Implemented", key=f"impl_{r['id']}"):
            db.update_recommendation(r["id"], status="implemented"); st.rerun()
        if cols[1].button("Dismiss", key=f"dis_{r['id']}"):
            db.update_recommendation(r["id"], status="dismissed"); st.rerun()
        if cols[2].button("✅ Improved", key=f"imp_{r['id']}"):
            db.update_recommendation(r["id"], outcome="improved"); st.rerun()
        if cols[3].button("❌ Worse", key=f"wor_{r['id']}"):
            db.update_recommendation(r["id"], outcome="worse"); st.rerun()
        if cols[4].button("➖ Neutral", key=f"neu_{r['id']}"):
            db.update_recommendation(r["id"], outcome="neutral"); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# FORECAST
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔮 Forecast":
    ui.hero("7-Day Forecast", "Where spend, leads, and cost per lead are heading.")
    fc = analytics.forecast(metrics)
    summ = fc.get("summary", {})
    if not summ:
        st.info("Not enough history to forecast yet — sync more days of data.")
    else:
        ui.kpis([
            theme.kpi_card("Projected spend (7d)", fmt_money(summ["next7_spend"]), summ["spend_direction"], "💸"),
            theme.kpi_card("Projected leads (7d)", f"{summ['next7_leads']:.0f}", summ["leads_direction"], "🎯"),
            theme.kpi_card("Projected CPL", f"${summ['projected_cpl']:.2f}", "next 7 days", "🧮"),
        ])
        ui.section("Spend outlook", "Actual + forecast with 80% band", "💸")
        ui.forecast_chart([{"date": h["date"], "value": h["spend"]} for h in fc["history"]], fc["spend"], "value")
        c1, c2 = st.columns(2)
        with c1:
            ui.section("Leads outlook", "", "🎯")
            ui.forecast_chart([{"date": h["date"], "value": h["leads"]} for h in fc["history"]], fc["leads"], "value")
        with c2:
            ui.section("Cost-per-lead outlook", "", "🧮")
            ui.forecast_chart([{"date": h["date"], "value": h["cpl"]} for h in fc["history"]], fc["cpl"], "value")

        if gem_ok and st.button("🧠 Explain this forecast", type="primary"):
            with st.spinner("Interpreting the forecast…"):
                try:
                    st.session_state["fc_note"] = agent.forecast_narrative(summ)
                except agent.AgentError as e:
                    st.error(str(e))
        if st.session_state.get("fc_note"):
            st.markdown(f'<div class="glass">🔮 {st.session_state["fc_note"]}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HEALTH SCORE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "❤️ Health Score":
    ui.hero("Marketing Health Score", "A single composite of cost, quality, momentum, and consistency.")
    health = analytics.marketing_health(metrics, campaigns, leads)
    c1, c2 = st.columns([1, 1.4])
    with c1:
        ui.gauge(health["score"])
        st.markdown(f'<div style="text-align:center;"><span class="grade">{health["grade"]}</span>'
                    f'<div style="font-weight:700;color:#4b2a86;">{health["label"]}</div></div>',
                    unsafe_allow_html=True)
    with c2:
        ui.section("Score breakdown", "Weighted components", "🧩")
        ui.health_components(health["components"])
        st.caption(f"💪 Strongest: **{health['strongest']}**  ·  🎯 Focus: **{health['weakest']}**")
    ui.section("What each component means", "", "📘")
    for comp in health["components"]:
        st.markdown(f"- **{comp['name']}** ({comp['score']}/100, weight {int(comp['weight']*100)}%): {comp['detail']}")

# ══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE BRIEF
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🗞️ Executive Brief":
    ui.hero("Executive Brief", "Leadership-ready summary: health, wins, risks, and priorities.")
    if not gem_ok:
        st.warning("Add your **GEMINI_API_KEY** to generate the executive brief.")
    elif st.button("🗞️ Generate brief", type="primary"):
        with st.spinner("Composing with Gemini 2.5 Pro…"):
            try:
                stats = load_stats(version, s_iso, e_iso, camp_pick)
                summary = agent.executive_summary(stats)
                db.save_analysis("exec_summary", summary)
                st.session_state["last_exec"] = summary
                st.rerun()
            except agent.AgentError as e:
                st.error(str(e))

    summ = st.session_state.get("last_exec") or (db.latest_analysis("exec_summary") or {}).get("payload")
    if summ:
        if summ.get("headline"):
            st.markdown(f'<div class="glass"><h3 style="margin:0;">{summ["headline"]}</h3>'
                        f'<div style="color:#6b7280;margin-top:6px;">{summ.get("health_read","")}</div></div>',
                        unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.success("**Wins**\n\n" + "\n".join(f"- {w}" for w in summ.get("wins", [])) or "—")
        c2.error("**Risks**\n\n" + "\n".join(f"- {r}" for r in summ.get("risks", [])) or "—")
        if summ.get("forecast_note"):
            st.info("🔮 " + summ["forecast_note"])
        ui.section("This week's priorities", "", "✅")
        for i, p in enumerate(summ.get("priorities", []), 1):
            st.markdown(f"**{i}.** {p}")
    else:
        st.caption("Generate a brief to see your executive summary.")

# ══════════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔔 Notifications":
    ui.hero("Notification Center", "Automatic alerts from every sync — nothing important slips by.")
    c1, c2, c3 = st.columns([1, 1, 3])
    only_unread = c1.toggle("Unread only", value=False)
    if c2.button("Mark all read"):
        db.mark_all_read(); st.rerun()
    items = db.get_notifications(unread_only=only_unread, limit=100)
    ui.notifications(items)
    if items:
        st.markdown("---")
        cols = st.columns(6)
        for i, n in enumerate(items[:12]):
            if not n["read"] and cols[i % 6].button("✓ read", key=f"nr_{n['id']}"):
                db.mark_notification_read(n["id"]); st.rerun()
        if st.button("🗑️ Clear all notifications"):
            db.clear_notifications(); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# AI ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💬 AI Assistant":
    ui.hero("AI Assistant", "Ask anything about your campaigns and lead quality.")
    if not gem_ok:
        st.warning("Add your **GEMINI_API_KEY** to chat with the assistant.")
    else:
        st.session_state.setdefault("chat", [])
        examples = ["Which campaign is best?", "Why did CPL increase?",
                    "Which audience is highest quality?", "Which ads should we pause?",
                    "Compare this week vs last."]
        cols = st.columns(len(examples))
        clicked = next((ex for i, ex in enumerate(examples) if cols[i].button(ex, key=f"ex_{i}")), None)
        for turn in st.session_state["chat"]:
            with st.chat_message(turn["role"]):
                st.markdown(turn["content"])
        prompt = st.chat_input("Ask about your campaigns…") or clicked
        if prompt:
            st.session_state["chat"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking…"):
                    try:
                        stats = load_stats(version, s_iso, e_iso, camp_pick)
                        answer = agent.chat(prompt, stats, st.session_state["chat"])
                    except agent.AgentError as e:
                        answer = f"⚠️ {e}"
                    st.markdown(answer)
            st.session_state["chat"].append({"role": "assistant", "content": answer})
        if st.session_state["chat"] and st.button("Clear conversation"):
            st.session_state["chat"] = []; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    ui.hero("Settings", "Connections, sync, scheduling, and data.")

    ui.section("Connections", "", "🔌")
    c1, c2 = st.columns(2)
    c1.metric("Meta Marketing API", "Connected" if meta_api.is_configured() else "Not connected")
    c2.metric("Gemini 2.5 Pro", "Ready" if agent.is_configured() else "No key")

    ui.section("API keys", "Kept in memory for this session only", "🔑")
    with st.form("api_keys"):
        g_key = st.text_input("Gemini API key", value=st.session_state.get("k_gemini", ""), type="password",
                              help="aistudio.google.com/apikey", placeholder="AIza…")
        m_tok = st.text_input("Meta access token", value=st.session_state.get("k_meta_token", ""), type="password",
                              help="Long-lived token with ads_read + leads_retrieval", placeholder="EAAG…")
        m_acct = st.text_input("Meta ad account ID", value=st.session_state.get("k_meta_acct", ""),
                               help="Include the act_ prefix", placeholder="act_1234567890")
        if st.form_submit_button("💾 Save keys for this session", type="primary"):
            st.session_state["k_gemini"], st.session_state["k_meta_token"], st.session_state["k_meta_acct"] = g_key, m_tok, m_acct
            _apply_session_keys()
            st.success("Keys saved. Connection status updated."); st.rerun()
    with st.expander("What each key is for & how to get it"):
        st.markdown(
            "- **Gemini API key** — powers every AI feature. Free at "
            "[aistudio.google.com/apikey](https://aistudio.google.com/apikey).\n"
            "- **Meta access token** — pulls live campaigns/insights/leads. Create a Business app at "
            "[developers.facebook.com](https://developers.facebook.com/), add the Marketing API, and grant "
            "`ads_read` + `leads_retrieval`. Use a long-lived / System User token.\n"
            "- **Meta ad account ID** — e.g. `act_1234567890` (the `act_` prefix is added automatically).")

    ui.section("Sync", "Pull fresh data + run AI", "🔄")
    days = st.slider("History window (days)", 14, 90, config.DEFAULT_SYNC_DAYS, step=7)
    cA, cB = st.columns(2)
    if cA.button("🔄 Sync from Meta + AI", type="primary", disabled=not meta_api.is_configured()):
        prog = st.progress(0.0, "Starting…")
        res = sync_service.run_sync(days=days, source="manual", run_ai=agent.is_configured(),
                                    on_progress=lambda m, p: prog.progress(min(p, 1.0), m))
        prog.empty()
        (st.success if res["ok"] else st.error)(" ".join(res.get("messages", [res.get("error", "")])))
        st.rerun()
    if cB.button("🧠 Refresh AI on current data", disabled=not agent.is_configured() or not db.has_data()):
        prog = st.progress(0.0, "Starting…")
        res = sync_service.run_sync(source="manual", run_ai=True, skip_fetch=True, force_recs=True,
                                    on_progress=lambda m, p: prog.progress(min(p, 1.0), m))
        prog.empty()
        st.success("AI insights refreshed."); st.rerun()

    ls = db.last_sync()
    if ls:
        st.caption(f"Last sync: {(ls.get('finished_at') or '')[:19].replace('T',' ')} · "
                   f"{ls['status']} · {ls['leads']} leads · AI: {'yes' if ls['ran_ai'] else 'no'}")

    with st.expander("⏱️ Automate daily syncs (GitHub Actions / cron)"):
        st.markdown(
            "Streamlit can't run background jobs, so a **separate script** does the periodic sync:\n\n"
            "```bash\npython sync.py --days 70          # live Meta sync + AI\n"
            "python sync.py --sample --no-ai    # demo data, no AI\n```\n\n"
            "- **GitHub Actions (preferred):** the included workflow "
            "`.github/workflows/instagram-ad-manager-sync.yml` runs daily, then commits the refreshed "
            "database back so the deployed app shows fresh data. Add `GEMINI_API_KEY`, `META_ACCESS_TOKEN`, "
            "and `META_AD_ACCOUNT_ID` as repo **Secrets**.\n"
            "- **cron / Task Scheduler:** schedule the same `python sync.py` command.\n"
            "- Point `ADMANAGER_DB_PATH` at a shared/persistent location so the job and app use one database.")

    if db.recent_syncs():
        st.dataframe(pd.DataFrame(db.recent_syncs())[
            ["started_at", "status", "source", "campaigns", "metrics", "leads", "ran_ai"]],
            width="stretch", hide_index=True)

    ui.section("Sample data", "Explore the UI without connecting Meta", "🌱")
    cc1, cc2 = st.columns(2)
    if cc1.button("🌱 Load sample data"):
        counts = demo_seed.seed(config.DEFAULT_SYNC_DAYS)
        st.success(f"Loaded {counts['campaigns']} campaigns, {counts['leads']} leads."); st.rerun()
    if cc2.button("🗑️ Clear all data"):
        db.clear_all(); st.warning("All local data cleared."); st.rerun()

    st.caption("Data is stored locally in SQLite (`data/admanager.db`, override with `ADMANAGER_DB_PATH`). "
               "On Streamlit Cloud this resets on redeploy — use the scheduled sync to keep it fresh.")
