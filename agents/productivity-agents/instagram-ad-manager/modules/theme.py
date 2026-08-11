"""
theme.py — the premium design system (Instagram-inspired).

Holds the global CSS (purple→pink→orange gradients, glassmorphism cards, modern
typography, responsive grids) plus small HTML component builders that return
strings. Keeping presentation here keeps `app.py` and `ui.py` readable.
"""

from __future__ import annotations

# ── Brand palette (also used to theme Plotly) ─────────────────────────────────
PURPLE = "#833AB4"
MAGENTA = "#C13584"
PINK = "#E1306C"
RED = "#FD1D1D"
ORANGE = "#F56040"
AMBER = "#FCAF45"

# Categorical sequence for charts (distinct but on-brand).
GRADIENT_SEQ = [PURPLE, PINK, ORANGE, MAGENTA, "#4F5BD5", AMBER, RED]
# Continuous scale (low→high) for heat-style bars.
CONTINUOUS = [[0.0, "#4F5BD5"], [0.5, MAGENTA], [1.0, AMBER]]

HERO_GRADIENT = f"linear-gradient(135deg, {PURPLE} 0%, {PINK} 55%, {ORANGE} 100%)"

# Severity → accent color (notifications / health).
SEVERITY = {
    "success": "#16a34a",
    "info": "#4F5BD5",
    "warning": "#d97706",
    "critical": "#dc2626",
}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Sora:wght@600;700;800&display=swap');

:root {{
  --grad: {HERO_GRADIENT};
  --purple: {PURPLE};
  --pink: {PINK};
  --orange: {ORANGE};
  --ink: #1e1633;
  --muted: #6b7280;
  --card: rgba(255,255,255,0.72);
  --border: rgba(131,58,180,0.14);
  --shadow: 0 10px 30px rgba(131,58,180,0.10);
}}

html, body, [class*="css"], .stMarkdown, p, span, div {{ font-family: 'Inter', sans-serif; }}
h1, h2, h3, h4 {{ font-family: 'Sora', 'Inter', sans-serif; color: var(--ink); letter-spacing: -0.01em; }}

/* App background — soft brand wash so glass cards pop */
[data-testid="stAppViewContainer"] {{
  background:
    radial-gradient(1200px 600px at 88% -8%, rgba(245,96,64,0.10), transparent 60%),
    radial-gradient(1000px 620px at -8% 8%, rgba(131,58,180,0.12), transparent 55%),
    linear-gradient(180deg, #faf7ff 0%, #fdf4fb 100%);
}}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1300px; }}

