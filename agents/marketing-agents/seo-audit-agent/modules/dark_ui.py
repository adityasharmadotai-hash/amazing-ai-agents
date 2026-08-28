"""
dark_ui.py — Renders the dark, animated page bodies for the SEO agent.

Each render_* function returns a complete standalone HTML document (inline CSS +
SVG + a little JS) meant for st.components.v1.html(). Rendering inside an iframe
sidesteps Streamlit's markdown sanitiser entirely, so the full neon look and all
animations come through exactly as designed. Navigation, buttons and the location
toggle live in the Streamlit sidebar; these bodies are display-only and built from
real audit / projection / ranking data.
"""

from __future__ import annotations

import math

# ── palette ───────────────────────────────────────────────────────────────────
GREEN = "#34d399"; CYAN = "#22d3ee"; LIME = "#a3e635"
AMBER = "#fbbf24"; RED = "#fb7185"; VIOLET = "#a78bfa"; BLUE = "#93c5fd"

_CSS = """
:root{--bg:#05060d;--bg2:#090b16;--panel:#0e1120;--panel2:#121524;
 --line:rgba(140,120,255,.16);--line2:rgba(140,120,255,.3);--ink:#eef0ff;--mut:#8a90bf;--dim:#5a5f85;}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Inter',system-ui,sans-serif;color:var(--ink);
 background:radial-gradient(900px 460px at 88% -8%,rgba(124,58,237,.16),transparent 60%),
 radial-gradient(700px 460px at -5% 8%,rgba(34,211,238,.09),transparent 55%),var(--bg);overflow-x:hidden;}
.num{font-family:'Space Grotesk','Inter',sans-serif;}
.wrap{position:relative;z-index:1;padding:6px 4px 30px;}
.card{background:linear-gradient(180deg,var(--panel),var(--bg2));border:1px solid var(--line);
 border-radius:20px;box-shadow:0 16px 50px rgba(0,0,0,.5);}
.h{font-size:11px;font-weight:800;letter-spacing:.13em;color:var(--mut);text-transform:uppercase;}
.glow{filter:drop-shadow(0 0 8px currentColor);}
.sec{font-family:'Space Grotesk';font-weight:700;font-size:15px;margin:22px 0 12px;display:flex;align-items:center;gap:8px;color:#fff;}
.sub{color:var(--mut);font-size:13px;}
.float{animation:fl 4s ease-in-out infinite;}@keyframes fl{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}
.blink{transform-origin:center;animation:bl 4.5s infinite;}@keyframes bl{0%,92%,100%{transform:scaleY(1)}96%{transform:scaleY(.1)}}
.spin{animation:sp 1.4s cubic-bezier(.2,1,.3,1) forwards;}@keyframes sp{from{stroke-dashoffset:var(--c)}to{stroke-dashoffset:var(--t)}}
.draw{stroke-dashoffset:var(--len);animation:dr 1.3s ease forwards;}@keyframes dr{to{stroke-dashoffset:var(--off)}}
.hero{display:grid;grid-template-columns:300px 1fr;gap:18px;margin:6px 0;}
.L{padding:22px;display:flex;flex-direction:column;align-items:center;gap:6px;position:relative;overflow:hidden;}
.sonar{position:absolute;top:50px;width:150px;height:150px;border:2px solid var(--violet);border-radius:50%;opacity:0;animation:so 3s ease-out infinite;}
.sonar.b{animation-delay:1.5s;}@keyframes so{0%{transform:scale(.5);opacity:.6}100%{transform:scale(1.7);opacity:0}}
.R{display:flex;flex-direction:column;gap:14px;}
.bubble{background:linear-gradient(100deg,rgba(99,102,241,.16),rgba(167,139,250,.07));border:1px solid var(--line2);border-radius:16px;padding:15px 18px;}
.bubble .who{font-size:11px;font-weight:800;color:var(--violet);letter-spacing:.06em;text-transform:uppercase;margin-bottom:5px;}
.bubble .say{font-size:14.5px;line-height:1.6;color:#e3e5fb;}.bubble b{color:#fff;}
.ekg{background:#02030a;border:1px solid var(--line);border-radius:14px;height:74px;overflow:hidden;}
.ekg path{stroke-dasharray:700 380;animation:da 3s linear infinite;}@keyframes da{to{stroke-dashoffset:-1080}}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.tile{padding:15px;border-radius:16px;text-align:center;position:relative;overflow:hidden;background:linear-gradient(180deg,var(--panel2),var(--bg2));border:1px solid var(--line);}
.tile .v{font-family:'Space Grotesk';font-size:30px;font-weight:700;}
.tile .l{font-size:10px;color:var(--mut);font-weight:700;letter-spacing:.06em;text-transform:uppercase;margin-top:4px;}
.tile .gb{position:absolute;left:0;right:0;bottom:0;height:3px;}
.vitals{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;}
.vital{padding:15px 8px 13px;text-align:center;border-radius:18px;background:linear-gradient(180deg,var(--panel),var(--bg2));border:1px solid var(--line);transition:.18s;}
.vital:hover{transform:translateY(-4px);border-color:var(--line2);}
.vital .ic{font-size:17px;}.vital .nm{font-size:11px;color:var(--mut);font-weight:600;margin-top:5px;}.vital .mn{font-family:'Space Grotesk';font-weight:700;font-size:19px;}
/* rankings */
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:6px 0;}
.kpi{padding:16px;border-radius:16px;background:linear-gradient(180deg,var(--panel2),var(--bg2));border:1px solid var(--line);border-top:3px solid var(--c);}
.kpi .v{font-family:'Space Grotesk';font-weight:700;font-size:28px;color:var(--c);}.kpi .l{font-size:11px;color:var(--mut);font-weight:600;margin-top:2px;}
.rktbl{width:100%;border-collapse:separate;border-spacing:0 8px;}
.rktbl th{text-align:left;font-size:10.5px;color:var(--dim);letter-spacing:.08em;text-transform:uppercase;font-weight:700;padding:0 14px 4px;}
.rktbl td{background:linear-gradient(180deg,var(--panel2),var(--bg2));border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:13px 14px;vertical-align:middle;}
.rktbl tr td:first-child{border-left:1px solid var(--line);border-radius:13px 0 0 13px;}
.rktbl tr td:last-child{border-right:1px solid var(--line);border-radius:0 13px 13px 0;}
.rktbl tr:hover td{background:var(--panel);}
.kw{font-weight:700;font-size:14px;}.kwp{font-size:11.5px;color:var(--cyan);font-family:'Space Grotesk';}
.rank{display:inline-flex;align-items:center;gap:8px;}.pos{font-family:'Space Grotesk';font-weight:700;font-size:16px;min-width:34px;}
.badge{font-size:9.5px;font-weight:800;text-transform:uppercase;letter-spacing:.04em;padding:3px 8px;border-radius:20px;}
.b10{background:rgba(52,211,153,.16);color:#6ee7b7;border:1px solid rgba(52,211,153,.4);}
.b20{background:rgba(251,191,36,.16);color:#fcd34d;border:1px solid rgba(251,191,36,.4);}
.b100{background:rgba(96,165,250,.14);color:#93c5fd;border:1px solid rgba(96,165,250,.35);}
.bno{background:rgba(251,113,133,.14);color:#fda4af;border:1px solid rgba(251,113,133,.35);}
.tr-up{color:#34d399;font-weight:700;font-size:12px;}.tr-dn{color:#fb7185;font-weight:700;font-size:12px;}
/* pages */
.pagecard{background:linear-gradient(180deg,var(--panel2),var(--bg2));border:1px solid var(--line);border-radius:16px;padding:16px 18px;margin-bottom:12px;transition:.15s;}
.pagecard:hover{border-color:var(--line2);transform:translateX(3px);}
.pagecard .ph{display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap;}
.pagecard .url{font-family:'Space Grotesk';font-weight:600;font-size:14px;color:#fff;}
.pagecard .meta{margin-left:auto;font-size:11px;color:var(--mut);}
.kwrow{display:flex;flex-wrap:wrap;gap:8px;}
.kwchip{display:inline-flex;align-items:center;gap:7px;background:#04050d;border:1px solid var(--line);border-radius:30px;padding:5px 11px;font-size:12px;}
.kwchip .p{font-family:'Space Grotesk';font-weight:700;font-size:11px;padding:1px 7px;border-radius:20px;}
/* category */
.banner{border-radius:22px;padding:24px 26px;position:relative;overflow:hidden;margin:6px 0 16px;display:flex;align-items:center;gap:26px;border:1px solid var(--line2);flex-wrap:wrap;}
.banner .nm{font-family:'Space Grotesk';font-weight:700;font-size:28px;display:flex;align-items:center;gap:10px;}
.banner .desc{font-size:13px;color:#c9cdf2;max-width:520px;line-height:1.5;margin-top:5px;}
.banner .crumb{font-size:12px;color:var(--mut);font-weight:600;}
.beforeafter{display:flex;align-items:center;gap:14px;margin-left:auto;}
.ba-g{text-align:center;}.ba-g .cap{font-size:10px;color:var(--mut);font-weight:700;letter-spacing:.06em;margin-top:4px;text-transform:uppercase;}
.arrow{font-size:24px;color:var(--green);animation:nudge 1.4s ease-in-out infinite;}@keyframes nudge{0%,100%{transform:translateX(0)}50%{transform:translateX(5px)}}
.uplift{display:inline-flex;align-items:center;gap:6px;background:rgba(52,211,153,.14);border:1px solid rgba(52,211,153,.45);color:#6ee7b7;font-weight:800;font-size:13px;padding:5px 12px;border-radius:30px;font-family:'Space Grotesk';}
.fixes{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.fix{background:linear-gradient(180deg,var(--panel2),var(--bg2));border:1px solid var(--line);border-radius:16px;padding:16px 18px;border-left:4px solid var(--sev);transition:.16s;}
.fix:hover{transform:translateY(-3px);border-color:var(--line2);}
.fix .top{display:flex;align-items:center;gap:8px;margin-bottom:8px;}
.fix .sev{font-size:9.5px;font-weight:800;text-transform:uppercase;padding:3px 8px;border-radius:20px;color:#05060d;background:var(--sev);}
.fix .pts{margin-left:auto;font-family:'Space Grotesk';font-weight:700;font-size:15px;color:#6ee7b7;background:rgba(52,211,153,.12);border:1px solid rgba(52,211,153,.35);border-radius:20px;padding:3px 11px;}
.fix .ti{font-size:14px;font-weight:700;}.fix .why{font-size:12.5px;color:var(--mut);margin:7px 0 9px;line-height:1.5;}
.fix .how{font-size:12.5px;color:#cfd3f5;background:#04050d;border:1px solid var(--line);border-radius:10px;padding:9px 12px;line-height:1.5;}.fix .how b{color:var(--cyan);}
.fix .foot{display:flex;gap:8px;margin-top:10px;}
.tag{font-size:10.5px;font-weight:700;padding:3px 9px;border-radius:20px;background:rgba(255,255,255,.05);color:var(--mut);border:1px solid var(--line);}
/* roadmap */
.bigba{display:grid;grid-template-columns:1fr auto 1fr;gap:24px;align-items:center;margin:6px 0;}
.bigba .card{padding:24px;text-align:center;}
.stack{margin:9px 0;}.stack .t{display:flex;justify-content:space-between;font-size:12.5px;font-weight:600;margin-bottom:5px;color:#dfe2f4;}
.stack .trk{height:14px;background:rgba(255,255,255,.05);border-radius:8px;position:relative;overflow:hidden;}
.stack .cur{position:absolute;left:0;top:0;bottom:0;border-radius:8px;}
.stack .ext{position:absolute;top:0;bottom:0;background:repeating-linear-gradient(45deg,rgba(52,211,153,.6),rgba(52,211,153,.6) 5px,transparent 5px,transparent 10px);}
.plan{display:flex;flex-direction:column;gap:10px;}
.prow{display:flex;align-items:center;gap:14px;background:linear-gradient(180deg,var(--panel2),var(--bg2));border:1px solid var(--line);border-radius:14px;padding:13px 16px;transition:.15s;}
.prow:hover{transform:translateX(4px);border-color:var(--line2);}
.prow .rk{font-family:'Space Grotesk';font-weight:700;font-size:18px;color:var(--violet);width:26px;}
.prow .nm{font-weight:700;font-size:13.5px;}.prow .ds{font-size:11.5px;color:var(--mut);}
.prow .pts{margin-left:auto;font-family:'Space Grotesk';font-weight:700;color:#6ee7b7;font-size:16px;}
.empty{background:linear-gradient(180deg,var(--panel2),var(--bg2));border:1px solid var(--line);border-radius:16px;padding:26px;text-align:center;color:var(--mut);}
/* keyword ideas */
.sgcard{background:linear-gradient(180deg,var(--panel2),var(--bg2));border:1px solid var(--line);border-radius:16px;
  padding:16px 18px;margin-bottom:12px;transition:.15s;}
.sgcard:hover{border-color:var(--line2);transform:translateY(-2px);box-shadow:0 14px 30px rgba(0,0,0,.45);}
.sghead{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:10px;}
.sgkw{font-family:'Space Grotesk';font-weight:700;font-size:16px;color:#fff;}
.sgintent{font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#a78bfa;
  background:rgba(167,139,250,.12);border:1px solid rgba(167,139,250,.3);padding:2px 9px;border-radius:20px;}
.diff{font-size:9.5px;font-weight:800;text-transform:uppercase;letter-spacing:.04em;padding:3px 9px;border-radius:20px;}
.dEasy{background:rgba(52,211,153,.16);color:#6ee7b7;border:1px solid rgba(52,211,153,.4);}
.dMedium{background:rgba(251,191,36,.16);color:#fcd34d;border:1px solid rgba(251,191,36,.4);}
.dHard{background:rgba(251,113,133,.16);color:#fda4af;border:1px solid rgba(251,113,133,.4);}
.sgrow{display:flex;gap:10px;padding:7px 0;border-top:1px solid rgba(140,120,255,.08);font-size:12.5px;line-height:1.5;}
.sglbl{flex-shrink:0;width:120px;color:var(--mut);font-weight:700;}
.sgval{color:#d5d8f5;}
.sgval b{color:var(--cyan);}
.cta{display:inline-block;background:linear-gradient(100deg,#6366f1,#a78bfa);color:#fff;border-radius:11px;padding:10px 18px;font-weight:700;font-size:13px;text-decoration:none;}
.pt{position:fixed;inset:0;pointer-events:none;z-index:0;}
.pt i{position:absolute;width:3px;height:3px;border-radius:50%;animation:ri linear infinite;}
@keyframes ri{0%{transform:translateY(100vh);opacity:0}10%,90%{opacity:.55}100%{transform:translateY(-6vh);opacity:0}}
"""

