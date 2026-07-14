"""Dashboard view — scan, leads table, cost, analyze, enrich, history.

Rendered by streamlit_app.py via st.navigation. Page config / CSS / secrets
bootstrap are already done by the router before this runs.
"""
from __future__ import annotations

import io
import logging

import pandas as pd
import streamlit as st

import st_common
from agent import config, enrich, store, usage
from agent.pipeline import analyze_url, run_scan


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


@st.dialog("Delete all lead data?")
def _delete_dialog():
    st.warning("This permanently deletes **all** stored leads from your Supabase "
               "table. This cannot be undone.", icon="⚠️")
    also = st.checkbox("Also clear scan history & spend totals", value=True)
    c1, c2 = st.columns(2)
    if c1.button("🗑️ Yes, delete everything", type="primary",
                 use_container_width=True):
        try:
            n = store.delete_all()
            if also:
                usage.reset()
            st.session_state["_delete_result"] = ("ok", n)
        except Exception as exc:  # noqa: BLE001
            st.session_state["_delete_result"] = ("err", str(exc))
        st.rerun()
    if c2.button("Cancel", use_container_width=True):
        st.rerun()


# ── Hero ───────────────────────────────────────────────────────────────────
src_badge = "🟢 SerpAPI" if config.LINKEDIN_SOURCE == "serpapi" else "🔵 Apify"
locs = ", ".join(config.TARGET_LOCATIONS) or "🌍 Worldwide"
st_common.hero(
    "LayoffScout AI",
    "Finds software-engineering candidates from LinkedIn &amp; news layoff posts, "
    "extracts them with AI, and stores qualified leads.",
    badges=[f"Source · {src_badge}", f"🎯 {locs}",
            f"Roles · {len(config.TARGET_TITLES)}"],
)

# Show the outcome of a delete that just happened (dialog closed via rerun).
_res = st.session_state.pop("_delete_result", None)
if _res:
    if _res[0] == "ok":
        st.toast(f"🗑️ Deleted {_res[1]} lead(s). Everything is cleared.", icon="✅")
    else:
        st.toast(f"Delete failed: {_res[1]}", icon="⚠️")

missing = config.missing_required()
if missing:
    st.warning(
        "**Setup needed:** missing " + ", ".join(f"`{m}`" for m in missing)
        + ". Open **⚙️ Settings** (left) to add your API keys — it has step-by-step "
        "instructions for generating each one.",
        icon="⚙️",
    )

# ── Action bar ─────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([1.5, 1, 1])
with c1:
    scan_clicked = st.button("⚡ Scan New Data", type="primary",
                             use_container_width=True, disabled=bool(missing))
with c2:
    st.button("↻ Refresh", use_container_width=True)
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
        st.success(
            f"✅ Scan complete — **{summary.get('new_leads', 0)} new lead(s)** "
            f"({summary.get('relevant_us_swe', 0)} qualified of "
            f"{summary.get('candidates', 0)} examined). "
            f"This scan cost **{_money(cost.get('total'))}**."
        )
        # Funnel — shows exactly where candidates drop off (a lead must pass ALL
        # three: individual + target location + target role).
        b = summary.get("breakdown", {}) or {}
        st.markdown(
            f"**Why this number?** &nbsp; {summary.get('candidates', 0)} examined "
            f"→ **{b.get('layoff_posts', 0)}** layoff posts → "
            f"**{b.get('individuals', 0)}** individuals · "
            f"**{b.get('in_location', 0)}** in {locs} · "
            f"**{b.get('target_role', 0)}** in a target role → "
            f"**{summary.get('relevant_us_swe', 0)} qualified** "
            f"_(a lead must pass all three)_."
        )
        if summary.get("relevant_us_swe", 0) == 0:
            st.info(
                "0 qualified usually means the **US-only** filter dropped posts "
                "whose location couldn't be confirmed (common with SerpAPI, which "
                "can't scrape profiles to resolve location). Try one of these on "
                "the **⚙️ Settings** page: clear **Target locations** (worldwide), "
                "broaden **Target roles**, or switch the source to **Apify** "
                "(resolves unknown locations).",
                icon="💡",
            )
        with st.expander("📜 Scan log"):
            st.code(logs or "(no output)", language="text")

# ── What this scan looks for (active targeting, collapsible) ───────────────
with st.expander(
    f"🔎 What this scan looks for — {len(config.LINKEDIN_QUERIES)} "
    f"keyword{'s' if len(config.LINKEDIN_QUERIES) != 1 else ''} · "
    f"{len(config.TARGET_TITLES)} role{'s' if len(config.TARGET_TITLES) != 1 else ''} · "
    f"{locs}"
):
    kw_col, role_col = st.columns(2)
    with kw_col:
        st.markdown("**🔑 Search keywords / queries**")
        for q in config.LINKEDIN_QUERIES:
            st.markdown(f"- `{q}`")
    with role_col:
        st.markdown("**🎯 Target roles**")
        st.markdown(
            " ".join(
                f"<span style='display:inline-block;background:#efedff;color:#5a4bd6;"
                f"border:1px solid #e0ddff;border-radius:999px;padding:2px 10px;"
                f"margin:0 4px 6px 0;font-size:12px;font-weight:600'>{t}</span>"
                for t in config.TARGET_TITLES
            ),
            unsafe_allow_html=True,
        )
        st.markdown(f"**🌍 Locations:** {locs}")
    st.caption("Change any of these on the ⚙️ **Settings** page → *Search & targeting*.")

# ── Spend ──────────────────────────────────────────────────────────────────
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

# ── Tabs ───────────────────────────────────────────────────────────────────
tab_leads, tab_analyze, tab_enrich, tab_history = st.tabs(
    ["🎯 Leads", "🔗 Analyze a post", "✉️ Enrich", "📊 History"]
)

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
        dl, dele = st.columns([1, 1])
        dl.download_button("⤓ Download CSV", view.to_csv(index=False).encode("utf-8"),
                           "us_software_leads.csv", "text/csv",
                           use_container_width=True)
        if dele.button("🗑️ Delete all lead data", use_container_width=True):
            _delete_dialog()
    elif not missing:
        st.info("No leads yet — click **⚡ Scan New Data** above to collect some. "
                "You can retarget what it looks for on the **Settings** page.",
                icon="👋")
        if st.button("🗑️ Delete all lead data"):
            _delete_dialog()

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
