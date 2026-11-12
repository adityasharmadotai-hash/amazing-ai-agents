"""
ui.py — Agentic visual layer for the SEO Audit Agent.

Houses "Scout", the animated SEO agent character, plus a library of
animated, self-contained HTML/SVG components (gauges, heartbeat pulse line,
health-zone cards, fill-on-load bars, count-up stats, speech bubble).

Everything here returns an HTML string or renders via st.markdown so it can be
dropped into any Streamlit page. No external assets — all inline SVG + CSS.
"""

from __future__ import annotations

import re


def _flat(html: str) -> str:
    """Collapse inter-tag whitespace/newlines so Streamlit's markdown parser
    never mistakes an indented HTML fragment for a code block. Text *inside*
    leaf tags is preserved — only whitespace between a '>' and a '<' is removed."""
    return re.sub(r">\s+<", "><", html).strip()


# ── Palette ───────────────────────────────────────────────────────────────────
INDIGO = "#4f46e5"
VIOLET = "#7c3aed"
GREEN  = "#22c55e"
LIME   = "#84cc16"
AMBER  = "#f59e0b"
RED    = "#ef4444"
SLATE  = "#64748b"


# ── Health helpers ────────────────────────────────────────────────────────────
def health_color(score: int) -> str:
    if score >= 85: return GREEN
    if score >= 70: return LIME
    if score >= 50: return AMBER
    return RED


def health_word(score: int) -> str:
    if score >= 85: return "Thriving"
    if score >= 70: return "Healthy"
    if score >= 50: return "Needs Focus"
    return "Critical"


def mascot_mood(score: int) -> str:
    """Maps an overall score to one of Scout's four moods."""
    if score >= 85: return "thriving"
    if score >= 70: return "content"
    if score >= 50: return "concerned"
    return "worried"