_HEAD = ("<link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900"
         "&family=Space+Grotesk:wght@500;600;700&display=swap' rel='stylesheet'>")

_PARTICLES_JS = """<script>
var pt=document.createElement('div');pt.className='pt';document.body.appendChild(pt);
for(var i=0;i<20;i++){var s=document.createElement('i');s.style.left=(Math.random()*100)+'%';
 s.style.animationDuration=(8+Math.random()*9)+'s';s.style.animationDelay=(-Math.random()*14)+'s';
 var c=['#a78bfa','#22d3ee','#f472b6'][i%3];s.style.background=c;s.style.boxShadow='0 0 6px '+c;s.style.opacity=.4;pt.appendChild(s);}
</script>"""


def _doc(body: str) -> str:
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'>{_HEAD}<style>{_CSS}</style></head><body><div class='wrap'>{body}</div>{_PARTICLES_JS}</body></html>"


def health_color(s: int) -> str:
    return CYAN if s >= 85 else GREEN if s >= 70 else AMBER if s >= 50 else RED


# ── primitives ────────────────────────────────────────────────────────────────
def _ring(score, color, size=120, r=44, sw=10):
    c = 2 * math.pi * r
    off = c * (1 - score / 100)
    return (f"<svg width='{size}' height='{size}' viewBox='0 0 120 120'>"
            f"<circle cx='60' cy='60' r='{r}' fill='none' stroke='rgba(255,255,255,.07)' stroke-width='{sw}'/>"
            f"<circle class='draw' cx='60' cy='60' r='{r}' fill='none' stroke='{color}' stroke-width='{sw}' "
            f"stroke-linecap='round' transform='rotate(-90 60 60)' "
            f"style='--len:{c:.0f};--off:{off:.0f};filter:drop-shadow(0 0 7px {color})'/>"
            f"<text x='60' y='68' text-anchor='middle' class='num' font-size='30' font-weight='700' fill='#fff'>{score}</text></svg>")


