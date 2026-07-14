"""Shared Streamlit helpers that bridge the env-based `agent` config to
Streamlit Cloud secrets and the interactive Settings page.

The `agent` package reads all configuration from environment variables (via
`agent/config.py`, which uses python-dotenv). Streamlit Cloud does not use a
`.env` file — it injects secrets through `st.secrets`. This module:

1. `bootstrap_env()` — copies any known keys found in `st.secrets` into
   `os.environ` *before* the agent package is imported, so config picks them up.
2. `apply_overrides()` — lets the Settings page push keys typed by the user into
   `os.environ` for the current session and hot-reloads the config modules.
3. `CONFIG_KEYS` — the single source of truth describing every setting: its
   label, whether it is a secret, and step-by-step instructions to obtain it.
"""
from __future__ import annotations

import importlib
import os

import streamlit as st

# ── Every configurable key, with human-facing help ───────────────────────────
# group -> list of field dicts. Used by the Settings page to render inputs and
# by bootstrap to know which keys to copy from st.secrets.
CONFIG_KEYS: list[dict] = [
    # ---- Required core ----
    {
        "key": "GEMINI_API_KEY",
        "label": "Google Gemini API key",
        "group": "Required",
        "secret": True,
        "required": True,
        "help": "Powers all AI extraction (reading each post and pulling out the "
                "person, role, company and layoff signal).",
        "steps": [
            "Go to https://aistudio.google.com/app/apikey",
            "Sign in with a Google account.",
            "Click **Create API key** (choose or create a Google Cloud project).",
            "Copy the key that starts with `AIza…` and paste it here.",
        ],
    },
    {
        "key": "SUPABASE_URL",
        "label": "Supabase project URL",
        "group": "Required",
        "secret": False,
        "required": True,
        "help": "The database where qualified leads are stored.",
        "steps": [
            "Create a free project at https://supabase.com.",
            "Open **Project Settings → Data API**.",
            "Copy the **Project URL** (looks like `https://xxxx.supabase.co`).",
            "Then run the SQL in `supabase/layoff_posts.sql` in the Supabase SQL Editor to create the table.",
        ],
    },
    {
        "key": "SUPABASE_SERVICE_KEY",
        "label": "Supabase service_role key",
        "group": "Required",
        "secret": True,
        "required": True,
        "help": "Server-side key that lets the app read/write the leads table. "
                "Keep it secret — never expose it in client code.",
        "steps": [
            "In Supabase open **Project Settings → API keys**.",
            "Reveal and copy the **service_role** key (NOT the anon key).",
            "Paste it here / add it to Streamlit secrets.",
        ],
    },
    # ---- LinkedIn backend ----
    {
        "key": "LINKEDIN_SOURCE",
        "label": "LinkedIn backend (serpapi | apify)",
        "group": "LinkedIn source",
        "secret": False,
        "required": True,
        "help": "`serpapi` = cheap Google-indexed snippets. `apify` = full "
                "LinkedIn post scrape (paid, more volume).",
        "steps": [
            "Type `serpapi` to start cheap/free, or `apify` for full scraping.",
            "Then fill in the matching key below (SerpAPI **or** Apify).",
        ],
    },
    {
        "key": "SERPAPI_KEY",
        "label": "SerpAPI key",
        "group": "LinkedIn source",
        "backend": "serpapi",
        "secret": True,
        "required": False,
        "help": "Required when the source is SerpAPI.",
        "steps": [
            "Sign up free at https://serpapi.com.",
            "Open the **Dashboard → Your Account / API Key**.",
            "Copy the private API key and paste it here.",
        ],
    },
    {
        "key": "APIFY_TOKEN",
        "label": "Apify API token",
        "group": "LinkedIn source",
        "backend": "apify",
        "secret": True,
        "required": False,
        "help": "Required when the source is Apify.",
        "steps": [
            "Create an account at https://apify.com.",
            "Go to **Settings → Integrations → API tokens**.",
            "Copy your personal API token and paste it here.",
        ],
    },
    {
        "key": "APIFY_ACTOR",
        "label": "Apify post-search actor",
        "group": "LinkedIn source",
        "backend": "apify",
        "secret": False,
        "required": False,
        "help": "The Apify actor used to search LinkedIn posts. Default works "
                "out of the box.",
        "steps": [
            "Leave as `apimaestro/linkedin-posts-search-scraper-no-cookies` unless "
            "you have a preferred actor.",
        ],
    },
    # ---- Search & targeting (no keys — plain-English controls) ----
    {
        "key": "LINKEDIN_QUERIES",
        "label": "Search keywords / queries",
        "group": "Search & targeting",
        "secret": False,
        "required": False,
        "multiline": True,
        "help": "What to search for. One query per line. Leave blank to use the "
                "built-in layoff / open-to-work query set.",
        "steps": [
            "Write one search query per line (Google-style operators work).",
            'Example: `\"open to work\" \"data scientist\" (laid off OR layoff)`',
            "Leave blank to use the default set that targets laid-off software engineers.",
        ],
    },
    {
        "key": "TARGET_TITLES",
        "label": "Target job titles / roles to keep",
        "group": "Search & targeting",
        "secret": False,
        "required": False,
        "multiline": True,
        "help": "Only people whose role matches one of these titles are kept. "
                "Comma- or newline-separated. Leave blank for the default 36 "
                "software-engineering titles.",
        "steps": [
            "List the roles you want, comma- or newline-separated.",
            "Example: `Data Scientist, Machine Learning Engineer, Data Analyst`",
            "Leave blank to keep the default software-engineering titles.",
        ],
    },
    {
        "key": "TARGET_LOCATIONS",
        "label": "Target locations / countries",
        "group": "Search & targeting",
        "secret": False,
        "required": False,
        "help": "Only keep candidates in these countries (comma-separated). "
                "Leave blank to keep candidates worldwide. This overrides the "
                "'US only' toggle below.",
        "steps": [
            "Comma-separate the countries to keep, e.g. `United States, Canada`.",
            "Leave blank to include candidates from anywhere in the world.",
            "Country names are matched loosely (e.g. `United States` also matches `USA`).",
        ],
    },
    # ---- Optional ----
    {
        "key": "WIZA_API_KEY",
        "label": "Wiza API key (optional)",
        "group": "Optional integrations",
        "secret": True,
        "required": False,
        "help": "Enables the **Enrich** button (turns a profile into a verified "
                "work email). Without it, enrichment is disabled but everything "
                "else works.",
        "steps": [
            "Sign up at https://wiza.co.",
            "Open **Settings → API** and generate an API key.",
            "Paste it here to enable one-click contact enrichment.",
        ],
    },
    {
        "key": "NEWSAPI_KEY",
        "label": "NewsAPI key (optional)",
        "group": "Optional integrations",
        "secret": True,
        "required": False,
        "help": "Adds a news-article source on top of LinkedIn. If empty, the "
                "news source is simply skipped.",
        "steps": [
            "Register free at https://newsapi.org.",
            "Copy the API key shown on your account page.",
            "Paste it here to include news articles in scans.",
        ],
    },
    # ---- Tuning knobs (no secrets) ----
    {
        "key": "GEMINI_MODEL",
        "label": "Gemini model",
        "group": "Tuning",
        "secret": False,
        "required": False,
        "help": "`gemini-2.5-flash` is cheap & fast; `gemini-2.5-pro` is higher "
                "quality but costs more.",
        "steps": ["Leave as `gemini-2.5-flash` unless you need higher quality."],
    },
    {
        "key": "LINKEDIN_RECENCY",
        "label": "Recency window (d/w/m/y)",
        "group": "Tuning",
        "secret": False,
        "required": False,
        "help": "How far back to search: d=day, w=week, m=month, y=year.",
        "steps": ["`w` (past week) is a good default."],
    },
    {
        "key": "LINKEDIN_RESULTS_PER_Q",
        "label": "Results per query",
        "group": "Tuning",
        "secret": False,
        "required": False,
        "help": "How many results to pull per search query (higher = more cost).",
        "steps": ["`20` is a sensible default."],
    },
    {
        "key": "LAYOFF_US_ONLY",
        "label": "US only (true/false)",
        "group": "Tuning",
        "secret": False,
        "required": False,
        "help": "Restrict results to US-based candidates.",
        "steps": ["`true` keeps only US leads; `false` keeps everyone."],
    },
    {
        "key": "ENRICH_LOCATION",
        "label": "Resolve unknown locations (true/false)",
        "group": "Tuning",
        "secret": False,
        "required": False,
        "help": "When a post doesn't state a country, scrape the profile to find "
                "it (Apify only; costs one extra profile scrape).",
        "steps": ["`true` recovers more US leads; `false` saves scrapes."],
    },
]

