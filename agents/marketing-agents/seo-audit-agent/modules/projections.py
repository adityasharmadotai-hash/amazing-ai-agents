"""
projections.py — Turn a rule-based audit into concrete "after you fix it" numbers.

The analyser scores each category as (passed checks / total checks) * 100, then a
weighted average gives the overall score. So every actionable issue (critical or
warning) represents roughly one failed check worth ~100/total points. Fixing it
lifts the category by that much, and the overall score by (points * category weight).

Everything here is derived from the real scoring model — no magic numbers — so the
"projected" figures shown in the UI are honest, explainable estimates.
"""

from __future__ import annotations

from modules.analyser import WEIGHTS

try:
    from modules.fixes import get_fix_guide
except Exception:  # fixes is optional for projection math
    def get_fix_guide(_msg):  # type: ignore
        return None

# Number of checks each category scores against (mirrors analyser.py).
CATEGORY_TOTALS = {
    "meta": 9, "headings": 6, "keywords": 8,
    "technical": 9, "images": 5, "links": 5,
}
CAT_META = {
    "meta":      ("Meta Tags",  "🏷️"),
    "headings":  ("Headings",   "📝"),
    "keywords":  ("Keywords",   "🔑"),
    "technical": ("Technical",  "⚙️"),
    "images":    ("Images",     "🖼️"),
    "links":     ("Links",      "🔗"),
}


def per_check_points(cat: str) -> int:
    """Points one fixed check restores in a category (0–100 scale)."""
    return round(100 / CATEGORY_TOTALS.get(cat, 6))


def actionable_issues(cat_data: dict) -> list:
    return [i for i in cat_data.get("issues", []) if i.get("severity") in ("critical", "warning")]


def project_category(cat: str, cat_data: dict) -> int:
    score = cat_data.get("score", 0)
    gain  = per_check_points(cat) * len(actionable_issues(cat_data))
    return min(100, score + gain)


def project(audit: dict) -> dict:
    """Full projection: per-category current/projected/delta + overall."""
    cats, overall_proj = {}, 0.0
    for cat, w in WEIGHTS.items():
        cd   = audit.get(cat, {})
        cur  = cd.get("score", 0)
        proj = project_category(cat, cd)
        cats[cat] = {"current": cur, "projected": proj, "delta": proj - cur,
                     "name": CAT_META[cat][0], "icon": CAT_META[cat][1]}
        overall_proj += proj * w
    cur_overall = audit.get("overall_score", 0)
    proj_overall = round(overall_proj)
    return {
        "categories": cats,
        "overall_current": cur_overall,
        "overall_projected": proj_overall,
        "overall_delta": proj_overall - cur_overall,
    }


def category_fixes(audit: dict, cat: str) -> list:
    """Per-issue improvement cards for one category, richest-impact first."""
    cd = audit.get(cat, {})
    w  = WEIGHTS.get(cat, 0.15)
    gain = per_check_points(cat)
    out = []
    for i in actionable_issues(cd):
        g = get_fix_guide(i["message"]) or {}
        out.append({
            "message": i["message"],
            "fix": i.get("fix", ""),
            "severity": i["severity"],
            "cat_points": gain,
            "overall_points": round(gain * w, 1),
            "difficulty": g.get("difficulty", "Medium"),
            "time": g.get("time", ""),
            "title": g.get("title", i["message"]),
            "summary": g.get("summary", ""),
        })
    out.sort(key=lambda x: -x["cat_points"])
    return out


def roadmap(audit: dict) -> list:
    """All actionable issues across the site, ranked by overall impact."""
    out = []
    for cat, w in WEIGHTS.items():
        cd = audit.get(cat, {})
        gain = per_check_points(cat)
        for i in actionable_issues(cd):
            g = get_fix_guide(i["message"]) or {}
            out.append({
                "category": cat,
                "cat_name": CAT_META[cat][0],
                "icon": CAT_META[cat][1],
                "message": i["message"],
                "fix": i.get("fix", ""),
                "severity": i["severity"],
                "cat_points": gain,
                "overall_points": round(gain * w, 1),
                "difficulty": g.get("difficulty", "Medium"),
                "time": g.get("time", ""),
            })
    out.sort(key=lambda x: -x["overall_points"])
    return out