# ══════════════════════════════════════════════════════════════════════════════
# ANIMATION STYLESHEET  (inject once per page)
# ══════════════════════════════════════════════════════════════════════════════
def animations_css() -> str:
    return """
<style>
/* ── keyframes ─────────────────────────────────────────────── */
@keyframes scout-float   { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)} }
@keyframes scout-blink   { 0%,92%,100%{transform:scaleY(1)} 96%{transform:scaleY(0.1)} }
@keyframes scout-glow    { 0%,100%{opacity:.55;transform:scale(1)} 50%{opacity:1;transform:scale(1.12)} }
@keyframes sonar         { 0%{transform:scale(.6);opacity:.7} 100%{transform:scale(1.9);opacity:0} }
@keyframes antenna-pulse { 0%,100%{transform:scale(1);filter:drop-shadow(0 0 2px #a78bfa)} 50%{transform:scale(1.4);filter:drop-shadow(0 0 8px #a78bfa)} }
@keyframes ekg-dash      { to{stroke-dashoffset:-1000} }
@keyframes ekg-dot       { 0%{offset-distance:0%} 100%{offset-distance:100%} }
@keyframes ring-sweep    { from{stroke-dashoffset:var(--circ)} to{stroke-dashoffset:var(--target)} }
@keyframes bar-grow      { from{width:0} to{width:var(--w)} }
@keyframes pop-in        { 0%{transform:scale(.85);opacity:0} 100%{transform:scale(1);opacity:1} }
@keyframes shimmer       { 0%{background-position:-400px 0} 100%{background-position:400px 0} }
@keyframes spin-slow     { to{transform:rotate(360deg)} }
@keyframes badge-pulse   { 0%,100%{box-shadow:0 0 0 0 rgba(34,197,94,.55)} 50%{box-shadow:0 0 0 7px rgba(34,197,94,0)} }
@keyframes drift         { 0%,100%{transform:translate(0,0)} 33%{transform:translate(6px,-7px)} 66%{transform:translate(-5px,5px)} }

/* ── live badge ────────────────────────────────────────────── */
.live-badge{
    display:inline-flex;align-items:center;gap:7px;
    background:#0f172a;color:#e2e8f0;border-radius:20px;
    padding:5px 14px;font-size:12px;font-weight:700;letter-spacing:.04em;
}
.live-dot{width:9px;height:9px;border-radius:50%;background:#22c55e;
    animation:badge-pulse 1.6s infinite;}

/* ── speech bubble ─────────────────────────────────────────── */
.scout-bubble{
    position:relative;background:white;border:1.5px solid #e0e7ff;
    border-radius:16px;padding:14px 18px;max-width:520px;
    box-shadow:0 6px 22px rgba(79,70,229,.10);
    animation:pop-in .5s ease both;
}
.scout-bubble:after{
    content:"";position:absolute;left:-9px;top:26px;width:16px;height:16px;
    background:white;border-left:1.5px solid #e0e7ff;border-bottom:1.5px solid #e0e7ff;
    transform:rotate(45deg);
}
.scout-bubble .who{font-size:11px;font-weight:800;color:#7c3aed;
    text-transform:uppercase;letter-spacing:.08em;margin-bottom:3px;}
.scout-bubble .say{font-size:14px;color:#1e293b;line-height:1.55;}

/* ── health zone cards ─────────────────────────────────────── */
.zone-wrap{display:flex;flex-direction:column;gap:8px;}
.zone-card{
    display:flex;align-items:center;gap:12px;
    background:white;border:1px solid #e2e8f0;border-left-width:5px;
    border-radius:12px;padding:11px 15px;
    animation:pop-in .45s ease both;transition:transform .15s,box-shadow .15s;
}
.zone-card:hover{transform:translateX(4px);box-shadow:0 6px 18px rgba(0,0,0,.08);}
.zone-emoji{font-size:22px;width:30px;text-align:center;flex-shrink:0;}
.zone-name{font-size:13px;font-weight:700;color:#0f172a;}
.zone-meta{font-size:11px;color:#64748b;margin-top:1px;}
.zone-score{margin-left:auto;font-size:20px;font-weight:900;}
.zone-pill{font-size:10px;font-weight:800;text-transform:uppercase;
    letter-spacing:.05em;padding:2px 8px;border-radius:20px;margin-left:8px;}

/* ── animated category bars ────────────────────────────────── */
.abar-row{margin:9px 0;animation:pop-in .4s ease both;}
.abar-top{display:flex;justify-content:space-between;font-size:12px;
    font-weight:600;color:#334155;margin-bottom:4px;}
.abar-track{background:#eef2f7;border-radius:7px;height:11px;overflow:hidden;}
.abar-fill{height:11px;border-radius:7px;animation:bar-grow 1.1s cubic-bezier(.22,1,.36,1) both;
    background-size:400px 100%;}

/* ── count-up stat tiles ───────────────────────────────────── */
.stat-tile{
    background:white;border:1px solid #e2e8f0;border-radius:14px;
    padding:15px 12px;text-align:center;animation:pop-in .5s ease both;
    transition:transform .15s,box-shadow .15s;
}
.stat-tile:hover{transform:translateY(-3px);box-shadow:0 8px 20px rgba(0,0,0,.07);}
.stat-num{font-size:26px;font-weight:900;line-height:1;}
.stat-lbl{font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;
    letter-spacing:.05em;margin-top:5px;}

/* ── floating focus chips ──────────────────────────────────── */
.focus-chip{
    display:inline-flex;align-items:center;gap:6px;
    background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;
    border-radius:20px;padding:6px 13px;font-size:12px;font-weight:600;
    margin:4px;animation:drift 6s ease-in-out infinite;
}
.focus-chip.crit{background:#fef2f2;border-color:#fecaca;color:#b91c1c;}
.focus-chip.win{background:#f0fdf4;border-color:#bbf7d0;color:#15803d;animation:none;}
</style>
"""


# ══════════════════════════════════════════════════════════════════════════════
# SCOUT — the agent character
# ══════════════════════════════════════════════════════════════════════════════
_MOUTHS = {
    "thriving":  "M40 70 Q60 90 80 70",   # big smile
    "content":   "M44 72 Q60 82 76 72",   # gentle smile
    "concerned": "M44 76 L76 76",          # flat line
    "worried":   "M44 80 Q60 70 76 80",   # frown
}
_EYE = {
    "thriving":  GREEN,
    "content":   LIME,
    "concerned": AMBER,
    "worried":   RED,
}