# The env keys we will copy from st.secrets into os.environ at startup.
_ALL_KEYS = [c["key"] for c in CONFIG_KEYS]

# agent modules that cache config values and must be reloaded when keys change.
_RELOAD_ORDER = ("agent.config", "agent.llm")


def bootstrap_env() -> None:
    """Copy known keys from st.secrets into os.environ (once per process).

    Streamlit Cloud stores secrets in st.secrets; the agent package reads
    os.environ. This bridges the two. Existing env vars win, so a local `.env`
    or a Settings-page override is never clobbered.
    """
    # Accessing st.secrets (or `key in st.secrets`) raises
    # StreamlitSecretNotFoundError when no secrets.toml exists — the normal case
    # for a local run using a .env file or the Settings page. Treat that as
    # "no secrets" rather than crashing startup.
    for key in _ALL_KEYS:
        if os.environ.get(key):
            continue
        try:
            if key in st.secrets:
                os.environ[key] = str(st.secrets[key])
        except Exception:
            return  # no secrets file at all — nothing to bridge


def apply_overrides(values: dict[str, str]) -> None:
    """Set env vars from the Settings page and hot-reload the config modules.

    `from . import config` in the agent package binds the *module object*, and
    call sites read `config.ATTR` at call time — so reloading the config module
    in place propagates the new values everywhere.
    """
    for key, val in values.items():
        if val is None:
            continue
        val = str(val).strip()
        if val:
            os.environ[key] = val
        else:
            os.environ.pop(key, None)
    for mod_name in _RELOAD_ORDER:
        try:
            mod = importlib.import_module(mod_name)
            importlib.reload(mod)
        except Exception:
            pass
    # llm caches a "configured" flag against the old key — reset it so the new
    # Gemini key is picked up on the next call.
    try:
        import agent.llm as _llm
        _llm._configured = False
    except Exception:
        pass


