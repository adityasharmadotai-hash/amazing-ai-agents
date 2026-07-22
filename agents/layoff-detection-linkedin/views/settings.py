"""Settings view — every API key in one place, with step-by-step instructions
for generating each one, a source picker, and a live status check.

Exposed as `render()` and mounted by streamlit_app.py via st.navigation using a
callable page. Page config / CSS / secrets bootstrap are done by the router.
"""
from __future__ import annotations

import streamlit as st

import st_common
from agent import config

_SOURCE_LABELS = {
    "serpapi": "🟢  SerpAPI — free tier, fastest to set up (recommended to start)",
    "apify": "🔵  Apify — paid, full LinkedIn post scraping (more volume)",
    "gemini": "🟣  Gemini web search — no extra key, uses your Gemini key",
}
_GROUP_ICONS = {
    "Required": "🔑",
    "LinkedIn source": "🔎",
    "Search & targeting": "🎯",
    "Optional integrations": "✨",
    "Tuning": "🎛️",
}


def _field_help(f: dict) -> str:
    """Compose a field's tooltip: its short help plus the numbered how-to steps.

    Folding the steps into the `?` tooltip (instead of a per-field expander)
    keeps the Settings page short while retaining the full instructions.
    """
    txt = f.get("help", "")
    steps = f.get("steps") or []
    if steps:
        txt += "\n\n**How to get / use:**\n" + "\n".join(
            f"{i}. {s}" for i, s in enumerate(steps, 1))
    return txt


