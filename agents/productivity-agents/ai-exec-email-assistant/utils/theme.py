"""Centralized visual theme for the app.

A single source of truth for the design system: fonts, color tokens, and the
global CSS injected on every page. Keeping it here (instead of scattered
`st.markdown("<style>")` blocks) means the look stays consistent and is easy
to evolve.

Aesthetic direction: a refined dark "command center" — deep slate base,
an indigo→cyan accent, glassy cards with soft depth, and a distinctive
display typeface (Sora) paired with a clean body face (IBM Plex Sans).
"""
from __future__ import annotations

import streamlit as st

# --- Design tokens (also mirrored in .streamlit/config.toml for native widgets) ---
ACCENT = "#6D8BFF"          # primary indigo
ACCENT_2 = "#37D7C2"        # cyan/teal secondary
BG = "#0B0E16"              # app background
SURFACE = "#141926"         # card surface
SURFACE_2 = "#1B2233"       # raised surface
BORDER = "#262E40"
TEXT = "#E8ECF4"
MUTED = "#94A0B4"
GOOD = "#3FCF8E"
WARN = "#F5C451"
BAD = "#F2706B"

_GLOBAL_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

:root {{
    --accent: {ACCENT};
    --accent-2: {ACCENT_2};
    --bg: {BG};
    --surface: {SURFACE};
    --surface-2: {SURFACE_2};
    --border: {BORDER};
    --text: {TEXT};
    --muted: {MUTED};
    --good: {GOOD};
    --warn: {WARN};
    --bad: {BAD};
}}

/* ---- Base ---- */
html, body, [class*="css"], .stApp {{
    font-family: 'IBM Plex Sans', -apple-system, sans-serif;
}}
.stApp {{
    background:
        radial-gradient(1200px 600px at 12% -8%, rgba(109,139,255,0.10), transparent 55%),
        radial-gradient(1000px 500px at 100% 0%, rgba(55,215,194,0.07), transparent 50%),
        var(--bg);
}}
h1, h2, h3, h4, h5 {{
    font-family: 'Sora', sans-serif !important;
    letter-spacing: -0.02em;
    color: var(--text);
}}
h1 {{ font-weight: 800 !important; }}

/* Tighten the default top padding for a denser, app-like feel */
.block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1180px; }}

/* ---- Hero ---- */
.hero {{
    position: relative;
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 26px 30px;
    margin-bottom: 22px;
    background:
        linear-gradient(135deg, rgba(109,139,255,0.14), rgba(55,215,194,0.05) 60%),
        var(--surface);
    overflow: hidden;
}}
.hero::after {{
    content: "";
    position: absolute; inset: 0;
    background: radial-gradient(420px 180px at 88% -30%, rgba(55,215,194,0.18), transparent 70%);
    pointer-events: none;
}}
.hero h1 {{ margin: 0; font-size: 2.05rem; }}
.hero p {{ margin: 8px 0 0; color: var(--muted); font-size: 0.98rem; }}
.hero .eyebrow {{
    display: inline-block; font-family: 'Sora'; font-size: 0.72rem;
    text-transform: uppercase; letter-spacing: 0.18em; color: var(--accent-2);
    margin-bottom: 10px; font-weight: 600;
}}