def current_value(key: str) -> str:
    """Best-effort current value of a key (env first, then st.secrets)."""
    if os.environ.get(key):
        return os.environ[key]
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return ""


def current_source() -> str:
    """The selected LinkedIn backend — 'serpapi' (default) or 'apify'."""
    src = (current_value("LINKEDIN_SOURCE") or "serpapi").strip().lower()
    return src if src in ("serpapi", "apify") else "serpapi"


# Small, theme-aware CSS to lift the default Streamlit look a little without
# fighting the framework. Called once at the top of each page.
_CSS = """
<style>
  /* tighten the top padding so the app feels less empty */
  .block-container { padding-top: 2.2rem; max-width: 1150px; }
  /* metric cards: give them a subtle surface + border */
  div[data-testid="stMetric"] {
    background: rgba(127,127,127,0.06);
    border: 1px solid rgba(127,127,127,0.18);
    border-radius: 12px;
    padding: 12px 16px;
  }
  div[data-testid="stMetricValue"] { font-size: 1.5rem; }
  /* primary buttons: full-width feel + weight */
  button[kind="primary"] { font-weight: 600; border-radius: 10px; }
  /* dataframe corners */
  div[data-testid="stDataFrame"] { border-radius: 10px; }
  /* tab labels a touch larger */
  button[data-baseweb="tab"] { font-size: 0.95rem; }
</style>
"""


def inject_css() -> None:
    """Apply the shared visual polish. Safe to call on every page."""
    st.markdown(_CSS, unsafe_allow_html=True)
