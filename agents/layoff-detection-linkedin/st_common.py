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


# ── Brand design system ──────────────────────────────────────────────────────
# A cohesive, product-grade look injected as CSS. Targets Streamlit's stable
# data-testid hooks so it degrades gracefully across minor version bumps.
BRAND_PRIMARY = "#6d5efc"
BRAND_GRADIENT = "linear-gradient(135deg,#6d5efc 0%,#8b5cf6 52%,#ec4899 128%)"

_BRAND_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root { --brand:#6d5efc; --brand-2:#8b5cf6; --ink:#1e2233; --muted:#6b7280;
        --line:#e8eaf2; --card:#ffffff; --bg:#f5f6fb; }

html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stSidebar"] * , .stMarkdown, button, input, textarea, select {
  font-family:'Inter',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
}
.stApp { background:var(--bg); }
[data-testid="stHeader"] { background:transparent; }
.block-container { padding-top:1.4rem; padding-bottom:3rem; max-width:1180px; }

/* ---------- Hero ---------- */
.ls-hero {
  display:flex; justify-content:space-between; align-items:center; gap:18px;
  flex-wrap:wrap; background:""" + BRAND_GRADIENT + """; color:#fff;
  border-radius:22px; padding:26px 30px; margin:2px 0 20px;
  box-shadow:0 16px 34px rgba(109,94,252,.28);
}
.ls-hero-l { display:flex; align-items:center; gap:16px; }
.ls-logo {
  font-size:32px; width:60px; height:60px; border-radius:16px;
  background:rgba(255,255,255,.18); display:flex; align-items:center;
  justify-content:center; box-shadow:inset 0 0 0 1px rgba(255,255,255,.25);
}
.ls-title { font-size:27px; font-weight:800; letter-spacing:-.6px; line-height:1.05; }
.ls-sub { opacity:.92; font-size:13px; margin-top:4px; max-width:46ch; }
.ls-badges { display:flex; gap:10px; flex-wrap:wrap; justify-content:flex-end; }
.ls-pill {
  background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.30);
  color:#fff; padding:7px 14px; border-radius:999px; font-size:12.5px;
  font-weight:600; white-space:nowrap;
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] { background:var(--card); border-right:1px solid var(--line); }
[data-testid="stSidebarNav"] { padding-top:.4rem; }
[data-testid="stSidebarNav"] a { border-radius:10px; margin:2px 8px; }
[data-testid="stSidebarNav"] a:hover { background:#f1f0ff; }
[data-testid="stSidebarNav"] a[aria-current="page"] {
  background:#efedff; color:#5a4bd6; font-weight:700;
}
.ls-brand { display:flex; align-items:center; gap:11px; padding:6px 6px 2px; }
.ls-brand .m { font-size:22px; width:38px; height:38px; border-radius:11px;
  background:""" + BRAND_GRADIENT + """; display:flex; align-items:center;
  justify-content:center; box-shadow:0 6px 14px rgba(109,94,252,.35); }
.ls-brand .t { font-weight:800; font-size:16px; color:var(--ink); letter-spacing:-.3px; }
.ls-brand .s { font-size:11px; color:var(--muted); margin-top:-2px; }

/* ---------- Metric cards ---------- */
[data-testid="stMetric"] {
  background:var(--card); border:1px solid var(--line); border-radius:16px;
  padding:15px 18px; box-shadow:0 1px 3px rgba(16,24,40,.05);
  transition:transform .12s, box-shadow .12s;
}
[data-testid="stMetric"]:hover { transform:translateY(-2px);
  box-shadow:0 10px 22px rgba(16,24,40,.08); }
[data-testid="stMetricValue"] { font-weight:800; color:var(--ink); }
[data-testid="stMetricLabel"] p { font-weight:600; color:var(--muted); }

/* ---------- Buttons ---------- */
.stButton>button, .stDownloadButton>button, .stFormSubmitButton>button {
  border-radius:12px; font-weight:600; border:1px solid var(--line);
  transition:.15s; padding:.5rem 1rem;
}
.stButton>button:hover, .stDownloadButton>button:hover { border-color:var(--brand);
  color:var(--brand); }
button[kind="primary"], button[kind="primaryFormSubmit"] {
  background:""" + BRAND_GRADIENT + """ !important; border:none !important;
  color:#fff !important; box-shadow:0 8px 18px rgba(109,94,252,.34);
}
button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover {
  filter:brightness(1.06); transform:translateY(-1px); color:#fff !important;
}
button[kind="primary"]:disabled { filter:grayscale(.4) opacity(.7);
  box-shadow:none; transform:none; }

/* ---------- Surfaces ---------- */
[data-testid="stVerticalBlockBorderWrapper"] { border-radius:18px; }
[data-testid="stAlert"] { border-radius:14px; border:1px solid var(--line); }
[data-testid="stDataFrame"] { border-radius:12px; overflow:hidden;
  border:1px solid var(--line); }
[data-testid="stForm"] { border-radius:18px; border:1px solid var(--line);
  background:var(--card); }
.stTextInput input, .stTextArea textarea {
  border-radius:10px !important; }

/* ---------- Tabs ---------- */
[data-baseweb="tab-list"] { gap:2px; border-bottom:1px solid var(--line); }
button[data-baseweb="tab"] { font-weight:600; font-size:.95rem; }
[data-baseweb="tab-highlight"] { background:var(--brand); height:3px; border-radius:3px; }

/* ---------- Chrome ---------- */
#MainMenu, footer, [data-testid="stStatusWidget"] { visibility:hidden; }
</style>
"""


def apply_brand() -> None:
    """Inject the brand design system. Safe to call once per page."""
    st.markdown(_BRAND_CSS, unsafe_allow_html=True)


# Backwards-compatible alias.
def inject_css() -> None:
    apply_brand()


def sidebar_brand() -> None:
    """Render the branded product block at the top of the sidebar."""
    st.markdown(
        "<div class='ls-brand'><div class='m'>🎯</div>"
        "<div><div class='t'>LayoffScout&nbsp;AI</div>"
        "<div class='s'>AI recruiting agent</div></div></div>",
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, badges: list[str] | None = None) -> None:
    """Render the gradient product hero header.

    `badges` is a list of short HTML-safe strings shown as pills on the right.
    """
    pills = "".join(f"<span class='ls-pill'>{b}</span>" for b in (badges or []))
    st.markdown(
        f"<div class='ls-hero'><div class='ls-hero-l'>"
        f"<div class='ls-logo'>🎯</div><div>"
        f"<div class='ls-title'>{title}</div>"
        f"<div class='ls-sub'>{subtitle}</div></div></div>"
        f"<div class='ls-badges'>{pills}</div></div>",
        unsafe_allow_html=True,
    )