def _gauge(score, size=180):
    color = health_color(score)
    word = "THRIVING" if score >= 85 else "HEALTHY" if score >= 70 else "NEEDS WORK" if score >= 50 else "AT RISK"
    r = 82; c = 2 * math.pi * r; off = c * (1 - score / 100)
    return (f"<svg width='{size}' height='{size}' viewBox='0 0 200 200'>"
            f"<defs><linearGradient id='gg' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#22d3ee'/><stop offset='1' stop-color='{color}'/></linearGradient></defs>"
            f"<circle cx='100' cy='100' r='{r}' fill='none' stroke='rgba(255,255,255,.06)' stroke-width='13'/>"
            f"<circle class='spin' cx='100' cy='100' r='{r}' fill='none' stroke='url(#gg)' stroke-width='13' stroke-linecap='round' "
            f"transform='rotate(-90 100 100)' stroke-dasharray='{c:.0f}' style='--c:{c:.0f};--t:{off:.0f};stroke-dashoffset:{off:.0f};filter:drop-shadow(0 0 12px {color})'/>"
            f"<text x='100' y='96' text-anchor='middle' class='num' font-size='54' font-weight='700' fill='#fff'>{score}</text>"
            f"<text x='100' y='120' text-anchor='middle' font-size='11' fill='{color}' font-weight='800' letter-spacing='2'>{word}</text></svg>")


