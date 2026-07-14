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
}
_GROUP_ICONS = {
    "Required": "🔑",
    "LinkedIn source": "🔎",
    "Search & targeting": "🎯",
    "Optional integrations": "✨",
    "Tuning": "🎛️",
}


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
    source = st.radio(
        "How should the app find LinkedIn posts?",
        options=["serpapi", "apify"],
        index=0 if current_source == "serpapi" else 1,
        format_func=lambda s: _SOURCE_LABELS[s],
        key="source_radio",
    )
    if source != current_source:
        st_common.apply_overrides({"LINKEDIN_SOURCE": source})
        st.rerun()

    if source == "serpapi":
        st.info("**SerpAPI mode:** you only need a SerpAPI key below — Apify is "
                "not used at all. Great for getting started for free.", icon="🟢")
    else:
        st.info("**Apify mode:** you need an Apify token below. Apify scrapes full "
                "LinkedIn posts (higher volume, paid per use).", icon="🔵")

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

    # Only show the key for the chosen backend; hide the other one entirely.
    visible = [f for f in st_common.CONFIG_KEYS
               if f["key"] != "LINKEDIN_SOURCE"
               and f.get("backend", source) == source]

    groups: dict[str, list[dict]] = {}
    for field in visible:
        groups.setdefault(field["group"], []).append(field)

    with st.form("settings"):
        overrides: dict[str, str] = {}
        for group, fields in groups.items():
            st.markdown(f"#### {_GROUP_ICONS.get(group, '•')} {group}")
            for f in fields:
                key = f["key"]
                current = st_common.current_value(key)
                label = f["label"] + ("  ·  *required*" if f.get("required") else "")
                if f.get("multiline"):
                    # Pre-fill with the *active* values (defaults included) so the
                    # box is never confusingly blank. Clearing resets to defaults.
                    prefill = current
                    if not current and key == "LINKEDIN_QUERIES":
                        prefill = "\n".join(config.LINKEDIN_QUERIES)
                    elif not current and key == "TARGET_TITLES":
                        prefill = ", ".join(config.TARGET_TITLES)
                    overrides[key] = st.text_area(
                        label, value=prefill, help=f["help"],
                        placeholder="Clear this box to reset to the built-in defaults.",
                        height=160, key=f"in_{key}",
                    )
                else:
                    overrides[key] = st.text_input(
                        label,
                        value="" if f.get("secret") else current,
                        type="password" if f.get("secret") else "default",
                        placeholder="•••• already set" if (f.get("secret") and current)
                        else "",
                        help=f["help"], key=f"in_{key}",
                    )
                with st.expander(f"How to get / use: {f['label']}"):
                    for i, step in enumerate(f["steps"], 1):
                        st.markdown(f"{i}. {step}")
            st.divider()
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
    st.subheader("3 · Streamlit Cloud secrets template")
    st.caption("Copy this into your app's **Settings → Secrets** box and fill in "
               "the values. It already reflects your chosen source; delete any "
               "optional lines you don't use.")
    defaults = {
        "LINKEDIN_SOURCE": source,
        "APIFY_ACTOR": "apimaestro/linkedin-posts-search-scraper-no-cookies",
        "GEMINI_MODEL": "gemini-2.5-flash",
        "LINKEDIN_RECENCY": "w",
        "LINKEDIN_RESULTS_PER_Q": "20",
        "LAYOFF_US_ONLY": "false",
        "LOCATION_INCLUDE_UNKNOWN": "true",
        "ENRICH_LOCATION": "true",
    }
    template_lines = []
    for f in st_common.CONFIG_KEYS:
        if f.get("backend", source) != source:
            continue
        template_lines.append(f'{f["key"]} = "{defaults.get(f["key"], "")}"')
    st.code("\n".join(template_lines), language="toml")
