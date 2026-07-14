"""LayoffScout AI — Streamlit dashboard.

This is the Streamlit Cloud entry point. It calls the same `agent` pipeline the
original FastAPI app used, but in-process, so the whole thing runs as a single
`streamlit run streamlit_app.py` process with no separate API server.

Pages:
  streamlit_app.py          -> this dashboard (scan, leads table, cost, enrich)
  pages/1_Settings.py       -> all API keys + how to generate each one
"""
from __future__ import annotations

import io
import logging

import pandas as pd
import streamlit as st

import st_common

# ── Must run BEFORE importing the agent package so config sees the keys ───────
st.set_page_config(page_title="LayoffScout AI", page_icon="🎯", layout="wide")
st_common.bootstrap_env()
st_common.inject_css()

from agent import config, enrich, store, usage          # noqa: E402
from agent.pipeline import analyze_url, run_scan          # noqa: E402


def _money(v) -> str:
    v = v or 0
    return f"${v:.4f}" if v < 0.01 else f"${v:.2f}"


def _capture_scan():
    """Run a scan while capturing the agent's log output into a string buffer."""
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
    root = logging.getLogger()
    prev_level = root.level
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    try:
        summary = run_scan()
    finally:
        root.removeHandler(handler)
        root.setLevel(prev_level)
    return summary, buf.getvalue()


# ── Header ────────────────────────────────────────────────────────────────
src_badge = "🟢 SerpAPI" if config.LINKEDIN_SOURCE == "serpapi" else "🔵 Apify"
locs = ", ".join(config.TARGET_LOCATIONS) or "🌍 Worldwide"

htitle, hstatus = st.columns([3, 2])
with htitle:
    st.title("🎯 LayoffScout AI")
    st.caption("Finds software-engineering candidates from LinkedIn/news layoff "
               "posts, extracts them with AI, and stores qualified leads.")
with hstatus:
    st.markdown(
        f"<div style='text-align:right;padding-top:18px;line-height:2.1'>"
        f"<span style='background:rgba(127,127,127,.12);border:1px solid "
        f"rgba(127,127,127,.25);border-radius:999px;padding:4px 12px'>"
        f"Source&nbsp;·&nbsp;<b>{src_badge}</b></span>&nbsp; "
        f"<span style='background:rgba(127,127,127,.12);border:1px solid "
        f"rgba(127,127,127,.25);border-radius:999px;padding:4px 12px'>"
        f"🎯&nbsp;<b>{locs}</b></span><br>"
        f"<a href='Settings' target='_self'>⚙️ Open Settings</a></div>",
        unsafe_allow_html=True,
    )

missing = config.missing_required()
if missing:
    st.warning(
        "⚙️ Missing required configuration: **" + ", ".join(missing) + "**. "
        "Open the **Settings** page (left sidebar) to add your API keys — it has "
        "step-by-step instructions for generating each one.",
        icon="⚠️",
    )

# ── Action bar ────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([1.5, 1, 1])
with c1:
    scan_clicked = st.button("⚡ Scan New Data", type="primary",
                             use_container_width=True, disabled=bool(missing))
with c2:
    refresh_clicked = st.button("↻ Refresh", use_container_width=True)
with c3:
    otw_only = st.toggle("Open-to-work only", value=False)

if scan_clicked:
    with st.spinner("Scraping LinkedIn, extracting with AI, resolving "
                    "locations… this can take a minute."):
        summary, logs = _capture_scan()
    if summary.get("status") == "busy":
        st.info("⏳ " + summary.get("message", "A scan is already running."))
    else:
        cost = summary.get("cost", {}) or {}
        u = summary.get("usage", {}) or {}
        st.success(
            f"✅ Scan complete — **{summary.get('new_leads', 0)} new lead(s)** "
            f"({summary.get('relevant_us_swe', 0)} qualified of "
            f"{summary.get('candidates', 0)} examined). "
            f"This scan cost **{_money(cost.get('total'))}**."
        )
        with st.expander("📜 Scan log"):
            st.code(logs or "(no output)", language="text")