/* ── Sidebar — deep frosted gradient ── */
[data-testid="stSidebar"] {{
  background: linear-gradient(185deg, #3a0d52 0%, #6d1a67 52%, #7a1f52 100%) !important;
  border-right: 1px solid rgba(255,255,255,0.08);
}}
[data-testid="stSidebar"] * {{ color: #f6ecff !important; }}
[data-testid="stSidebar"] .stRadio label p {{ font-size: 14.5px !important; font-weight: 500; }}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{ color:#e7d6ff !important; font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:.06em; }}

/* Form controls in the sidebar: solid white fields with dark, readable text
   (the global near-white sidebar text color would otherwise hide the value). */
[data-testid="stSidebar"] [data-baseweb="select"] > div {{
  background: #ffffff !important; border-color: rgba(255,255,255,0.35) !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="select"] * {{ color: #2b0a3d !important; }}
[data-testid="stSidebar"] [data-baseweb="select"] svg {{ fill: #7c3aed !important; }}
[data-testid="stSidebar"] input {{
  background: #ffffff !important; color: #2b0a3d !important;
  border-color: rgba(255,255,255,0.35) !important; -webkit-text-fill-color: #2b0a3d !important;
}}
[data-testid="stSidebar"] input::placeholder {{ color: #9b7cc0 !important; -webkit-text-fill-color: #9b7cc0 !important; }}

/* Radio nav → pill list */
[data-testid="stSidebar"] div[role="radiogroup"] > label {{
  border-radius: 12px; padding: 7px 10px; margin: 1px 0; transition: all .15s ease;
}}
[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {{ background: rgba(255,255,255,0.08); }}

/* ── Buttons — gradient pills ── */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {{
  border-radius: 12px !important; font-weight: 600 !important; border: 1px solid var(--border) !important;
  transition: transform .12s ease, box-shadow .12s ease; background: #fff; color: var(--ink);
}}
.stButton > button:hover {{ transform: translateY(-1px); box-shadow: var(--shadow); }}
.stButton > button[kind="primary"], .stFormSubmitButton > button {{
  background: var(--grad) !important; color: #fff !important; border: none !important;
  box-shadow: 0 8px 20px rgba(225,48,108,0.28) !important;
}}
.stButton > button[kind="primary"]:hover {{ filter: brightness(1.05); transform: translateY(-1px); }}

/* ── Hero header ── */
.hero {{
  background: var(--grad); border-radius: 22px; padding: 22px 26px; color:#fff;
  box-shadow: 0 16px 40px rgba(131,58,180,0.30); margin-bottom: 18px;
  display:flex; align-items:center; justify-content:space-between; gap:18px; flex-wrap:wrap;
}}
.hero h1 {{ color:#fff !important; font-size: 26px; margin:0; }}
.hero .sub {{ color: rgba(255,255,255,0.92); font-size: 14px; margin-top:2px; }}
.hero .chip {{ background: rgba(255,255,255,0.18); border:1px solid rgba(255,255,255,0.28);
  padding:8px 14px; border-radius:999px; font-weight:600; font-size:13px; backdrop-filter: blur(6px); }}

/* ── Glass KPI cards ── */
.kpi-grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(185px, 1fr)); gap:14px; margin: 4px 0 20px; }}
.kpi {{
  position:relative; overflow:hidden; background: var(--card);
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
  border:1px solid var(--border); border-radius:18px; padding:16px 18px; box-shadow: var(--shadow);
  transition: transform .15s ease, box-shadow .15s ease;
}}
.kpi:hover {{ transform: translateY(-3px); box-shadow: 0 16px 38px rgba(131,58,180,0.16); }}
.kpi::before {{ content:""; position:absolute; inset:0 auto auto 0; width:100%; height:4px; background: var(--grad); opacity:.9; }}
.kpi .top {{ display:flex; align-items:center; justify-content:space-between; }}
.kpi .label {{ font-size:11.5px; font-weight:700; color:#8a5cb8; text-transform:uppercase; letter-spacing:.05em; }}
.kpi .icon {{ width:30px; height:30px; border-radius:9px; display:grid; place-items:center; font-size:15px;
  background: linear-gradient(135deg, rgba(131,58,180,0.14), rgba(245,96,64,0.14)); }}
.kpi .value {{ font-family:'Sora'; font-size:27px; font-weight:800; color:var(--ink); margin-top:8px; line-height:1.1; }}
.kpi .sub {{ font-size:12px; color:var(--muted); margin-top:3px; }}
.kpi .delta {{ font-size:12px; font-weight:700; margin-top:4px; }}
.delta-up {{ color:#16a34a; }} .delta-down {{ color:#dc2626; }} .delta-flat {{ color:#6b7280; }}

/* ── Generic glass panel ── */
.glass {{ background: var(--card); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
  border:1px solid var(--border); border-radius:18px; padding:18px 20px; box-shadow: var(--shadow); margin-bottom:14px; }}
.glass h3 {{ margin-top:0; }}

/* Section header */
.sec {{ display:flex; align-items:center; gap:10px; margin: 6px 0 2px; }}
.sec .ic {{ width:34px; height:34px; border-radius:10px; display:grid; place-items:center; color:#fff; background:var(--grad); font-size:16px; }}
.sec .t {{ font-family:'Sora'; font-weight:700; font-size:18px; color:var(--ink); }}
.sec .d {{ color:var(--muted); font-size:13px; }}

/* Badges / pills */
.badge {{ display:inline-block; padding:3px 11px; border-radius:999px; font-size:12px; font-weight:700; }}
.b-active {{ background:#e7f9ee; color:#0f8a3c; }}
.b-paused {{ background:#fff3e0; color:#b5730a; }}
.b-completed {{ background:#eef0f5; color:#586074; }}
.pill {{ display:inline-block; padding:3px 10px; border-radius:999px; font-size:11.5px; font-weight:700; border:1px solid var(--border); }}
.pill-conf {{ background: linear-gradient(135deg, rgba(79,91,213,0.12), rgba(131,58,180,0.12)); color:#4b2a86; }}
.pill-impact {{ background: linear-gradient(135deg, rgba(245,96,64,0.14), rgba(252,175,69,0.16)); color:#9a3d16; }}
.pri-high {{ color:#dc2626; font-weight:800; }}
.pri-medium {{ color:#d97706; font-weight:800; }}
.pri-low {{ color:#586074; font-weight:700; }}

/* Recommendation cards */
.rec-card {{ background: var(--card); backdrop-filter: blur(10px); border:1px solid var(--border);
  border-left:4px solid var(--pink); border-radius:14px; padding:14px 16px; margin-bottom:10px; box-shadow: var(--shadow); }}
.rec-card .rt {{ font-family:'Sora'; font-weight:700; color:#7c1fa8; font-size:15px; }}
.rec-meta {{ color:var(--muted); font-size:12px; margin-top:6px; }}

/* Notifications */
.notif {{ display:flex; gap:12px; align-items:flex-start; background:var(--card); border:1px solid var(--border);
  border-radius:14px; padding:12px 14px; margin-bottom:9px; box-shadow: var(--shadow); }}
.notif .dot {{ width:10px; height:10px; border-radius:50%; margin-top:6px; flex:none; }}
.notif .nt {{ font-weight:700; color:var(--ink); font-size:14px; }}
.notif .nb {{ color:#4b5563; font-size:13px; margin-top:2px; }}
.notif .nm {{ color:#9ca3af; font-size:11px; margin-top:4px; }}
.notif.unread {{ box-shadow: 0 10px 26px rgba(225,48,108,0.14); border-color: rgba(225,48,108,0.28); }}

/* Health */
.grade {{ font-family:'Sora'; font-weight:800; font-size:56px; line-height:1;
  background: var(--grad); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }}
.comp {{ display:flex; align-items:center; gap:12px; margin:9px 0; }}
.comp .cn {{ width:180px; font-weight:600; color:var(--ink); font-size:13.5px; }}
.comp .bar {{ flex:1; height:9px; border-radius:999px; background:#efe7fb; overflow:hidden; }}
.comp .fill {{ height:100%; border-radius:999px; background: var(--grad); }}
.comp .cv {{ width:46px; text-align:right; font-weight:700; color:#4b2a86; font-size:13px; }}

/* Tables */
div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {{ border-radius:14px; overflow:hidden; border:1px solid var(--border); }}

/* Chat */
[data-testid="stChatMessage"] {{ background: var(--card) !important; border:1px solid var(--border);
  border-radius:16px; box-shadow: var(--shadow); }}

.section-note {{ color:var(--muted); font-size:14px; margin:-4px 0 10px; }}
hr {{ border-color: var(--border); }}

@media (max-width: 640px) {{
  .hero {{ padding:16px; }} .hero h1 {{ font-size:21px; }}
  .kpi-grid {{ grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); }}
}}
</style>
"""


# ── HTML component builders (return strings) ──────────────────────────────────
def hero(title: str, subtitle: str, chip: str = "") -> str:
    chip_html = f'<div class="chip">{chip}</div>' if chip else ""
    return (
        f'<div class="hero"><div><h1>{title}</h1><div class="sub">{subtitle}</div></div>'
        f"{chip_html}</div>"
    )


def section(title: str, desc: str = "", icon: str = "✨") -> str:
    d = f'<div class="d">{desc}</div>' if desc else ""
    return f'<div class="sec"><div class="ic">{icon}</div><div><div class="t">{title}</div>{d}</div></div>'


def _delta_html(delta: str | None) -> str:
    if not delta:
        return ""
    cls = "delta-flat"
    if delta.startswith("+") or "▲" in delta:
        cls = "delta-up"
    elif delta.startswith("-") or "▼" in delta:
        cls = "delta-down"
    return f'<div class="delta {cls}">{delta}</div>'


def kpi_card(label: str, value: str, sub: str = "", icon: str = "📊", delta: str | None = None) -> str:
    return (
        f'<div class="kpi"><div class="top"><div class="label">{label}</div>'
        f'<div class="icon">{icon}</div></div>'
        f'<div class="value">{value}</div>'
        f'<div class="sub">{sub}</div>{_delta_html(delta)}</div>'
    )


def kpi_grid(cards: list[str]) -> str:
    return '<div class="kpi-grid">' + "".join(cards) + "</div>"


def badge(text: str, kind: str = "completed") -> str:
    cls = {"Active": "b-active", "Paused": "b-paused", "Completed": "b-completed"}.get(text, f"b-{kind}")
    return f'<span class="badge {cls}">{text}</span>'


def confidence_pill(pct) -> str:
    try:
        return f'<span class="pill pill-conf">◎ {int(round(float(pct)))}% confidence</span>'
    except Exception:
        return ""


def impact_pill(text: str) -> str:
    return f'<span class="pill pill-impact">⚡ {text}</span>' if text else ""


def notification_html(n: dict) -> str:
    color = SEVERITY.get(n.get("severity", "info"), SEVERITY["info"])
    unread = "" if n.get("read") else "unread"
    when = (n.get("created_at", "") or "")[:16].replace("T", " ")
    return (
        f'<div class="notif {unread}"><div class="dot" style="background:{color}"></div>'
        f'<div><div class="nt">{n.get("title","")}</div>'
        f'<div class="nb">{n.get("body","")}</div>'
        f'<div class="nm">{n.get("category","")} · {when}</div></div></div>'
    )
