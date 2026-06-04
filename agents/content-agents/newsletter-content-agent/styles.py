"""
Custom CSS for a distinctive dark-mode Streamlit UI.

Aesthetic direction: "editorial dark" — an ink-black canvas, a single electric
violet accent, a serif display face (Fraunces) paired with a clean grotesque
body face (Sora). Card surfaces float on subtle elevation with a faint violet
glow. The look is intentionally not the default Streamlit theme.
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,900&family=Sora:wght@300;400;500;600;700&display=swap');

:root {
  --bg: #0c0b10;
  --surface: #16151d;
  --surface-2: #1e1d28;
  --border: #2a2935;
  --accent: #8b7cff;
  --accent-2: #6c5ce7;
  --text: #ece9f5;
  --muted: #8f8ba3;
  --good: #3ddc97;
  --warn: #ffb86b;
}

.stApp { background: radial-gradient(1200px 600px at 80% -10%, #1a1330 0%, var(--bg) 55%); }
html, body, [class*="css"], .stMarkdown, p, span, label { font-family: 'Sora', sans-serif; color: var(--text); }

h1, h2, h3 { font-family: 'Fraunces', serif !important; color: var(--text) !important; letter-spacing: -0.02em; }
h1 { font-weight: 900 !important; }

section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #110f18 0%, #0a0910 100%);
  border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] * { color: var(--text); }

.block-container { padding-top: 2.2rem; max-width: 1180px; }

/* Brand block */
.brand {
  font-family: 'Fraunces', serif; font-weight: 900; font-size: 30px;
  background: linear-gradient(92deg, #fff 10%, var(--accent) 90%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  margin-bottom: 0;
}
.brand-sub { color: var(--muted); font-size: 12.5px; letter-spacing: .14em; text-transform: uppercase; margin-top: -2px; }

/* Metric / stat cards */
.stat-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 16px;
  padding: 18px 20px; position: relative; overflow: hidden;
}
.stat-card::after {
  content:''; position:absolute; inset:0; border-radius:16px;
  background: radial-gradient(420px 120px at 100% 0%, rgba(139,124,255,.14), transparent 60%);
  pointer-events:none;
}
.stat-value { font-family:'Fraunces',serif; font-size: 34px; font-weight: 900; line-height:1; }
.stat-label { color: var(--muted); font-size: 12.5px; text-transform: uppercase; letter-spacing:.1em; margin-top:8px; }

/* Generic surface panel */
.panel {
  background: var(--surface); border:1px solid var(--border); border-radius:16px;
  padding: 22px 24px; margin-bottom: 16px;
}

.tag {
  display:inline-block; padding: 3px 11px; border-radius: 999px; font-size: 11.5px;
  background: rgba(139,124,255,.14); color: var(--accent); border:1px solid rgba(139,124,255,.3);
  margin-right:6px; letter-spacing:.03em;
}
.tag.good { background: rgba(61,220,151,.12); color: var(--good); border-color: rgba(61,220,151,.3);}
.tag.warn { background: rgba(255,184,107,.12); color: var(--warn); border-color: rgba(255,184,107,.3);}

.item-row {
  border-bottom:1px solid var(--border); padding:12px 0;
}
.item-title { font-weight:600; font-size:15px; }
.item-meta { color: var(--muted); font-size:12.5px; margin-top:3px; }

/* Buttons */
.stButton > button {
  background: var(--accent-2); color:#fff; border:0; border-radius:10px;
  font-family:'Sora',sans-serif; font-weight:600; padding:.5rem 1.1rem;
  transition: transform .08s ease, box-shadow .2s ease;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 8px 24px rgba(108,92,231,.35); }

/* Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
  background: var(--surface-2) !important; color: var(--text) !important;
  border:1px solid var(--border) !important; border-radius:10px !important;
}

/* Tabs */
.stTabs [data-baseweb="tab"] { font-family:'Sora',sans-serif; color: var(--muted); }
.stTabs [aria-selected="true"] { color: var(--accent) !important; }

/* Progress / divider */
hr { border-color: var(--border); }
.small-muted { color: var(--muted); font-size: 12.5px; }
.kicker { color: var(--accent); font-size:12px; letter-spacing:.16em; text-transform:uppercase; font-weight:600; }
</style>
"""


def stat_card(value, label) -> str:
    return f'<div class="stat-card"><div class="stat-value">{value}</div><div class="stat-label">{label}</div></div>'