# ── Cost / usage summary ───────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("##### 💰 Spend")
    try:
        u = usage.totals()
        cost = u.get("cost", {}) or {}
        counts = u.get("counts", {}) or {}
        last = u.get("last", {}) or {}
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total spend", _money(cost.get("total")), f"{u.get('scans', 0)} scans")
        m2.metric("Apify (scraping)", _money(cost.get("apify")),
                  f"{counts.get('apify_posts', 0)} posts")
        m3.metric("Gemini (AI)", _money(cost.get("gemini")),
                  f"{counts.get('gemini_calls', 0)} calls")
        m4.metric("SerpAPI", _money(cost.get("serpapi")),
                  f"{counts.get('serpapi_searches', 0)} searches")
        last_cost = (last.get("cost") or {}).get("total") if last else None
        m5.metric("Last scan", _money(last_cost) if last_cost is not None else "—",
                  f"+{last.get('new_leads', 0)} leads" if last else "no scans yet")
    except Exception as exc:  # usage log is local + optional
        st.caption(f"Usage stats unavailable: {exc}")

# ── Tabbed content ─────────────────────────────────────────────────────────
tab_leads, tab_analyze, tab_enrich, tab_history = st.tabs(
    ["🎯 Leads", "🔗 Analyze a post", "✉️ Enrich", "📊 History"]
)

# --- Leads -----------------------------------------------------------------
with tab_leads:
    try:
        rows = store.list_records(limit=200, open_to_work=True if otw_only else None)
    except Exception as exc:
        rows = []
        st.info(
            "No database connection yet. Add your **Supabase** URL + service key "
            "on the Settings page to store and view leads.\n\n"
            f"_Details: {exc}_"
        )

    if rows:
        st.caption(f"**{len(rows)}** lead(s)"
                   + (" · open-to-work only" if otw_only else ""))
        df = pd.DataFrame(rows)
        show_cols = [c for c in [
            "person_name", "role_category", "company", "location", "is_us",
            "open_to_work", "summary", "source_url",
        ] if c in df.columns]
        view = df[show_cols].rename(columns={
            "person_name": "Person", "role_category": "Role", "company": "Company",
            "location": "Location", "is_us": "US", "open_to_work": "Open?",
            "summary": "Summary", "source_url": "Post",
        })
        st.dataframe(
            view, use_container_width=True, hide_index=True,
            column_config={"Post": st.column_config.LinkColumn("Post",
                                                               display_text="open ↗")},
        )
        st.download_button("⤓ Download CSV", view.to_csv(index=False).encode("utf-8"),
                           "us_software_leads.csv", "text/csv")
    elif not missing:
        st.info("No leads yet — click **⚡ Scan New Data** above to collect some. "
                "You can retarget what it looks for on the **Settings** page.",
                icon="👋")

# --- Analyze one URL -------------------------------------------------------
with tab_analyze:
    st.caption("Test the pipeline on a single post without running a full scan.")
    with st.form("analyze"):
        url = st.text_input("LinkedIn post URL",
                            placeholder="https://www.linkedin.com/posts/…")
        submitted = st.form_submit_button("Analyze URL", disabled=bool(missing),
                                          type="primary")
    if submitted and url.strip():
        with st.spinner("Analyzing that post…"):
            rec = analyze_url(url.strip())
        if rec:
            st.success(f"✅ {rec.get('person_name') or 'Lead'} — "
                       f"{rec.get('role_category') or '—'} at "
                       f"{rec.get('company') or '—'} ({rec.get('location') or '—'})")
            st.json(rec)
        else:
            st.info("ℹ️ Not a layoff post, not a target role, or the URL was "
                    "unreachable — nothing stored.")

# --- Enrich ----------------------------------------------------------------
with tab_enrich:
    st.caption("Turn a LinkedIn profile into a verified work email (requires a "
               "Wiza API key).")
    with st.form("enrich"):
        profile = st.text_input("LinkedIn profile / post URL",
                                placeholder="https://www.linkedin.com/in/…")
        enrich_go = st.form_submit_button("✉ Enrich via Wiza", type="primary")
    if enrich_go and profile.strip():
        with st.spinner("Looking up contact via Wiza…"):
            res = enrich.enrich_profile(profile.strip())
        if res.get("status") == "ok":
            st.success(f"✅ {res.get('full_name') or ''} — "
                       f"{res.get('email') or 'no email found'}")
            st.json(res)
        else:
            st.info(f"ℹ️ {res.get('message') or res.get('status')}")

# --- History ---------------------------------------------------------------
with tab_history:
    try:
        hist = usage.recent(25)
        if hist:
            hdf = pd.DataFrame(hist).rename(columns={
                "at": "When", "examined": "Examined", "qualified": "Qualified",
                "new_leads": "New leads", "cost": "Cost ($)",
            })
            st.dataframe(hdf, use_container_width=True, hide_index=True)
        else:
            st.info("No scans yet — your scan history will appear here.", icon="📊")
    except Exception:
        st.info("No scans yet — your scan history will appear here.", icon="📊")