def _scout(size=150):
    return (f"<svg class='float' width='{size}' height='{size}' viewBox='0 0 120 130' style='filter:drop-shadow(0 14px 26px rgba(124,58,237,.55))'>"
            "<defs><linearGradient id='bd' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#6366f1'/><stop offset='1' stop-color='#7c3aed'/></linearGradient>"
            "<radialGradient id='hl' cx='50%' cy='45%' r='55%'><stop offset='0' stop-color='#a78bfa' stop-opacity='.5'/><stop offset='1' stop-color='#a78bfa' stop-opacity='0'/></radialGradient></defs>"
            "<ellipse cx='60' cy='60' rx='56' ry='56' fill='url(#hl)'/>"
            "<line x1='60' y1='18' x2='60' y2='6' stroke='#a78bfa' stroke-width='3'/><circle cx='60' cy='5' r='4.5' fill='#22d3ee' class='glow'/>"
            "<rect x='22' y='20' width='76' height='68' rx='22' fill='url(#bd)'/><rect x='32' y='32' width='56' height='44' rx='14' fill='#04050d'/>"
            "<g class='blink'><circle cx='48' cy='52' r='7' fill='#22d3ee' class='glow'/></g><g class='blink'><circle cx='72' cy='52' r='7' fill='#22d3ee' class='glow'/></g>"
            "<path d='M44 70 Q60 86 76 70' stroke='#22d3ee' stroke-width='3' fill='none'/>"
            "<circle cx='20' cy='54' r='5' fill='#7c3aed'/><circle cx='100' cy='54' r='5' fill='#7c3aed'/>"
            "<g transform='translate(78,78) rotate(20)'><circle cx='10' cy='10' r='11' fill='none' stroke='#fbbf24' stroke-width='4'/><line x1='18' y1='18' x2='30' y2='30' stroke='#fbbf24' stroke-width='5'/></g></svg>")