def render():
    st_common.hero(
        "Settings &amp; API keys",
        "Configure every service the agent uses. Each field explains exactly how "
        "to generate the key. Nothing is sent anywhere except the service it "
        "belongs to.",
        badges=["🔐 Keys stay private"],
    )

    # ── Step 1: choose the LinkedIn data source ────────────────────────────
    st.subheader("1 · Choose your LinkedIn data source")
    current_source = st_common.current_source()
    _options = ["serpapi", "apify", "gemini"]
    source = st.radio(
        "How should the app find LinkedIn posts?",
        options=_options,
        index=_options.index(current_source) if current_source in _options else 0,
        format_func=lambda s: _SOURCE_LABELS[s],
        key="source_radio",
    )
    if source != current_source:
        st_common.apply_overrides({"LINKEDIN_SOURCE": source})
        st.rerun()

    if source == "serpapi":
        st.info("**SerpAPI mode:** you only need a SerpAPI key below — Apify is "
                "not used at all. Great for getting started for free.", icon="🟢")
    elif source == "apify":
        st.info("**Apify mode:** you need an Apify token below. Apify scrapes full "
                "LinkedIn posts (higher volume, paid per use).", icon="🔵")
    else:
        st.info("**Gemini web search mode:** no extra key needed — this reuses your "
                "Gemini API key to search Google for LinkedIn posts. Coverage "
                "depends on what Google surfaces, and each query spends Gemini "
                "tokens (shown under Gemini spend on the dashboard).", icon="🟣")

    # ── Live status ────────────────────────────────────────────────────────
    missing = config.missing_required()
    if missing:
        st.warning("Missing required keys: **" + ", ".join(missing) + "**",
                   icon="⚠️")
    else:
        st.success("✅ All required keys are set — head to the dashboard and click "
                   "**Scan New Data**.")

    with st.expander("ℹ️ How configuration works"):
        st.markdown(
            "- **On Streamlit Cloud**, open your app → **⋮ → Settings → Secrets** "
            "and paste keys in TOML form (see the template at the bottom of this "
            "page). They load automatically every time the app starts.\n"
            "- **Locally**, copy `.env.example` to `.env` and fill it in, *or* "
            "paste keys below to set them just for this session.\n"
            "- Session values entered below win until the app restarts."
        )

    st.divider()

    # ── Step 2: the configuration form ─────────────────────────────────────
    st.subheader("2 · Keys & options")
    st.caption("Grouped below to keep things short — **Required** and your "
               "**LinkedIn source** are open; expand the others only to change "
               "them. Hover the **?** on any field for step-by-step help.")

    # Only show the key for the chosen backend; hide the other one entirely.
    visible = [f for f in st_common.CONFIG_KEYS
               if f["key"] != "LINKEDIN_SOURCE"
               and f.get("backend", source) == source]

    groups: dict[str, list[dict]] = {}
    for field in visible:
        groups.setdefault(field["group"], []).append(field)

    # Groups that start expanded (what a first-time user must fill in). The rest
    # collapse so the page fits on a screen.
    _open = {"Required", "LinkedIn source"}

    with st.form("settings"):
        overrides: dict[str, str] = {}
        for group, fields in groups.items():
            with st.expander(f"{_GROUP_ICONS.get(group, '•')}  {group}",
                             expanded=(group in _open)):
                for f in fields:
                    key = f["key"]
                    current = st_common.current_value(key)
                    label = f["label"] + ("  ·  *required*" if f.get("required") else "")
                    help_txt = _field_help(f)
                    if f.get("multiline"):
                        # Pre-fill with the *active* values (defaults included) so
                        # the box is never confusingly blank; clearing resets it.
                        prefill = current
                        if not current and key == "LINKEDIN_QUERIES":
                            prefill = "\n".join(config.LINKEDIN_QUERIES)
                        elif not current and key == "TARGET_TITLES":
                            prefill = ", ".join(config.TARGET_TITLES)
                        overrides[key] = st.text_area(
                            label, value=prefill, help=help_txt,
                            placeholder="Clear this box to reset to the built-in defaults.",
                            height=130, key=f"in_{key}",
                        )
                    elif f.get("secret"):
                        overrides[key] = st.text_input(
                            label, value="", type="password",
                            placeholder="•••• already set" if current else "",
                            help=help_txt, key=f"in_{key}",
                        )
                    else:
                        # Non-secret: prefill with the current value, or the built-in
                        # default (so e.g. the Apify actor shows its default value).
                        overrides[key] = st.text_input(
                            label, value=current or f.get("default", ""),
                            help=help_txt, key=f"in_{key}",
                        )
        saved = st.form_submit_button("💾 Save for this session", type="primary",
                                      use_container_width=True)

    if saved:
        to_apply: dict[str, str] = {"LINKEDIN_SOURCE": source}
        for f in visible:
            key = f["key"]
            val = overrides.get(key, "")
            if f.get("secret") and not val:
                continue  # blank secret = "leave as-is"
            to_apply[key] = val
        st_common.apply_overrides(to_apply)
        st.success("Saved for this session. Re-checking required keys…")
        st.rerun()

    # ── Secrets template for Streamlit Cloud ───────────────────────────────
    with st.expander("3 · Streamlit Cloud secrets template"):
        st.caption("Copy this into your app's **Settings → Secrets** box and fill "
                   "in the values. It already reflects your chosen source; delete "
                   "any optional lines you don't use.")
        defaults = {
            "LINKEDIN_SOURCE": source,
            "APIFY_ACTOR": "apimaestro/linkedin-posts-search-scraper-no-cookies",
            "GEMINI_MODEL": "gemini-2.5-flash",
            "LINKEDIN_RECENCY_DAYS": "2",
            "LINKEDIN_RESULTS_PER_Q": "20",
            "LAYOFF_US_ONLY": "true",
            "REQUIRE_TARGET_TITLE": "false",
            "LOCATION_IN_SEARCH": "false",
            "LOCATION_INCLUDE_UNKNOWN": "true",
            "ENRICH_LOCATION": "true",
        }
        template_lines = []
        for f in st_common.CONFIG_KEYS:
            if f.get("backend", source) != source:
                continue
            template_lines.append(f'{f["key"]} = "{defaults.get(f["key"], "")}"')
        st.code("\n".join(template_lines), language="toml")
