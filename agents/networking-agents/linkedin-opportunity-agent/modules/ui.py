"""
ui.py — Shared UI helpers: global styles, KPI cards, badges, opportunity cards.

Dark-mode-friendly, LinkedIn-blue accented design. All helpers render directly
into the current Streamlit container.
"""

from __future__ import annotations

import html

import streamlit as st

SCORE_COLORS = {"High": "#16a34a", "Medium": "#d97706", "Low": "#64748b"}
TYPE_COLORS = {
    "Hiring": "#0a66c2",
    "Sales / Buying Intent": "#7c3aed",
    "Partnership": "#0891b2",
    "Funding": "#16a34a",
    "Networking": "#db2777",
    "Lead / Client": "#ea580c",
    "Collaboration": "#0d9488",
}


def inject_css() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
html, body, [class*="css"] { font-family:'Inter',sans-serif; }

/* App background */
.stApp { background: radial-gradient(1200px 600px at 10% -10%, #14233b 0%, #0b1220 55%); }

/* Sidebar */
[data-testid="stSidebar"] { background:linear-gradient(180deg,#0a1525 0%,#0b1220 100%) !important;
    border-right:1px solid rgba(255,255,255,0.06); }
[data-testid="stSidebar"] * { color:#dbe5f1 !important; }

/* Hero */
.hero { background:linear-gradient(135deg,#0a66c2 0%,#0a4a8c 60%,#072a52 100%);
    border-radius:18px; padding:26px 28px; margin-bottom:18px;
    box-shadow:0 10px 30px rgba(10,102,194,0.30); }
.hero h1 { color:#fff; font-weight:900; font-size:28px; margin:0; letter-spacing:-0.5px; }
.hero p { color:#cfe2f7; margin:6px 0 0; font-size:14px; }

/* KPI cards */
.kpi-row { display:flex; gap:14px; flex-wrap:wrap; margin:6px 0 14px; }
.kpi { flex:1; min-width:150px; background:#111c2e; border:1px solid rgba(255,255,255,0.07);
    border-radius:16px; padding:18px 18px; box-shadow:0 4px 16px rgba(0,0,0,0.25); }
.kpi .v { font-size:30px; font-weight:900; color:#ffffff; line-height:1; }
.kpi .l { font-size:11px; color:#9fb2c9; font-weight:600; text-transform:uppercase;
    letter-spacing:0.06em; margin-top:8px; }
.kpi .d { font-size:12px; color:#5eead4; margin-top:4px; }

/* Opportunity card */
.opp { background:#111c2e; border:1px solid rgba(255,255,255,0.07); border-left:4px solid #0a66c2;
    border-radius:14px; padding:16px 18px; margin-bottom:12px; }
.opp:hover { border-color:rgba(10,102,194,0.6); }
.opp .top { display:flex; justify-content:space-between; align-items:flex-start; gap:10px; }
.opp .name { font-size:16px; font-weight:700; color:#fff; }
.opp .sub { font-size:12px; color:#9fb2c9; margin-top:1px; }
.opp .summary { font-size:14px; color:#dbe5f1; margin:10px 0 8px; }
.opp .why { font-size:13px; color:#9fb2c9; }
.opp .action { font-size:13px; color:#5eead4; margin-top:6px; }
.badge { display:inline-block; padding:2px 10px; border-radius:11px; font-size:11px;
    font-weight:700; color:#fff; }
.scorebig { text-align:right; }
.scorebig .num { font-size:26px; font-weight:900; color:#fff; line-height:1; }
.scorebig .lbl { font-size:11px; font-weight:700; }
.chip { display:inline-block; background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.1);
    color:#c7d4e4; padding:2px 9px; border-radius:10px; font-size:11px; margin:2px 4px 2px 0; }
.section-title { font-size:13px; font-weight:700; color:#9fb2c9; text-transform:uppercase;
    letter-spacing:0.08em; margin:14px 0 6px; }
</style>
""",
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f"<div class='hero'><h1>{html.escape(title)}</h1>"
        f"<p>{html.escape(subtitle)}</p></div>",
        unsafe_allow_html=True,
    )


def kpi_row(cards: list[tuple]) -> None:
    """cards = list of (value, label, optional_delta)."""
    html_cards = ""
    for c in cards:
        value, label = c[0], c[1]
        delta = c[2] if len(c) > 2 else ""
        d = f"<div class='d'>{html.escape(str(delta))}</div>" if delta else ""
        html_cards += (
            f"<div class='kpi'><div class='v'>{html.escape(str(value))}</div>"
            f"<div class='l'>{html.escape(str(label))}</div>{d}</div>"
        )
    st.markdown(f"<div class='kpi-row'>{html_cards}</div>", unsafe_allow_html=True)


def type_badge(opp_type: str) -> str:
    color = TYPE_COLORS.get(opp_type, "#0a66c2")
    return f"<span class='badge' style='background:{color}'>{html.escape(opp_type)}</span>"


def opportunity_card(o: dict) -> None:
    score_color = SCORE_COLORS.get(o.get("score_label", "Low"), "#64748b")
    signals = o.get("signals") or []
    if isinstance(signals, str):
        try:
            import json

            signals = json.loads(signals)
        except Exception:
            signals = [signals]
    chips = "".join(f"<span class='chip'>{html.escape(str(s))}</span>" for s in signals[:5])
    ai_tag = (
        "<span class='chip' style='border-color:#0a66c2;color:#7ab8f5'>★ AI</span>"
        if o.get("ai_generated")
        else "<span class='chip'>rules</span>"
    )

    st.markdown(
        f"""
<div class='opp' style='border-left-color:{score_color}'>
  <div class='top'>
    <div>
      <div class='name'>{html.escape(o.get('person_name') or '—')}</div>
      <div class='sub'>{html.escape(o.get('person_headline') or '')}
        {('· ' + html.escape(o.get('company'))) if o.get('company') else ''}</div>
    </div>
    <div class='scorebig'>
      <div class='num'>{o.get('score_value', 0)}</div>
      <div class='lbl' style='color:{score_color}'>{html.escape(o.get('score_label','Low'))}</div>
    </div>
  </div>
  <div style='margin-top:8px'>{type_badge(o.get('opp_type','Networking'))}
    <span class='chip'>confidence {o.get('confidence',0)}%</span> {ai_tag}</div>
  <div class='summary'>{html.escape(o.get('summary') or '')}</div>
  <div class='why'>💡 {html.escape(o.get('why_it_matters') or '')}</div>
  <div class='action'>➡ {html.escape(o.get('recommended_action') or '')}</div>
  <div style='margin-top:8px'>{chips}</div>
</div>
""",
        unsafe_allow_html=True,
    )