def _ekg(color=GREEN):
    path = ("M0 38 L70 38 L82 12 L94 62 L106 38 L180 38 L192 12 L204 62 L216 38 L300 38 L312 12 L324 62 "
            "L336 38 L420 38 L432 12 L444 62 L456 38 L540 38 L552 12 L564 62 L576 38 L1000 38")
    return (f"<div class='ekg'><svg viewBox='0 0 600 74' width='100%' height='74' preserveAspectRatio='none'>"
            f"<path d='{path}' fill='none' stroke='{color}' stroke-width='2.5' style='filter:drop-shadow(0 0 6px {color})'/></svg></div>")


def _pos_badge(p):
    if not p:
        return "<span class='rank'><span class='pos' style='color:#fb7185'>—</span><span class='badge bno'>Not in top 100</span></span>"
    cls, lab, col = ("b10", "Top 10", GREEN) if p <= 10 else ("b20", "Top 20", AMBER) if p <= 20 else ("b100", "Top 100", BLUE)
    return f"<span class='rank'><span class='pos' style='color:{col}'>#{p}</span><span class='badge {cls}'>{lab}</span></span>"


def _trend_chart(points, w=1160, h=190):
    if len(points) < 2:
        note = "Scout will plot your score here as scans accumulate — check back after a few refreshes."
        return f"<div class='empty'>📈 Building your trend… {note}</div>"
    lo, hi = min(points), max(points)
    span = max(1, hi - lo)
    n = len(points)
    pad = 28
    xs = [i * (w / (n - 1)) for i in range(n)]
    ys = [pad + (h - 2 * pad) * (1 - (p - lo) / span) for p in points]
    line = " ".join(f"{'M' if i == 0 else 'L'}{xs[i]:.0f} {ys[i]:.0f}" for i in range(n))
    fill = line + f" L{w} {h} L0 {h} Z"
    return (f"<div class='card' style='padding:20px'><svg viewBox='0 0 {w} {h}' width='100%' height='{h}'>"
            "<defs><linearGradient id='af' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#7c3aed' stop-opacity='.5'/><stop offset='1' stop-color='#7c3aed' stop-opacity='0'/></linearGradient>"
            "<linearGradient id='as' x1='0' y1='0' x2='1' y2='0'><stop offset='0' stop-color='#22d3ee'/><stop offset='1' stop-color='#a78bfa'/></linearGradient></defs>"
            f"<path d='{fill}' fill='url(#af)'/><path d='{line}' fill='none' stroke='url(#as)' stroke-width='3' stroke-linecap='round' style='filter:drop-shadow(0 0 6px #a78bfa)'/>"
            f"<circle cx='{xs[-1]:.0f}' cy='{ys[-1]:.0f}' r='5' fill='#22d3ee' class='glow'/></svg></div>")


# ── pages ─────────────────────────────────────────────────────────────────────
_VIT_KEYS = [("meta", "Meta", "🏷️"), ("headings", "Headings", "📝"), ("keywords", "Keywords", "🔑"),
             ("technical", "Technical", "⚙️"), ("images", "Images", "🖼️"), ("links", "Links", "🔗")]


def render_overview(audit, counts, load_time, scout_msg, trend_points, last_scan):
    score = audit["overall_score"]
    vit = "".join(
        f"<div class='vital'>{_ring(audit[k]['score'], health_color(audit[k]['score']), 74, 26, 7)}"
        f"<div class='ic'>{ic}</div><div class='nm'>{nm}</div></div>"
        for k, nm, ic in _VIT_KEYS)
    tiles = "".join(
        f"<div class='tile'><div class='v' style='color:{col}'>{v}</div><div class='l'>{l}</div>"
        f"<div class='gb' style='background:{col};box-shadow:0 0 10px {col}'></div></div>"
        for v, l, col in [(counts["critical"], "Critical", RED), (counts["warning"], "Warnings", AMBER),
                          (counts["pass"], "Passing", GREEN), (f"{load_time}s", "Load", CYAN)])
    body = f"""
    <div class='hero'>
      <div class='L card'><div class='sonar'></div><div class='sonar b'></div>{_scout(150)}{_gauge(score,180)}</div>
      <div class='R'>
        <div class='bubble'><div class='who'>◇ Scout · SEO Agent</div><div class='say'>{scout_msg}</div></div>
        <div><div class='h' style='margin-bottom:6px'>⌁ HEARTBEAT · last scan {last_scan}</div>{_ekg(health_color(score))}</div>
        <div class='tiles'>{tiles}</div>
      </div>
    </div>
    <div class='sec'>🩺 Category Vitals <span class='sub' style='font-weight:500'>— open a page on the left to see its fixes</span></div>
    <div class='vitals'>{vit}</div>
    <div class='sec'>📈 Score trend</div>
    {_trend_chart(trend_points)}
    """
    return _doc(body)