def scout_svg(mood: str = "content", size: int = 170, sonar: bool = True) -> str:
    """Inline animated SVG of Scout, the SEO agent. Mood drives eye colour + mouth."""
    mouth = _MOUTHS.get(mood, _MOUTHS["content"])
    eye   = _EYE.get(mood, LIME)
    sonar_rings = ""
    if sonar:
        sonar_rings = ('<circle cx="60" cy="60" r="40" fill="none" stroke="#a78bfa" stroke-width="2" '
                       'style="transform-origin:60px 60px;animation:sonar 2.6s ease-out infinite"/>'
                       '<circle cx="60" cy="60" r="40" fill="none" stroke="#a78bfa" stroke-width="2" '
                       'style="transform-origin:60px 60px;animation:sonar 2.6s ease-out infinite 1.3s"/>')
    return (
      f'<div style="width:{size}px;height:{size}px;margin:0 auto;animation:scout-float 4s ease-in-out infinite;">'
      f'<svg viewBox="0 0 120 130" width="{size}" height="{size}">'
      '<defs>'
      '<linearGradient id="scoutBody" x1="0" y1="0" x2="1" y2="1">'
      '<stop offset="0" stop-color="#6366f1"/><stop offset="1" stop-color="#7c3aed"/></linearGradient>'
      '<radialGradient id="scoutGlow" cx="50%" cy="45%" r="55%">'
      '<stop offset="0" stop-color="#a78bfa" stop-opacity=".55"/>'
      '<stop offset="1" stop-color="#a78bfa" stop-opacity="0"/></radialGradient>'
      '</defs>'
      '<ellipse cx="60" cy="60" rx="56" ry="56" fill="url(#scoutGlow)" '
      'style="transform-origin:60px 60px;animation:scout-glow 3s ease-in-out infinite"/>'
      f'{sonar_rings}'
      '<line x1="60" y1="18" x2="60" y2="6" stroke="#a78bfa" stroke-width="3" stroke-linecap="round"/>'
      '<circle cx="60" cy="5" r="4.5" fill="#c4b5fd" '
      'style="transform-origin:60px 5px;animation:antenna-pulse 1.8s ease-in-out infinite"/>'
      '<rect x="22" y="20" width="76" height="68" rx="22" fill="url(#scoutBody)"/>'
      '<rect x="22" y="20" width="76" height="68" rx="22" fill="none" '
      'stroke="#c4b5fd" stroke-opacity=".4" stroke-width="1.5"/>'
      '<rect x="32" y="32" width="56" height="44" rx="14" fill="#0b1020"/>'
      '<g style="transform-origin:48px 52px;animation:scout-blink 4.4s infinite">'
      f'<circle cx="48" cy="52" r="6.5" fill="{eye}"/>'
      '<circle cx="50" cy="50" r="2" fill="#fff" opacity=".9"/></g>'
      '<g style="transform-origin:72px 52px;animation:scout-blink 4.4s infinite">'
      f'<circle cx="72" cy="52" r="6.5" fill="{eye}"/>'
      '<circle cx="74" cy="50" r="2" fill="#fff" opacity=".9"/></g>'
      f'<path d="{mouth}" fill="none" stroke="{eye}" stroke-width="3" stroke-linecap="round" '
      'transform="translate(0,-6) scale(1,0.9)"/>'
      '<circle cx="20" cy="54" r="5" fill="#7c3aed"/>'
      '<circle cx="100" cy="54" r="5" fill="#7c3aed"/>'
      '<g transform="translate(78,78) rotate(20)">'
      '<circle cx="10" cy="10" r="11" fill="none" stroke="#fbbf24" stroke-width="4"/>'
      '<circle cx="10" cy="10" r="11" fill="#fde68a" opacity=".18"/>'
      '<line x1="18" y1="18" x2="30" y2="30" stroke="#fbbf24" stroke-width="5" stroke-linecap="round"/></g>'
      '<rect x="40" y="88" width="14" height="9" rx="4" fill="#6366f1"/>'
      '<rect x="66" y="88" width="14" height="9" rx="4" fill="#6366f1"/>'
      '</svg></div>'
    )


def scout_mini(mood: str = "content", size: int = 54) -> str:
    """Compact face-only Scout for the sidebar logo."""
    eye = _EYE.get(mood, LIME)
    return _flat(f"""
    <div style="width:{size}px;height:{size}px;margin:0 auto;">
      <svg viewBox="0 0 60 60" width="{size}" height="{size}">
        <defs><linearGradient id="sm" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#6366f1"/><stop offset="1" stop-color="#7c3aed"/>
        </linearGradient></defs>
        <line x1="30" y1="9" x2="30" y2="3" stroke="#a78bfa" stroke-width="2.5" stroke-linecap="round"/>
        <circle cx="30" cy="3" r="3" fill="#c4b5fd"
                style="transform-origin:30px 3px;animation:antenna-pulse 1.8s ease-in-out infinite"/>
        <rect x="9" y="10" width="42" height="40" rx="13" fill="url(#sm)"/>
        <rect x="15" y="17" width="30" height="26" rx="9" fill="#0b1020"/>
        <g style="transform-origin:25px 30px;animation:scout-blink 4.4s infinite">
          <circle cx="25" cy="29" r="4" fill="{eye}"/></g>
        <g style="transform-origin:37px 30px;animation:scout-blink 4.4s infinite">
          <circle cx="37" cy="29" r="4" fill="{eye}"/></g>
        <path d="M24 37 Q31 42 38 37" fill="none" stroke="{eye}" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </div>
    """)