/* ---- Metric cards ---- */
.metric-card {{
    background: linear-gradient(160deg, var(--surface-2) 0%, var(--surface) 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 18px 20px;
    transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
    position: relative;
}}
.metric-card:hover {{
    transform: translateY(-3px);
    border-color: rgba(109,139,255,0.55);
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
}}
.metric-card .mval {{
    font-family: 'Sora'; font-weight: 700; font-size: 2.1rem; line-height: 1;
    background: linear-gradient(120deg, var(--text), var(--accent));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.metric-card .mlabel {{
    margin-top: 8px; color: var(--muted); font-size: 0.74rem;
    text-transform: uppercase; letter-spacing: 0.09em; font-weight: 600;
}}
.metric-card .mtrend {{ font-size: 0.78rem; margin-top: 6px; }}

/* ---- Feature tiles ---- */
.feature {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 18px;
    height: 100%;
    transition: transform .18s ease, border-color .18s ease, background .18s ease;
}}
.feature:hover {{
    transform: translateY(-3px);
    border-color: rgba(55,215,194,0.5);
    background: var(--surface-2);
}}
.feature .ficon {{ font-size: 1.4rem; }}
.feature h4 {{ margin: 8px 0 6px; font-size: 1.02rem; }}
.feature p {{ margin: 0; color: var(--muted); font-size: 0.86rem; line-height: 1.45; }}

/* ---- Generic panel ---- */
.panel {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 20px 22px;
}}

/* ---- Pills / badges ---- */
.pill {{
    display: inline-block; padding: 3px 11px; border-radius: 999px;
    font-size: 0.74rem; font-weight: 600; font-family: 'Sora';
    border: 1px solid var(--border);
}}
.pill.good {{ color: var(--good); border-color: rgba(63,207,142,0.4); background: rgba(63,207,142,0.08); }}
.pill.warn {{ color: var(--warn); border-color: rgba(245,196,81,0.4); background: rgba(245,196,81,0.08); }}
.pill.bad  {{ color: var(--bad);  border-color: rgba(242,112,107,0.4); background: rgba(242,112,107,0.08); }}
.pill.accent {{ color: var(--accent-2); border-color: rgba(55,215,194,0.4); background: rgba(55,215,194,0.08); }}

/* ---- Streamlit widget polish ---- */
.stButton > button {{
    border-radius: 11px;
    border: 1px solid var(--border);
    font-family: 'Sora'; font-weight: 600;
    transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease;
}}
.stButton > button:hover {{ transform: translateY(-1px); border-color: var(--accent); }}
.stButton > button[kind="primary"] {{
    background: linear-gradient(120deg, var(--accent), #5a78f0);
    border: none;
    box-shadow: 0 6px 18px rgba(109,139,255,0.35);
}}
.stButton > button[kind="primary"]:hover {{ box-shadow: 0 8px 24px rgba(109,139,255,0.5); }}

.stTabs [data-baseweb="tab-list"] {{ gap: 4px; }}
.stTabs [data-baseweb="tab"] {{
    border-radius: 10px 10px 0 0; padding: 6px 14px;
    font-family: 'Sora'; font-weight: 500;
}}
.stTabs [aria-selected="true"] {{ background: var(--surface-2); }}

/* Inputs */
.stTextInput input, .stTextArea textarea, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {{
    border-radius: 11px !important;
}}
[data-testid="stMetricValue"] {{ font-family: 'Sora'; }}

/* Expander */
.streamlit-expanderHeader, details summary {{ font-family: 'Sora'; font-weight: 600; }}

/* ---- Sidebar ---- */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #0E1320 0%, #0B0E16 100%);
    border-right: 1px solid var(--border);
}}
[data-testid="stSidebar"] .brand {{
    font-family: 'Sora'; font-weight: 800; font-size: 1.15rem;
    display: flex; align-items: center; gap: 9px; margin: 2px 0 4px;
}}
[data-testid="stSidebar"] .brand .dot {{
    width: 10px; height: 10px; border-radius: 50%;
    background: linear-gradient(120deg, var(--accent), var(--accent-2));
    box-shadow: 0 0 12px rgba(55,215,194,0.7);
}}
[data-testid="stSidebar"] .brand-sub {{
    color: var(--muted); font-size: 0.72rem; letter-spacing: 0.14em;
    text-transform: uppercase; margin: -2px 0 8px 19px;
}}
[data-testid="stSidebarNav"] ul {{ padding-top: 4px; }}
[data-testid="stSidebarNav"] a {{ border-radius: 10px; }}

/* Hide Streamlit's auto-generated page nav — we render a custom one below. */
[data-testid="stSidebarNav"] {{ display: none; }}

/* ---- Custom sidebar navigation ---- */
[data-testid="stSidebar"] .nav-group {{
    font-family: 'Sora'; font-size: 0.68rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.15em; color: var(--muted);
    margin: 16px 2px 6px;
}}
/* page_link rows */
[data-testid="stSidebar"] [data-testid="stPageLink"] a,
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {{
    border-radius: 11px;
    padding: 7px 11px !important;
    font-family: 'Sora'; font-weight: 500;
    transition: background .15s ease, transform .12s ease;
}}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover,
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {{
    background: var(--surface-2);
    transform: translateX(2px);
}}