def render_category(cat_key, cat_name, icon, desc, current, projected, fixes):
    up = projected - current
    if fixes:
        cards = "".join(
            f"<div class='fix' style='--sev:{RED if f['severity']=='critical' else AMBER}'>"
            f"<div class='top'><span class='sev'>{f['severity'].title()}</span><span class='ti'>{f.get('title') or f['message']}</span>"
            f"<span class='pts'>+{f['cat_points']}</span></div>"
            f"<div class='why'>{f.get('summary') or f['message']}</div>"
            f"<div class='how'>🔧 {f['fix'] or 'Apply the recommended fix.'}</div>"
            f"<div class='foot'><span class='tag'>{f['difficulty']}</span>{('<span class=tag>'+f['time']+'</span>') if f['time'] else ''}"
            f"<span class='tag' style='margin-left:auto;color:#6ee7b7'>+{f['overall_points']} overall</span></div></div>"
            for f in fixes)
        ba = (f"<div style='text-align:center'><div class='arrow'>➜</div><div class='uplift'>+{up}</div></div>"
              f"<div class='ba-g'>{_ring(projected, GREEN)}<div class='cap' style='color:#6ee7b7'>After</div></div>")
        sec = "🔧 Improvement areas — exact fixes for this page"
    else:
        cards = ("<div class='fix' style='--sev:#34d399;grid-column:1/-1'><div class='top'>"
                 "<span class='sev' style='background:#34d399'>Perfect</span><span class='ti'>No issues found 🎉</span></div>"
                 "<div class='why'>This area is fully optimised — Scout will alert you if anything regresses.</div></div>")
        ba = ""
        sec = "✅ Status"
    body = f"""
    <div class='banner' style='background:linear-gradient(110deg,#6366f133,transparent)'>
      <div><div class='crumb'>Page-by-page health ›</div><div class='nm'>{icon} {cat_name}</div><div class='desc'>{desc}</div></div>
      <div class='beforeafter'><div class='ba-g'>{_ring(current, health_color(current))}<div class='cap'>Now</div></div>{ba}</div>
    </div>
    <div class='sec'>{sec}</div>
    <div class='fixes'>{cards}</div>
    """
    return _doc(body)


def render_rankings(rows, summary, updated, has_key, locations=None, site="your site"):
    locations = locations or [("us", "🇺🇸", "US")]
    loc_names = " &amp; ".join(f"{flag} {label}" for _, flag, label in locations)
    if not has_key:
        body = ("<div class='banner' style='background:linear-gradient(110deg,#6366f133,transparent)'>"
                "<div><div class='crumb'>Search rankings ›</div><div class='nm'>🔑 Keyword Rankings</div>"
                f"<div class='desc'>Connect SerpAPI to track where <b>{site}</b> ranks in Google {loc_names} for your "
                "target keywords. Add <b style='color:#22d3ee'>SERPAPI_KEY</b> in Settings, then hit “Refresh”.</div></div></div>"
                "<div class='empty'>🔌 No SerpAPI key detected — showing your keyword list below. "
                "Real positions appear once a key is connected and you refresh.</div>")
        return _doc(body)
    kpi = "".join(
        f"<div class='kpi' style='--c:{col}'><div class='v'>{summary[k]}</div><div class='l'>{l}</div></div>"
        for k, l, col in [("top10", "Top 10", GREEN), ("top20", "Top 11–20", AMBER),
                          ("top100", "Top 21–100", BLUE), ("none", "Not ranking", RED)])
    loc_head = "".join(f"<th>{flag} {label}</th>" for _, flag, label in locations)
    trows = ""
    for r in rows:
        best = r["best"]
        best_txt = f"#{best}" if best else "—"
        loc_cells = "".join(f"<td>{_pos_badge(r['pos'].get(lk))}</td>" for lk, _, _ in locations)
        trows += (f"<tr><td><div class='kw'>{r['keyword']}</div></td>"
                  f"<td><span class='kwp'>{r['page']}</span></td>"
                  f"{loc_cells}<td><span class='pos'>{best_txt}</span></td></tr>")
    body = f"""
    <div class='kpis'>{kpi}</div>
    <div class='card' style='padding:8px 14px 14px;margin-top:14px;overflow-x:auto'>
      <table class='rktbl'><thead><tr><th>Keyword</th><th>Ranking page</th>{loc_head}<th>Best</th></tr></thead>
      <tbody>{trows}</tbody></table>
    </div>
    <div class='sub' style='margin-top:10px'>Last updated: {updated}</div>
    """
    return _doc(body)