def scout_bubble(message: str, name: str = "Scout · SEO Agent") -> str:
    return _flat(f"""
    <div class="scout-bubble">
        <div class="who">{name}</div>
        <div class="say">{message}</div>
    </div>
    """)


# ══════════════════════════════════════════════════════════════════════════════
# ANIMATED GAUGE
# ══════════════════════════════════════════════════════════════════════════════
def gauge(score: int, size: int = 200, label: str = "SEO HEALTH") -> str:
    color = health_color(score)
    word  = health_word(score)
    r = (size / 2) - 16
    cx = cy = size / 2
    circ = 2 * 3.14159 * r
    target = circ * (1 - score / 100)
    stroke = max(10, int(size * 0.07))
    return _flat(f"""
    <div style="position:relative;width:{size}px;height:{size}px;margin:0 auto;">
      <svg width="{size}" height="{size}" style="transform:rotate(-90deg);">
        <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#eef2f7" stroke-width="{stroke}"/>
        <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{stroke}"
            stroke-linecap="round" stroke-dasharray="{circ:.1f}"
            style="--circ:{circ:.1f};--target:{target:.1f};
                   stroke-dashoffset:{target:.1f};
                   animation:ring-sweep 1.4s cubic-bezier(.22,1,.36,1) both;
                   filter:drop-shadow(0 0 6px {color}66);"/>
      </svg>
      <div style="position:absolute;inset:0;display:flex;flex-direction:column;
                  align-items:center;justify-content:center;">
        <div style="font-size:{int(size*0.30)}px;font-weight:900;color:{color};line-height:1;">{score}</div>
        <div style="font-size:11px;font-weight:800;color:{color};text-transform:uppercase;
                    letter-spacing:.06em;margin-top:2px;">{word}</div>
        <div style="font-size:9px;color:#94a3b8;font-weight:700;letter-spacing:.1em;margin-top:3px;">{label}</div>
      </div>
    </div>
    """)


# ══════════════════════════════════════════════════════════════════════════════
# HEARTBEAT / PULSE LINE  (animated EKG to signal "live")
# ══════════════════════════════════════════════════════════════════════════════
def pulse_line(score: int, height: int = 70) -> str:
    color = health_color(score)
    # Faster, spikier trace for unhealthy sites; calmer for healthy ones.
    path = ("M0 35 L60 35 L72 12 L84 58 L96 35 L160 35 L172 12 L184 58 L196 35 "
            "L260 35 L272 12 L284 58 L296 35 L360 35 L372 12 L384 58 L396 35 "
            "L460 35 L472 12 L484 58 L496 35 L560 35 L572 12 L584 58 L596 35 L1000 35")
    return _flat(f"""
    <div style="background:#0b1020;border-radius:14px;padding:6px 4px;overflow:hidden;
                box-shadow:inset 0 0 22px rgba(124,58,237,.25);">
      <svg viewBox="0 0 600 {height}" width="100%" height="{height}" preserveAspectRatio="none">
        <path d="{path}" fill="none" stroke="{color}" stroke-width="2.5"
              stroke-linejoin="round" stroke-linecap="round"
              stroke-dasharray="600 400" style="animation:ekg-dash 3.2s linear infinite;
              filter:drop-shadow(0 0 5px {color});"/>
      </svg>
    </div>
    """)


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH ZONES  (categories sorted into good / focus / critical)
# ══════════════════════════════════════════════════════════════════════════════
_CAT_META = [
    ("meta",      "Meta Tags",  "🏷️"),
    ("headings",  "Headings",   "📝"),
    ("keywords",  "Keywords",   "🔑"),
    ("technical", "Technical",  "⚙️"),
    ("images",    "Images",     "🖼️"),
    ("links",     "Links",      "🔗"),
]


def _cat_issue_summary(cat: dict) -> str:
    crit = sum(1 for i in cat.get("issues", []) if i.get("severity") == "critical")
    warn = sum(1 for i in cat.get("issues", []) if i.get("severity") == "warning")
    bits = []
    if crit: bits.append(f"{crit} critical")
    if warn: bits.append(f"{warn} warning{'s' if warn > 1 else ''}")
    return " · ".join(bits) if bits else "all checks passing"