/* ---- Featured Voice card ---- */
.voice-feature {{
    position: relative;
    border-radius: 16px;
    padding: 14px 15px 13px;
    margin: 4px 0 6px;
    background:
        linear-gradient(135deg, rgba(55,215,194,0.18), rgba(109,139,255,0.14));
    border: 1px solid rgba(55,215,194,0.45);
    box-shadow: 0 6px 22px rgba(55,215,194,0.12);
    overflow: hidden;
}}
.voice-feature::before {{
    content: ""; position: absolute; inset: 0;
    background: radial-gradient(180px 80px at 90% -20%, rgba(55,215,194,0.30), transparent 70%);
    pointer-events: none;
}}
.voice-feature .vf-top {{ display: flex; align-items: center; gap: 9px; }}
.voice-feature .vf-mic {{
    width: 32px; height: 32px; border-radius: 10px; flex: none;
    display: grid; place-items: center; font-size: 1.05rem;
    background: linear-gradient(120deg, var(--accent-2), var(--accent));
    color: #06121f;
    box-shadow: 0 0 16px rgba(55,215,194,0.6);
    animation: vfpulse 2.6s ease-in-out infinite;
}}
@keyframes vfpulse {{
    0%,100% {{ box-shadow: 0 0 12px rgba(55,215,194,0.45); }}
    50% {{ box-shadow: 0 0 22px rgba(55,215,194,0.85); }}
}}
.voice-feature .vf-title {{ font-family: 'Sora'; font-weight: 700; font-size: 0.96rem; color: var(--text); line-height: 1; }}
.voice-feature .vf-badge {{
    font-family: 'Sora'; font-size: 0.58rem; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: var(--accent-2);
    border: 1px solid rgba(55,215,194,0.5); border-radius: 999px;
    padding: 2px 7px; margin-top: 3px; display: inline-block;
}}
.voice-feature .vf-desc {{ color: var(--muted); font-size: 0.76rem; line-height: 1.4; margin: 9px 0 0; }}
/* The actual link button inside the card gets a filled accent treatment */
.voice-feature + div [data-testid="stPageLink"] a {{
    background: linear-gradient(120deg, var(--accent-2), var(--accent)) !important;
    color: #06121f !important; font-weight: 700 !important;
    justify-content: center; margin-top: -2px;
}}
.voice-feature + div [data-testid="stPageLink"] a:hover {{ transform: translateY(-1px); filter: brightness(1.05); }}

/* User chip */
.user-chip {{
    display: flex; align-items: center; gap: 11px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 13px; padding: 10px 12px; margin: 6px 0 4px;
}}
.user-chip .avatar {{
    width: 34px; height: 34px; border-radius: 50%; flex: none;
    display: grid; place-items: center; font-family: 'Sora'; font-weight: 700;
    color: #08121f; background: linear-gradient(120deg, var(--accent-2), var(--accent));
}}
.user-chip .u-name {{ font-weight: 600; font-size: 0.9rem; color: var(--text); line-height: 1.1; }}
.user-chip .u-mail {{ font-size: 0.74rem; color: var(--muted); }}

/* Section eyebrow used across pages */
.section-eyebrow {{
    font-family: 'Sora'; font-size: 0.72rem; text-transform: uppercase;
    letter-spacing: 0.16em; color: var(--accent-2); font-weight: 600; margin-bottom: 2px;
}}

/* Sign-in card */
.signin-wrap {{ max-width: 460px; margin: 4vh auto 0; }}
.signin-card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 22px; padding: 34px 32px;
    box-shadow: 0 24px 60px rgba(0,0,0,0.45);
}}
.signin-logo {{
    width: 56px; height: 56px; border-radius: 16px; display: grid; place-items: center;
    font-size: 1.7rem; margin-bottom: 16px;
    background: linear-gradient(135deg, rgba(109,139,255,0.25), rgba(55,215,194,0.18));
    border: 1px solid var(--border);
}}

/* hide default footer/menu for a cleaner app shell */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}

/* staggered fade-in on load */
@keyframes rise {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: none; }} }}
.metric-card, .feature, .panel, .hero {{ animation: rise .5s ease both; }}
</style>
"""


def inject_global_css() -> None:
    """Inject the global stylesheet. Safe to call once per page render."""
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str = "", eyebrow: str = "") -> None:
    eb = f"<div class='eyebrow'>{eyebrow}</div>" if eyebrow else ""
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f"<div class='hero'>{eb}<h1>{title}</h1>{sub}</div>",
        unsafe_allow_html=True,
    )


def metric_card(col, value, label: str, trend: str = "", trend_kind: str = "") -> None:
    trend_html = ""
    if trend:
        color = {"good": GOOD, "bad": BAD, "warn": WARN}.get(trend_kind, MUTED)
        trend_html = f"<div class='mtrend' style='color:{color}'>{trend}</div>"
    col.markdown(
        f"<div class='metric-card'><div class='mval'>{value}</div>"
        f"<div class='mlabel'>{label}</div>{trend_html}</div>",
        unsafe_allow_html=True,
    )


def section_eyebrow(text: str) -> None:
    st.markdown(f"<div class='section-eyebrow'>{text}</div>", unsafe_allow_html=True)


def pill(text: str, kind: str = "accent") -> str:
    """Return HTML for an inline status pill (caller embeds in markdown)."""
    return f"<span class='pill {kind}'>{text}</span>"