def render_pages(by_page, page_names, locations=None, site="your site"):
    locations = locations or [("us", "🇺🇸", "US")]
    if not by_page:
        return _doc("<div class='empty'>No ranking pages yet — connect SerpAPI and refresh to populate this view.</div>")
    cards = ""
    for path, kws in by_page.items():
        best = min([p for k in kws for p in k["pos"].values() if p], default=None)
        tag = ("<span class='badge b10'>Top 10</span>" if best and best <= 10 else
               "<span class='badge b20'>Top 20</span>" if best and best <= 20 else
               "<span class='badge b100'>Top 100</span>" if best else "<span class='badge bno'>Not ranking</span>")
        chips = ""
        for k in kws:
            b = k["best"]
            col = GREEN if b and b <= 10 else AMBER if b and b <= 20 else BLUE if b else RED
            locpills = "".join(
                f"<span class='p' style='background:{col}22;color:{col}'>{flag} {('#'+str(k['pos'][lk])) if k['pos'].get(lk) else '—'}</span>"
                for lk, flag, _ in locations)
            chips += (f"<span class='kwchip'><b>{k['keyword']}</b>{locpills}</span>")
        url = site.replace("https://", "").replace("http://", "").rstrip("/") + ("" if path == "/" else path)
        nm = page_names.get(path, "")
        cards += (f"<div class='pagecard'><div class='ph'><span style='font-size:16px'>📄</span>"
                  f"<span class='url'>{url}</span> {tag}<span class='meta'>{len(kws)} keyword{'s' if len(kws)>1 else ''}{' · '+nm if nm else ''}</span></div>"
                  f"<div class='kwrow'>{chips}</div></div>")
    return _doc(cards)


def render_roadmap(proj, items):
    cur, prj, delta = proj["overall_current"], proj["overall_projected"], proj["overall_delta"]
    stacks = ""
    for k, nm, ic in _VIT_KEYS:
        d = proj["categories"][k]
        c, p = d["current"], d["projected"]
        col = health_color(c)
        ext = (f"<div class='ext' style='left:{c}%;width:{p-c}%'></div>") if p > c else ""
        proj_txt = f" <span style='color:#34d399'>→ {p}</span>" if p > c else ""
        stacks += (f"<div class='stack'><div class='t'><span>{ic} {nm}</span><span><b style='color:{col}'>{c}</b>{proj_txt}</span></div>"
                   f"<div class='trk'><div class='cur' style='width:{c}%;background:linear-gradient(90deg,{col}aa,{col})'></div>{ext}</div></div>")
    rows = ""
    for i, it in enumerate(items[:8], 1):
        eff_col = GREEN if it["difficulty"] == "Easy" else AMBER if it["difficulty"] == "Medium" else RED
        eff = f"{it['difficulty']}" + (f" · {it['time']}" if it["time"] else "")
        rows += (f"<div class='prow'><span class='rk'>{i}</span><span style='font-size:18px'>{it['icon']}</span>"
                 f"<div><div class='nm'>{it['fix'] or it['message']}</div><div class='ds'>{it['cat_name']} · {it['message']}</div></div>"
                 f"<span class='tag' style='color:{eff_col}'>{eff}</span><span class='pts'>+{it['overall_points']}</span></div>")
    if not items:
        rows = "<div class='empty'>🎉 No actionable issues — your site is in great shape!</div>"
    aft = (f"<div style='text-align:center'><div class='arrow' style='font-size:40px'>➜</div>"
           f"<div class='uplift' style='margin-top:8px'>▲ +{delta} pts</div></div>"
           f"<div class='card' style='border-color:rgba(52,211,153,.4)'><div class='h' style='color:#6ee7b7'>AFTER FIXES</div>"
           f"{_gauge(prj,150)}<div class='h' style='margin-top:6px;color:#6ee7b7'>Projected</div></div>") if delta > 0 else \
          "<div></div><div class='card'><div class='h'>Already optimised 🎉</div></div>"
    body = f"""
    <div class='bigba'>
      <div class='card'><div class='h'>TODAY</div>{_gauge(cur,150)}<div class='h' style='margin-top:6px;color:#a78bfa'>Current</div></div>
      {aft}
    </div>
    <div class='sec'>📊 Current vs projected — by category</div>
    <div class='card' style='padding:20px'>{stacks}
      <div class='sub' style='margin-top:12px'><span style='display:inline-block;width:12px;height:8px;background:#6366f1;border-radius:2px'></span> current &nbsp;
      <span style='display:inline-block;width:12px;height:8px;background:repeating-linear-gradient(45deg,#34d399,#34d399 3px,transparent 3px,transparent 6px);border-radius:2px'></span> projected gain</div>
    </div>
    <div class='sec'>🎯 Do these first — ranked by impact</div>
    <div class='plan'>{rows}</div>
    """
    return _doc(body)


