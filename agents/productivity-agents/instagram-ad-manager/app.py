"""
app.py — Instagram AI Ad Manager
Streamlit app: monitor Instagram lead-gen campaigns, analyze performance with
Gemini 2.5 Pro, generate daily recommendations, learn from lead feedback, and
chat with an AI marketing assistant. Data comes from the live Meta Marketing API
(Settings → Sync), with an optional sample dataset for exploring the UI.
"""

import os
import sys
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

from modules import agent, analytics, database as db, demo_seed, meta_api

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Instagram AI Ad Manager",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.block-container { padding-top: 2.2rem; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #2b0a3d 0%, #3d1152 45%, #4a1259 100%) !important;
}
[data-testid="stSidebar"] * { color: #f3e8ff !important; }
[data-testid="stSidebar"] .stRadio label { font-size: 14px !important; }

/* KPI cards */
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 14px; margin: 6px 0 18px; }
.kpi {
    background: linear-gradient(145deg, #ffffff, #faf5ff);
    border: 1px solid #ecdcff; border-radius: 16px; padding: 16px 18px;
    box-shadow: 0 2px 10px rgba(120, 40, 160, 0.06);
}
.kpi .label { font-size: 12px; font-weight: 600; color: #8a5cb8; text-transform: uppercase; letter-spacing: .04em; }
.kpi .value { font-size: 26px; font-weight: 800; color: #2b0a3d; margin-top: 4px; }
.kpi .sub { font-size: 12px; color: #7c7c8a; margin-top: 2px; }

/* Status badges */
.badge { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }
.b-active { background:#e6f9ec; color:#0f8a3c; }
.b-paused { background:#fff4e0; color:#b5730a; }
.b-completed { background:#eef0f5; color:#586074; }

h1, h2, h3 { color: #2b0a3d; }
.section-note { color:#6b7280; font-size: 14px; margin-top:-6px; }
div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }

/* Pills for recommendations */
.rec-card { border:1px solid #ecdcff; border-radius:14px; padding:14px 16px; margin-bottom:10px; background:#ffffff; }
.rec-type { font-weight:700; color:#7c1fa8; }
.pri-high { color:#c0392b; font-weight:700; }
.pri-medium { color:#b5730a; font-weight:700; }
.pri-low { color:#586074; font-weight:600; }
</style>
""", unsafe_allow_html=True)

db.init_db()

# ── Runtime API keys (entered on the Settings page) ───────────────────────────
# Keys typed into Settings live in session_state only (never written to disk) and
# are pushed into os.environ so the existing modules — which read st.secrets first,
# then os.environ — pick them up. For permanent setup, use `.env` / Streamlit Secrets.
_KEY_ENV = {
    "k_gemini": "GEMINI_API_KEY",
    "k_meta_token": "META_ACCESS_TOKEN",
    "k_meta_acct": "META_AD_ACCOUNT_ID",
}


def _apply_session_keys():
    for sk, env in _KEY_ENV.items():
        val = st.session_state.get(sk)
        if val:
            os.environ[env] = val.strip()


_apply_session_keys()

# ── Filter helpers (§8) ───────────────────────────────────────────────────────
PRESETS = ["Today", "Yesterday", "Last 7 days", "Last 30 days", "Last 10 weeks", "All time", "Custom range"]


def resolve_range(preset: str, custom):
    today = date.today()
    if preset == "Today":
        return today, today
    if preset == "Yesterday":
        y = today - timedelta(days=1)
        return y, y
    if preset == "Last 7 days":
        return today - timedelta(days=6), today
    if preset == "Last 30 days":
        return today - timedelta(days=29), today
    if preset == "Last 10 weeks":
        return today - timedelta(weeks=10), today
    if preset == "Custom range" and custom and len(custom) == 2:
        return custom[0], custom[1]
    return None, None  # All time


def load_data(start, end, campaign_id, status, ad_name):
    s = start.isoformat() if start else None
    e = end.isoformat() if end else None
    metrics = db.get_metrics(s, e, campaign_id)
    campaigns = db.get_campaigns()
    leads = db.get_leads(s, e, campaign_id, status, ad_name)
    return metrics, campaigns, leads


def fmt_money(x):
    return f"${x:,.0f}" if x is not None else "—"


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 Instagram AI\n#### Ad Manager")
    st.caption("Smarter campaigns for Bay Area job seekers")

    page = st.radio(
        "Navigate",
        ["🏠 Dashboard", "📣 Campaigns", "👥 Leads", "🧠 AI Analysis",
         "💡 Recommendations", "🗞️ Daily Brief", "💬 AI Assistant", "⚙️ Settings"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("#### 🔎 Filters")
    preset = st.selectbox("Date range", PRESETS, index=3)
    custom = None
    if preset == "Custom range":
        lo, hi = db.date_bounds()
        default_start = date.fromisoformat(lo) if lo else date.today() - timedelta(days=30)
        default_end = date.fromisoformat(hi) if hi else date.today()
        custom = st.date_input("Pick dates", (default_start, default_end))

    camp_map = db.campaign_name_map()
    camp_choices = ["All"] + list(camp_map.keys())
    camp_pick = st.selectbox(
        "Campaign", camp_choices,
        format_func=lambda cid: "All campaigns" if cid == "All" else camp_map.get(cid, cid),
    )
    status_pick = st.selectbox("Lead status", ["All"] + db.LEAD_STATUSES)
    ad_pick = st.selectbox("Advertisement", ["All"] + db.ad_names())

    st.markdown("---")
    connected = meta_api.is_configured()
    st.markdown(f"**Meta API:** {'🟢 Connected' if connected else '⚪ Not connected'}")
    st.markdown(f"**Gemini:** {'🟢 Ready' if agent.is_configured() else '⚪ No key'}")

start, end = resolve_range(preset, custom)
metrics, campaigns, leads = load_data(start, end, camp_pick, status_pick, ad_pick)
has_data = db.has_data()

# Empty-state guard ------------------------------------------------------------
if not has_data and page not in ("⚙️ Settings",):
    st.title("📈 Instagram AI Ad Manager")
    st.info(
        "No campaign data yet. Open **⚙️ Settings** to **Sync from Meta** "
        "(with your access token) or **Load sample data** to explore the UI."
    )
    st.stop()


# ── KPI card renderer ─────────────────────────────────────────────────────────
def kpi_cards(kpis: dict):
    best = kpis["best_campaign"]["name"] if kpis["best_campaign"] else "—"
    worst = kpis["worst_campaign"]["name"] if kpis["worst_campaign"] else "—"
    cards = [
        ("Total Spend", fmt_money(kpis["total_spend"]), "in range"),
        ("Today's Spend", fmt_money(kpis["today_spend"]), "so far"),
        ("Total Leads", f"{kpis['total_leads']:,}", "CRM records"),
        ("Qualified", f"{kpis['qualified_leads']:,}", "quality leads"),
        ("Rejected", f"{kpis['rejected_leads']:,}", "not a fit"),
        ("Active Campaigns", f"{kpis['active_campaigns']}", "running now"),
        ("Avg Cost / Lead", f"${kpis['avg_cpl']:,.2f}", "spend ÷ leads"),
        ("Avg CTR", f"{kpis['avg_ctr']:.2f}%", "click-through"),
        ("Best Campaign", best[:22], f"CPL ${kpis['best_campaign']['cpl']:.2f}" if kpis["best_campaign"] else ""),
        ("Worst Campaign", worst[:22], f"CPL ${kpis['worst_campaign']['cpl']:.2f}" if kpis["worst_campaign"] else ""),
    ]
    html = '<div class="kpi-grid">'
    for label, value, sub in cards:
        html += f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div><div class="sub">{sub}</div></div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def status_badge(s: str) -> str:
    cls = {"Active": "b-active", "Paused": "b-paused", "Completed": "b-completed"}.get(s, "b-completed")
    return f'<span class="badge {cls}">{s}</span>'


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    st.title("🏠 Dashboard")
    st.markdown('<p class="section-note">Live view of spend, leads, and campaign health for the selected range.</p>', unsafe_allow_html=True)

    kpis = analytics.dashboard_kpis(metrics, leads, campaigns)
    kpi_cards(kpis)

    ts = pd.DataFrame(analytics.time_series(metrics))
    lead_days = pd.DataFrame(analytics.leads_by_day(leads))

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Spend over time")
        if not ts.empty:
            st.plotly_chart(px.area(ts, x="date", y="spend", color_discrete_sequence=["#a855f7"]),
                            width='stretch')
        else:
            st.caption("No data in range.")
    with c2:
        st.subheader("Leads over time")
        if not lead_days.empty:
            st.plotly_chart(px.bar(lead_days, x="date", y="leads", color_discrete_sequence=["#7c3aed"]),
                            width='stretch')
        else:
            st.caption("No leads in range.")

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Cost per lead trend")
        if not ts.empty:
            st.plotly_chart(px.line(ts, x="date", y="cpl", markers=True, color_discrete_sequence=["#db2777"]),
                            width='stretch')
    with c4:
        st.subheader("CTR trend")
        if not ts.empty:
            st.plotly_chart(px.line(ts, x="date", y="ctr", markers=True, color_discrete_sequence=["#2563eb"]),
                            width='stretch')

    c5, c6 = st.columns(2)
    with c5:
        st.subheader("Qualified vs Rejected")
        qvr = analytics.qualified_vs_rejected(leads)
        if qvr:
            dfq = pd.DataFrame({"status": list(qvr.keys()), "count": list(qvr.values())})
            st.plotly_chart(px.pie(dfq, names="status", values="count", hole=0.45),
                            width='stretch')
    with c6:
        st.subheader("Campaign comparison (CPL)")
        comp = pd.DataFrame(analytics.campaign_comparison(metrics, campaigns, leads))
        comp = comp[comp["leads"] > 0]
        if not comp.empty:
            st.plotly_chart(
                px.bar(comp.sort_values("cpl"), x="cpl", y="name", orientation="h",
                       color="cpl", color_continuous_scale="RdYlGn_r"),
                width='stretch',
            )

    # Placement insight
    pl = analytics.placement_breakdown(metrics)
    if pl:
        st.subheader("Placement performance")
        st.dataframe(
            pd.DataFrame(pl).rename(columns={"placement": "Placement", "spend": "Spend",
                                             "impressions": "Impressions", "clicks": "Clicks",
                                             "leads": "Leads", "ctr": "CTR %", "cpl": "CPL $"}),
            width='stretch', hide_index=True,
        )

# ══════════════════════════════════════════════════════════════════════════════
# CAMPAIGNS (§1)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📣 Campaigns":
    st.title("📣 Campaigns")
    st.markdown('<p class="section-note">Every campaign with its latest performance metrics.</p>', unsafe_allow_html=True)

    table = analytics.campaign_table(metrics, campaigns, leads)
    if not table:
        st.caption("No campaigns in range.")
    else:
        df = pd.DataFrame(table)
        df = df[["name", "status", "budget", "spend", "reach", "impressions", "clicks",
                 "ctr", "cpc", "cpl", "leads", "qualified_leads", "conversion_rate"]]
        df.columns = ["Campaign", "Status", "Budget $", "Spend $", "Reach", "Impressions",
                      "Clicks", "CTR %", "CPC $", "CPL $", "Leads", "Qualified", "Conv %"]
        st.dataframe(
            df, width='stretch', hide_index=True,
            column_config={
                "Budget $": st.column_config.NumberColumn(format="$%.0f"),
                "Spend $": st.column_config.NumberColumn(format="$%.0f"),
                "CPC $": st.column_config.NumberColumn(format="$%.2f"),
                "CPL $": st.column_config.NumberColumn(format="$%.2f"),
                "CTR %": st.column_config.NumberColumn(format="%.2f%%"),
                "Conv %": st.column_config.NumberColumn(format="%.2f%%"),
            },
        )

# ══════════════════════════════════════════════════════════════════════════════
# LEADS (§5)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👥 Leads":
    st.title("👥 Leads")
    st.markdown('<p class="section-note">Update each lead\'s status — the AI learns from your feedback.</p>', unsafe_allow_html=True)

    if not leads:
        st.caption("No leads match the current filters.")
    else:
        name_map = db.campaign_name_map()
        rows = []
        for ld in leads:
            rows.append({
                "id": ld["id"],
                "Name": ld["name"], "Email": ld["email"], "Phone": ld["phone"],
                "Campaign": name_map.get(ld["campaign_id"], ld["campaign_id"]),
                "Ad": ld["ad_name"],
                "Received": (ld["received_at"] or "")[:16].replace("T", " "),
                "Audience": ld["audience"], "Age": ld["age_range"],
                "Status": ld["status"],
            })
        df = pd.DataFrame(rows)
        edited = st.data_editor(
            df, width='stretch', hide_index=True, key="lead_editor",
            column_config={
                "id": None,
                "Status": st.column_config.SelectboxColumn("Status", options=db.LEAD_STATUSES, required=True),
                "Email": st.column_config.TextColumn(disabled=True),
                "Name": st.column_config.TextColumn(disabled=True),
            },
            disabled=["Name", "Email", "Phone", "Campaign", "Ad", "Received", "Audience", "Age"],
        )
        # Persist any status changes
        orig = {r["id"]: r["Status"] for r in rows}
        changed = 0
        for _, r in edited.iterrows():
            if orig.get(r["id"]) != r["Status"]:
                db.update_lead_status(r["id"], r["Status"])
                changed += 1
        if changed:
            st.success(f"Updated {changed} lead status(es).")
        st.caption(f"{len(leads)} leads shown.")

# ══════════════════════════════════════════════════════════════════════════════
# AI ANALYSIS (§2)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🧠 AI Analysis":
    st.title("🧠 AI Performance Analysis")
    st.markdown('<p class="section-note">Gemini reads the numbers and explains what they mean in plain English.</p>', unsafe_allow_html=True)

    if not agent.is_configured():
        st.warning("Add your **GEMINI_API_KEY** (Settings or `.env`) to run AI analysis.")
    else:
        if st.button("🔁 Run today's analysis", type="primary"):
            with st.spinner("Analyzing campaigns with Gemini 2.5 Pro…"):
                stats = analytics.build_stats_payload(metrics, campaigns, leads)
                try:
                    result = agent.analyze_performance(stats)
                    db.save_analysis("performance", result)
                    st.session_state["last_perf"] = result
                except agent.AgentError as e:
                    st.error(str(e))

    latest = st.session_state.get("last_perf") or (db.latest_analysis("performance") or {}).get("payload")
    if latest:
        if latest.get("headline"):
            st.info(f"**{latest['headline']}**")
        cols = st.columns(2)
        blocks = [
            ("🏆 Best performing", latest.get("best_performing", [])),
            ("⚠️ Worst performing", latest.get("worst_performing", [])),
            ("📈 Improving", latest.get("improving", [])),
            ("📉 Declining", latest.get("declining", [])),
            ("🔔 Unusual changes", latest.get("anomalies", [])),
            ("💰 Cost-saving opportunities", latest.get("cost_opportunities", [])),
            ("🎯 More qualified leads", latest.get("lead_quality_opportunities", [])),
            ("🔍 Observations", latest.get("observations", [])),
        ]
        for i, (title, items) in enumerate(blocks):
            with cols[i % 2]:
                st.subheader(title)
                if items:
                    for it in items:
                        st.markdown(f"- {it}")
                else:
                    st.caption("Nothing notable.")
    else:
        st.caption("Run an analysis to see insights.")

# ══════════════════════════════════════════════════════════════════════════════
# RECOMMENDATIONS (§3 / §4 continuous learning)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💡 Recommendations":
    st.title("💡 Daily Recommendations")
    st.markdown('<p class="section-note">Actionable moves with a reason — and tracking of whether they worked.</p>', unsafe_allow_html=True)

    left, right = st.columns([1, 1])
    with left:
        gen = st.button("✨ Generate today's recommendations", type="primary",
                        disabled=not agent.is_configured())
    with right:
        if st.button("🧪 Learn from lead feedback", disabled=not agent.is_configured()):
            with st.spinner("Studying lead quality…"):
                try:
                    lq = analytics.lead_quality(leads)
                    learning = agent.learn_from_leads(lq)
                    db.save_analysis("lead_learning", learning)
                    st.session_state["last_learn"] = learning
                except agent.AgentError as e:
                    st.error(str(e))

    if not agent.is_configured():
        st.warning("Add your **GEMINI_API_KEY** to generate recommendations.")

    if gen and agent.is_configured():
        with st.spinner("Thinking with Gemini 2.5 Pro…"):
            try:
                stats = analytics.build_stats_payload(metrics, campaigns, leads)
                recs = agent.daily_recommendations(stats, db.get_recommendations(limit=20))
                for r in recs:
                    db.add_recommendation(r.get("type", "Action"), r.get("target", ""),
                                          f"{r.get('rationale','')}  (priority: {r.get('priority','')})")
                st.success(f"Added {len(recs)} recommendations.")
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

    st.subheader("Recommendation history")
    recs = db.get_recommendations()
    if not recs:
        st.caption("No recommendations yet.")
    for r in recs:
        pri = "pri-low"
        rationale = r["rationale"] or ""
        if "priority: high" in rationale.lower():
            pri = "pri-high"
        elif "priority: medium" in rationale.lower():
            pri = "pri-medium"
        st.markdown(
            f'<div class="rec-card"><span class="rec-type">{r["type"]}</span> — '
            f'<b>{r["target"]}</b><br>{rationale}'
            f'<br><small>{r["date"]} · status: <b>{r["status"]}</b> · outcome: <b>{r["outcome"]}</b></small></div>',
            unsafe_allow_html=True,
        )
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
# DAILY BRIEF (§9 notifications)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🗞️ Daily Brief":
    st.title("🗞️ Daily Brief")
    st.markdown('<p class="section-note">Your morning summary: health, wins, concerns, and what to do next.</p>', unsafe_allow_html=True)

    if not agent.is_configured():
        st.warning("Add your **GEMINI_API_KEY** to generate the daily brief.")
    elif st.button("🗞️ Generate today's brief", type="primary"):
        with st.spinner("Composing summary…"):
            try:
                stats = analytics.build_stats_payload(metrics, campaigns, leads)
                summary = agent.daily_summary(stats)
                db.save_analysis("summary", summary)
                st.session_state["last_summary"] = summary
            except agent.AgentError as e:
                st.error(str(e))

    summ = st.session_state.get("last_summary") or (db.latest_analysis("summary") or {}).get("payload")
    if summ:
        st.markdown(f"### Overall health\n{summ.get('health','—')}")
        c1, c2 = st.columns(2)
        c1.success(f"**Biggest improvement**\n\n{summ.get('biggest_improvement','—')}")
        c2.error(f"**Biggest concern**\n\n{summ.get('biggest_concern','—')}")
        st.markdown("### Recommended actions")
        for a in summ.get("recommended_actions", []):
            st.markdown(f"- {a}")
        st.markdown("### New opportunities")
        for o in summ.get("opportunities", []):
            st.markdown(f"- {o}")
    else:
        st.caption("Generate a brief to see your summary.")

# ══════════════════════════════════════════════════════════════════════════════
# AI ASSISTANT (§10)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💬 AI Assistant":
    st.title("💬 AI Assistant")
    st.markdown('<p class="section-note">Ask anything about your campaigns and lead quality.</p>', unsafe_allow_html=True)

    if not agent.is_configured():
        st.warning("Add your **GEMINI_API_KEY** to chat with the assistant.")
    else:
        st.session_state.setdefault("chat", [])
        examples = ["Which campaign is performing best?", "Why has the cost per lead increased?",
                    "Which audience produces the highest-quality candidates?",
                    "Which ads should we pause?", "Compare this week with last week."]
        cols = st.columns(len(examples))
        clicked = None
        for i, ex in enumerate(examples):
            if cols[i].button(ex, key=f"ex_{i}"):
                clicked = ex

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
                        stats = analytics.build_stats_payload(metrics, campaigns, leads)
                        answer = agent.chat(prompt, stats, st.session_state["chat"])
                    except agent.AgentError as e:
                        answer = f"⚠️ {e}"
                    st.markdown(answer)
            st.session_state["chat"].append({"role": "assistant", "content": answer})

        if st.session_state["chat"] and st.button("Clear conversation"):
            st.session_state["chat"] = []
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    st.title("⚙️ Settings")

    st.subheader("Connections")
    c1, c2 = st.columns(2)
    c1.metric("Meta Marketing API", "Connected" if meta_api.is_configured() else "Not connected")
    c2.metric("Gemini 2.5 Pro", "Ready" if agent.is_configured() else "No key")

    # ── API key entry (this session) ─────────────────────────────────────────
    st.subheader("🔑 API keys")
    st.caption(
        "Enter your keys here to use them for this session. They're kept in memory "
        "only (not saved to disk). For a permanent setup, add them to a `.env` file "
        "or Streamlit **Secrets** instead — see **Tutorial.md**."
    )
    with st.form("api_keys"):
        g_key = st.text_input(
            "Gemini API key", value=st.session_state.get("k_gemini", ""), type="password",
            help="Google AI Studio → aistudio.google.com/apikey. Needed for all AI features.",
            placeholder="AIza…",
        )
        m_tok = st.text_input(
            "Meta access token", value=st.session_state.get("k_meta_token", ""), type="password",
            help="Long-lived token with ads_read + leads_retrieval. See Tutorial → section 11.",
            placeholder="EAAG… (long-lived)",
        )
        m_acct = st.text_input(
            "Meta ad account ID", value=st.session_state.get("k_meta_acct", ""),
            help="Found in Meta Ads Manager. Include the act_ prefix.",
            placeholder="act_1234567890",
        )
        saved = st.form_submit_button("💾 Save keys for this session", type="primary")
    if saved:
        st.session_state["k_gemini"] = g_key
        st.session_state["k_meta_token"] = m_tok
        st.session_state["k_meta_acct"] = m_acct
        _apply_session_keys()
        st.success("Keys saved for this session. Connection status updated.")
        st.rerun()

    with st.expander("What each key is for & how to get it"):
        st.markdown(
            "- **Gemini API key** — powers AI Analysis, Recommendations, Daily Brief, and the "
            "Assistant. Free to start at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).\n"
            "- **Meta access token** — lets the app pull your live campaigns, insights, and leads. "
            "Create a **Business** app at [developers.facebook.com](https://developers.facebook.com/), "
            "add the **Marketing API**, and grant `ads_read` + `leads_retrieval`. Use a **long-lived** "
            "or **System User** token so it doesn't expire.\n"
            "- **Meta ad account ID** — the account to read from, e.g. `act_1234567890` "
            "(Ads Manager → account dropdown). The `act_` prefix is added automatically if you omit it.\n\n"
            "You only need the **Gemini key** for the AI features and the **sample data**. "
            "The two Meta values are required only for **live sync**."
        )

    if not meta_api.is_configured():
        st.info(
            "Meta isn't connected yet — enter your token + ad account ID above (or use `.env` / "
            "Secrets), then **Sync**. No account? Use **Load sample data** below to explore the UI."
        )

    st.subheader("Sync from Meta")
    days = st.slider("History window (days)", 14, 90, 70, step=7)
    if st.button("🔄 Sync live data from Meta", type="primary", disabled=not meta_api.is_configured()):
        with st.spinner("Pulling campaigns, insights, and leads from Meta…"):
            try:
                payload = meta_api.pull_all(days=days)
                nc = db.upsert_campaigns(payload["campaigns"])
                nm = db.upsert_metrics(payload["metrics"])
                nl = db.upsert_leads(payload["leads"])
                st.success(f"Synced {nc} campaigns, {nm} metric rows, {nl} leads.")
            except meta_api.MetaAPIError as e:
                st.error(f"Meta sync failed: {e}")

    st.markdown("---")
    st.subheader("Sample data")
    st.caption("Load a realistic demo dataset to explore the UI before connecting Meta.")
    cc1, cc2 = st.columns(2)
    if cc1.button("🌱 Load sample data"):
        counts = demo_seed.seed(70)
        st.success(f"Loaded {counts['campaigns']} campaigns, {counts['leads']} leads. Reloading…")
        st.rerun()
    if cc2.button("🗑️ Clear all data"):
        db.clear_all()
        st.warning("All local data cleared.")
        st.rerun()

    st.markdown("---")
    st.caption("Data is stored locally in `data/admanager.db` (SQLite). "
               "On Streamlit Cloud this resets on redeploy.")
