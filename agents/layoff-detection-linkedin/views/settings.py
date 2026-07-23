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
    "all": "⭐  All (merge) — combine every provider you have a key for (max coverage)",
    "serpapi": "🟢  SerpAPI — free tier, fastest to set up",
    "apify": "🔵  Apify — paid, full LinkedIn post scraping (more volume)",
    "perplexity": "🟠  Perplexity web search — live search with citations (needs a key)",
    "gemini": "🟣  Gemini web search — no extra key, but can't find LinkedIn posts",
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
    _options = ["all", "serpapi", "apify", "perplexity", "gemini"]
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

    if source == "all":
        active = ", ".join(config.active_sources()) or "none yet"
        st.info("**All (merge) mode — recommended.** Runs every provider you have "
                "a key for (SerpAPI + Apify + Perplexity) at once and dedupes the "
                "results — the widest coverage. Add keys below for each provider "
                f"you want included. **Currently active:** {active}. Gemini is "
                "excluded (it can't find LinkedIn posts).", icon="⭐")
    elif source == "serpapi":
        st.info("**SerpAPI mode:** you only need a SerpAPI key below. Cheap Google-"
                "indexed snippets — good for getting started.", icon="🟢")
    elif source == "apify":
        st.info("**Apify mode:** you need an Apify token below. Apify scrapes full "
                "LinkedIn posts (highest volume, paid per use).", icon="🔵")
    elif source == "perplexity":
        st.info("**Perplexity web search mode:** add a Perplexity API key below. "
                "Live web search returning real LinkedIn post URLs — fresh, no "
                "scraper. Billed per search.", icon="🟠")
    else:
        st.info("**Gemini web search mode:** no extra key needed, but note Google "
                "Search can't reach individual LinkedIn posts, so this usually "
                "returns 0. Use **All** or another provider for real coverage.",
                icon="🟣")

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

    # Show a field when it isn't backend-specific, OR its backend matches the
    # chosen source, OR we're in "all" (merge) mode — then show every provider's
    # key so the user can supply all the ones they want merged.
    def _field_visible(f: dict) -> bool:
        if f["key"] == "LINKEDIN_SOURCE":
            return False
        backend = f.get("backend")
        return backend is None or source == "all" or backend == source

    visible = [f for f in st_common.CONFIG_KEYS if _field_visible(f)]

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
                        overrides[key] = st.text_area(
                            label, value=prefill, help=help_txt,
                            placeholder="Clear this box to reset to the built-in defaults.",
                            height=130, key=f"in_{key}",
                        )
                    elif f.get("choices"):
                        # Fixed-choice dropdown (e.g. recency days).
                        opts = f["choices"]
                        cur = current or f.get("default", opts[0])
                        idx = opts.index(cur) if cur in opts else 0
                        overrides[key] = st.selectbox(
                            label, options=opts, index=idx, help=help_txt,
                            key=f"in_{key}",
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
            "LINKEDIN_RECENCY_DAYS": "3",
            "LINKEDIN_RESULTS_PER_Q": "30",
            "APIFY_MAX_KEYWORD_VARIANTS": "8",
            "TARGET_LOCATIONS": "San Francisco, California",
            "LOCATION_IN_SEARCH": "false",
            "LOCATION_INCLUDE_UNKNOWN": "true",
            "ENRICH_LOCATION": "true",
        }
        template_lines = []
        for f in st_common.CONFIG_KEYS:
            backend = f.get("backend")
            if backend is not None and source != "all" and backend != source:
                continue
            template_lines.append(f'{f["key"]} = "{defaults.get(f["key"], "")}"')
        st.code("\n".join(template_lines), language="toml")
