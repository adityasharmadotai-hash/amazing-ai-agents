"""Dashboard view — scan, leads table, cost, analyze, enrich, history.

Exposed as `render()` and mounted by streamlit_app.py via st.navigation using a
callable page (no file-path resolution, which is unreliable in a subdirectory).
Page config / CSS / secrets bootstrap are done by the router before this runs.
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


def render():
    # ── Hero ───────────────────────────────────────────────────────────────
    _labels = {"serpapi": "SerpAPI", "apify": "Apify", "perplexity": "Perplexity",
               "gemini": "Gemini"}
    active = config.active_sources()
    src_badge = ("⭐ " + " + ".join(_labels.get(s, s) for s in active)
                 if config.LINKEDIN_SOURCE == "all"
                 else _labels.get(config.LINKEDIN_SOURCE, config.LINKEDIN_SOURCE))
    locs = ", ".join(config.TARGET_LOCATIONS) or "🌍 Worldwide"
    st_common.hero(
        "LayoffScout AI",
        "Finds layoff posts — companies announcing layoffs and laid-off people — "
        "from LinkedIn &amp; news, extracts them with AI, and stores the leads.",
        badges=[f"Source · {src_badge}", f"🎯 {locs}",
                f"⏱ Last {config.LINKEDIN_RECENCY_DAYS}d"],
    )

    # Outcome of a delete that just happened (dialog closed via rerun).
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
            + ". Open **⚙️ Settings** (left) to add your API keys — it has "
            "step-by-step instructions for generating each one.",
            icon="⚙️",
        )

    # ── Action bar ─────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns([1.6, 1, 1.15, 1.15])
    with c1:
        scan_clicked = st.button("⚡ Scan New Data", type="primary",
                                 use_container_width=True, disabled=bool(missing))
    with c2:
        st.button("↻ Refresh", use_container_width=True)
    with c3:
        validated_only = st.toggle("✅ In-location only", value=False,
                                   help="Show only leads that matched your target "
                                        "location filter.")
    with c4:
        otw_only = st.toggle("Open-to-work only", value=False)

    if scan_clicked:
        with st.spinner("Scraping LinkedIn, extracting with AI, resolving "
                        "locations… this can take a minute."):
            summary, logs = _capture_scan()
        if summary.get("status") == "busy":
            st.info("⏳ " + summary.get("message", "A scan is already running."))
        elif summary.get("ai_error"):
            st.error(
                "🛑 **The AI (Gemini) rejected every request — no posts could be "
                "analyzed.** This is almost always a bad **GEMINI_API_KEY** or an "
                "invalid **GEMINI_MODEL**, not 'no layoffs found'.\n\n"
                f"**Gemini said:** `{summary['ai_error'][:300]}`\n\n"
                "Fix on the **⚙️ Settings** page: paste a valid key from "
                "https://aistudio.google.com/app/apikey (or set `GEMINI_MODEL` to "
                "`gemini-2.5-flash` / `gemini-1.5-flash`), then scan again."
            )
            with st.expander("📜 Scan log"):
                st.code(logs or "(no output)", language="text")
        else:
            cost = summary.get("cost", {}) or {}
            st.success(
                f"✅ Scan complete — **{summary.get('new_leads', 0)} new lead(s) "
                f"saved** · **{summary.get('companies_discovered', 0)} companies "
                f"discovered** "
                f"(**{summary.get('qualified_in_location', 0)} in {locs}**, of "
                f"{summary.get('candidates', 0)} examined). "
                f"This scan cost **{_money(cost.get('total'))}**."
            )
            b = summary.get("breakdown", {}) or {}
            st.markdown(
                f"**Why this number?** &nbsp; {summary.get('candidates', 0)} examined "
                f"→ **{b.get('layoff_posts', 0)}** layoff posts "
                f"(**{b.get('individuals', 0)}** people · "
                f"**{b.get('companies', 0)}** company posts) → "
                f"**{summary.get('qualified_in_location', 0)} in {locs}** "
                f"_(the only gate is target location)_."
            )
            if summary.get("qualified_in_location", 0) == 0 and b:
                if b.get("layoff_posts", 0) == 0:
                    st.info("No layoff posts were found. Try a wider **recency "
                            "window** (Settings → Tuning), add more provider keys "
                            "for **All (merge)**, or broaden your **queries**.",
                            icon="💡")
                else:
                    st.info(f"Found **{b.get('layoff_posts', 0)}** layoff posts but "
                            f"**0 in {locs}**. Widen or clear **Target locations**, "
                            "keep **Keep unknown-location candidates** ON, or enable "
                            "**Resolve unknown locations** (Apify) in Settings → "
                            "Tuning.", icon="💡")
            with st.expander("📜 Scan log"):
                st.code(logs or "(no output)", language="text")

    # ── What this scan looks for (collapsible) ─────────────────────────────
    loc_mode = "in search+filter" if config.LOCATION_IN_SEARCH else "filter only"
    providers = " + ".join(config.active_sources())
    with st.expander(
        f"🔎 What this scan looks for — {providers} · "
        f"{len(config.LINKEDIN_QUERIES)} "
        f"quer{'ies' if len(config.LINKEDIN_QUERIES) != 1 else 'y'} · "
        f"last {config.LINKEDIN_RECENCY_DAYS}d · {locs} ({loc_mode})"
    ):
        kw_col, meta_col = st.columns(2)
        with kw_col:
            st.markdown("**🔑 Search keywords / queries**")
            for q in config.LINKEDIN_QUERIES:
                st.markdown(f"- `{q}`")
        with meta_col:
            st.markdown(f"**🔌 Providers merged:** {providers}")
            st.markdown(f"**🌍 Locations:** {locs} _({loc_mode})_")
            st.markdown(f"**⏱ Recency:** last {config.LINKEDIN_RECENCY_DAYS} days")
            st.markdown("**🎯 Kept:** every layoff post (company or individual) in "
                        "the target location — no role filter.")
        st.caption("Change any of these on the ⚙️ **Settings** page.")

    # ── Spend ──────────────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("##### 💰 Spend")
        try:
            u = usage.totals()
            cost = u.get("cost", {}) or {}
            counts = u.get("counts", {}) or {}
            last = u.get("last", {}) or {}
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("Total spend", _money(cost.get("total")),
                      f"{u.get('scans', 0)} scans")
            m2.metric("Apify (scraping)", _money(cost.get("apify")),
                      f"{counts.get('apify_posts', 0)} posts")
            m3.metric("Gemini (AI)", _money(cost.get("gemini")),
                      f"{counts.get('gemini_calls', 0)} calls")
            m4.metric("SerpAPI", _money(cost.get("serpapi")),
                      f"{counts.get('serpapi_searches', 0)} searches")
            m5.metric("Perplexity", _money(cost.get("perplexity")),
                      f"{counts.get('perplexity_searches', 0)} searches")
            last_cost = (last.get("cost") or {}).get("total") if last else None
            m6.metric("Last scan",
                      _money(last_cost) if last_cost is not None else "—",
                      f"+{last.get('new_leads', 0)} leads" if last else "no scans yet")
        except Exception as exc:  # usage log is local + optional
            st.caption(f"Usage stats unavailable: {exc}")

    # ── Tabs ───────────────────────────────────────────────────────────────
    tab_companies, tab_leads, tab_analyze, tab_enrich, tab_history = st.tabs(
        ["🏢 Companies", "🎯 Leads", "🔗 Analyze a post", "✉️ Enrich", "📊 History"]
    )

    with tab_companies:
        st.caption("Companies discovered from layoff posts, ranked by confidence. "
                   "Confidence rises when multiple independent signals — several "
                   "employees, a recruiter, a founder, a news article — name the "
                   "same company.")
        min_conf = st.slider("Minimum confidence", 0.0, 1.0, 0.0, 0.05,
                             key="company_min_conf")
        try:
            comps = store.list_companies(limit=500,
                                         min_confidence=min_conf or None)
        except Exception as exc:
            comps = []
            st.info("No company data yet. Run the **`supabase/companies.sql`** "
                    "migration in Supabase, then click **Scan New Data**.\n\n"
                    f"_Details: {exc}_")
        if comps:
            st.caption(f"**{len(comps)}** compan{'y' if len(comps) == 1 else 'ies'} "
                       "discovered.")
            cdf = pd.DataFrame(comps)
            show = [c for c in [
                "company_name", "confidence", "total_posts", "employee_posts",
                "recruiter_posts", "founder_posts", "announcement_posts",
                "news_posts", "locations",
            ] if c in cdf.columns]
            cview = cdf[show].rename(columns={
                "company_name": "Company", "confidence": "Confidence",
                "total_posts": "Posts", "employee_posts": "Employees",
                "recruiter_posts": "Recruiters", "founder_posts": "Founders",
                "announcement_posts": "Announcements", "news_posts": "News",
                "locations": "Locations",
            })
            # ProgressColumn shows the value via `format`, so scale 0–1 to 0–100.
            if "Confidence" in cview.columns:
                cview["Confidence"] = (cview["Confidence"].fillna(0) * 100).round()
            st.dataframe(
                cview, use_container_width=True, hide_index=True,
                column_config={"Confidence": st.column_config.ProgressColumn(
                    "Confidence", min_value=0, max_value=100, format="%.0f%%")},
            )
            st.download_button("⤓ Download companies CSV",
                               cview.to_csv(index=False).encode("utf-8"),
                               "discovered_companies.csv", "text/csv",
                               use_container_width=True)
        elif not missing:
            st.info("No companies discovered yet — click **⚡ Scan New Data** "
                    "above (and make sure you've run `supabase/companies.sql`).",
                    icon="🏢")

    with tab_leads:
        try:
            rows = store.list_records(
                limit=500,
                open_to_work=True if otw_only else None,
                qualified=True if validated_only else None,
            )
        except Exception as exc:
            rows = []
            st.info(
                "No database connection yet. Add your **Supabase** URL + service "
                "key on the Settings page to store and view leads.\n\n"
                f"_Details: {exc}_"
            )

        if rows:
            n_valid = sum(1 for r in rows if r.get("is_qualified"))
            st.caption(
                f"**{len(rows)}** lead(s) saved · **{n_valid}** in-location"
                + (" · in-location only" if validated_only else "")
                + (" · open-to-work only" if otw_only else "")
            )
            df = pd.DataFrame(rows)
            # Rank most-confident first so the strongest layoff posts surface.
            if "confidence" in df.columns:
                df = df.sort_values("confidence", ascending=False, na_position="last")
            show_cols = [c for c in [
                "person_name", "company", "role_hint", "location", "event_date",
                "is_us", "open_to_work", "confidence", "summary", "source_url",
            ] if c in df.columns]
            view = df[show_cols].rename(columns={
                "person_name": "Person", "company": "Company", "role_hint": "Role",
                "location": "Location", "event_date": "Layoff date", "is_us": "US",
                "open_to_work": "Open?", "confidence": "Conf.",
                "summary": "Summary", "source_url": "Post",
            })
            st.dataframe(
                view, use_container_width=True, hide_index=True,
                column_config={"Post": st.column_config.LinkColumn(
                    "Post", display_text="open ↗")},
            )
            dl, dele = st.columns([1, 1])
            dl.download_button("⤓ Download CSV",
                               view.to_csv(index=False).encode("utf-8"),
                               "us_software_leads.csv", "text/csv",
                               use_container_width=True)
            if dele.button("🗑️ Delete all lead data", use_container_width=True):
                _delete_dialog()
        elif not missing:
            st.info("No leads yet — click **⚡ Scan New Data** above to collect "
                    "some. You can retarget what it looks for on the **Settings** "
                    "page.", icon="👋")
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
                st.success(f"✅ {rec.get('person_name') or rec.get('company') or 'Lead'} — "
                           f"{rec.get('role_hint') or '—'} at "
                           f"{rec.get('company') or '—'} "
                           f"({rec.get('location') or '—'})")
                st.json(rec)
            else:
                st.info("ℹ️ Not a layoff post, or the URL was unreachable — "
                        "nothing stored.")

    with tab_enrich:
        st.caption("Turn a LinkedIn profile into a verified work email (requires a "
                   "Wiza API key).")
        with st.form("enrich"):
            profile = st.text_input("LinkedIn profile / post URL",
                                    placeholder="https://www.linkedin.com/in/…")
            enrich_go = st.form_submit_button("✉ Enrich via Wiza", type="primary")
        if enrich_go and profile.strip():
            with st.spinner("Looking up contact via Wiza… this can take up to a "
                            "minute (Wiza processes the reveal asynchronously)."):
                res = enrich.enrich_profile(profile.strip())
            status = res.get("status")
            if status == "ok" and res.get("email"):
                st.success(f"✅ {res.get('full_name') or 'Contact'} — {res.get('email')}")
                st.json(res)
            elif status == "ok":
                st.warning("Wiza finished the lookup but **found no email** for this "
                           "profile. (Not every profile has a discoverable email.)")
                st.json(res)
            elif status == "pending":
                st.info("⏳ " + (res.get("message") or "Still processing — try "
                                 "again in a few seconds."))
            else:
                st.info(f"ℹ️ {res.get('message') or status}")

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
                st.info("No scans yet — your scan history will appear here.",
                        icon="📊")
        except Exception:
            st.info("No scans yet — your scan history will appear here.", icon="📊")