def zone_card(key: str, name: str, emoji: str, audit: dict, delay: float) -> str:
    cat   = audit.get(key, {})
    score = cat.get("score", 0)
    color = health_color(score)
    pill  = health_word(score)
    pill_bg = {GREEN: "#dcfce7", LIME: "#ecfccb", AMBER: "#fef3c7", RED: "#fee2e2"}.get(color, "#f1f5f9")
    return _flat(f"""
    <div class="zone-card" style="border-left-color:{color};animation-delay:{delay:.2f}s;">
        <div class="zone-emoji">{emoji}</div>
        <div>
            <div class="zone-name">{name}
              <span class="zone-pill" style="background:{pill_bg};color:{color};">{pill}</span>
            </div>
            <div class="zone-meta">{_cat_issue_summary(cat)}</div>
        </div>
        <div class="zone-score" style="color:{color};">{score}</div>
    </div>
    """)


def health_zones(audit: dict):
    """Returns (good_html, focus_html, critical_html) lists of zone cards."""
    buckets = {"good": [], "focus": [], "critical": []}
    for i, (key, name, emoji) in enumerate(_CAT_META):
        score = audit.get(key, {}).get("score", 0)
        bucket = "good" if score >= 70 else ("focus" if score >= 50 else "critical")
        buckets[bucket].append(zone_card(key, name, emoji, audit, delay=0.06 * i))
    return buckets


# ══════════════════════════════════════════════════════════════════════════════
# ANIMATED CATEGORY BARS
# ══════════════════════════════════════════════════════════════════════════════
def animated_bars(audit: dict) -> str:
    rows = []
    for i, (key, name, emoji) in enumerate(_CAT_META):
        score = audit.get(key, {}).get("score", 0)
        color = health_color(score)
        grad  = f"linear-gradient(90deg,{color},{color}); background-image:linear-gradient(90deg,{color}cc,{color})"
        rows.append(f"""
        <div class="abar-row" style="animation-delay:{0.05*i:.2f}s;">
            <div class="abar-top">
                <span>{emoji} {name}</span>
                <span style="color:{color};font-weight:800;">{score}/100</span>
            </div>
            <div class="abar-track">
                <div class="abar-fill" style="--w:{score}%;background:{grad};
                     animation-delay:{0.05*i:.2f}s;"></div>
            </div>
        </div>
        """)
    return _flat("".join(rows))


# ══════════════════════════════════════════════════════════════════════════════
# COUNT-UP STAT TILES
# ══════════════════════════════════════════════════════════════════════════════
def stat_tiles(tiles: list) -> str:
    """tiles: list of (value, label, color)."""
    out = []
    for i, (val, lbl, color) in enumerate(tiles):
        out.append(f"""
        <div class="stat-tile" style="animation-delay:{0.07*i:.2f}s;">
            <div class="stat-num" style="color:{color};">{val}</div>
            <div class="stat-lbl">{lbl}</div>
        </div>
        """)
    return _flat("".join(out))


# ══════════════════════════════════════════════════════════════════════════════
# FOCUS CHIPS  (top things to fix / wins, floating)
# ══════════════════════════════════════════════════════════════════════════════
def focus_chips(audit: dict, limit: int = 6) -> str:
    chips = []
    for key, name, emoji in _CAT_META:
        for iss in audit.get(key, {}).get("issues", []):
            sev = iss.get("severity")
            if sev == "critical":
                chips.append(("crit", f"🚨 {iss['message']}"))
            elif sev == "warning":
                chips.append(("", f"⚠️ {iss['message']}"))
    chips = chips[:limit]
    if not chips:
        return f'<span class="focus-chip win">✅ No critical issues — Scout is happy!</span>'
    return "".join(f'<span class="focus-chip {cls}">{txt}</span>' for cls, txt in chips)


def scout_line(score: int, audit: dict) -> str:
    """A short, character-driven status line based on the live audit."""
    worst = min(_CAT_META, key=lambda c: audit.get(c[0], {}).get("score", 100))
    worst_name = worst[1]
    if score >= 85:
        return (f"Looking sharp! Your site is scoring <b>{score}/100</b> — top-tier territory. "
                f"I'm keeping an eye on <b>{worst_name}</b> for any slip-ups.")
    if score >= 70:
        return (f"Solid health at <b>{score}/100</b>. A little love for <b>{worst_name}</b> "
                f"would push you into the excellent zone.")
    if score >= 50:
        return (f"We're at <b>{score}/100</b> — workable, but <b>{worst_name}</b> needs attention. "
                f"Let's tackle the red zone first.")
    return (f"Heads up — <b>{score}/100</b>. <b>{worst_name}</b> is in critical shape. "
            f"I've flagged the urgent fixes below so we can turn this around fast.")