def render_suggestions(items, counts, updated, has_key):
    if not has_key:
        body = ("<div class='banner' style='background:linear-gradient(110deg,#6366f133,transparent)'>"
                "<div><div class='crumb'>Search rankings ›</div><div class='nm'>💡 Keyword Ideas</div>"
                "<div class='desc'>Connect SerpAPI (in Settings) and Scout will mine Google’s “People Also Ask” and "
                "related searches for winnable long-tail keywords — each with a plan for how to rank.</div></div></div>")
        return _doc(body)
    if not items:
        return _doc("<div class='empty'>💡 No ideas yet — hit <b>Generate ideas</b> to mine winnable long-tail keywords.</div>")
    kpi = "".join(
        f"<div class='kpi' style='--c:{col}'><div class='v'>{counts.get(k,0)}</div><div class='l'>{k} to win</div></div>"
        for k, col in [("Easy", GREEN), ("Medium", AMBER), ("Hard", RED)])
    cards = ""
    for it in items:
        d = it["difficulty"]
        cards += (
            f"<div class='sgcard'>"
            f"<div class='sghead'><span class='sgkw'>{it['keyword']}</span>"
            f"<span class='diff d{d}'>{d} to win</span>"
            f"<span class='sgintent'>{it['intent']}</span></div>"
            f"<div class='sgrow'><span class='sglbl'>🎯 Target page</span><span class='sgval'>{it['page']}</span></div>"
            f"<div class='sgrow'><span class='sglbl'>✍️ Add content</span><span class='sgval'>{it['content']}</span></div>"
            f"<div class='sgrow'><span class='sglbl'>🏷️ Title tag</span><span class='sgval'><b>{it['title']}</b></span></div>"
            f"<div class='sgrow'><span class='sglbl'>🧩 Schema</span><span class='sgval'>{it['schema']}</span></div>"
            f"</div>")
    body = f"""
    <div class='kpis' style='grid-template-columns:repeat(3,1fr)'>{kpi}</div>
    <div class='sec'>💡 Winnable keywords — mined from Google, with a plan to rank</div>
    {cards}
    <div class='sub' style='margin-top:6px'>Discovered {updated}. “Easy to win” = long-tail / People-Also-Ask questions you can target with one focused page.</div>
    """
    return _doc(body)


def render_competitors(comps, has_key, updated, summary=None):
    if not has_key:
        body = ("<div class='banner' style='background:linear-gradient(110deg,#6366f133,transparent)'>"
                "<div><div class='crumb'>Search rankings ›</div><div class='nm'>🏆 Competitors</div>"
                "<div class='desc'>Connect SerpAPI (in Settings) and refresh <b>Keyword Rankings</b> — Scout will "
                "surface every company ranking in Google’s top 10 for your staffing keywords, and which keywords each wins.</div></div></div>")
        return _doc(body)
    if not comps:
        return _doc("<div class='empty'>🏆 No competitor data yet — go to <b>Keyword Rankings</b> and hit "
                    "<b>🔄 Refresh</b>. Competitors are built from the same search, so one refresh fills this in.</div>")
    summary = summary or {}
    kpi = "".join(
        f"<div class='kpi' style='--c:{col}'><div class='v'>{summary.get(k,0)}</div><div class='l'>{l}</div></div>"
        for k, l, col in [("total", "Competitors found", VIOLET),
                          ("strong", "Rank for 3+ of your keywords", GREEN),
                          ("keywords_covered", "Keywords contested", AMBER)])
    cards = ""
    for i, c in enumerate(comps, 1):
        best = c["best"]
        bcol = GREEN if best <= 10 else AMBER if best <= 20 else BLUE
        chips = ""
        for k in c["keywords"]:
            p = k["position"]
            col = GREEN if p <= 3 else LIME if p <= 10 else AMBER if p <= 20 else BLUE
            chips += (f"<span class='kwchip'><b>{k['keyword']}</b>"
                      f"<span class='p' style='background:{col}22;color:{col}'>#{p}</span></span>")
        cards += (
            f"<div class='pagecard'><div class='ph'>"
            f"<span style='font-family:Space Grotesk;font-weight:700;color:{VIOLET};width:26px'>{i}</span>"
            f"<span style='font-size:16px'>🏢</span>"
            f"<span class='url'>{c['domain']}</span>"
            f"<span class='badge {'b10' if best<=10 else 'b20' if best<=20 else 'b100'}'>Best #{best}</span>"
            f"<span class='meta'>ranks for {c['appearances']} of your keyword{'s' if c['appearances']>1 else ''}"
            f"{' · '+str(c['top10'])+' in top 10' if c['top10'] else ''}</span></div>"
            f"<div class='kwrow'>{chips}</div></div>")
    body = f"""
    <div class='kpis' style='grid-template-columns:repeat(3,1fr)'>{kpi}</div>
    <div class='sec'>🏆 Who's winning your keywords — ranked by how many they contest</div>
    {cards}
    <div class='sub' style='margin-top:6px'>From the top-10 Google results for your {summary.get('keywords_covered','')} contested keywords · {updated}. Job boards &amp; info sites are filtered out.</div>
    """
    return _doc(body)
