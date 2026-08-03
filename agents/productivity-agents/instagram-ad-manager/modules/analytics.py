"""
analytics.py — deterministic metric computations (no AI).

Turns the raw rows from `database` into everything the dashboard and the AI need:
the per-campaign table (§1), dashboard KPIs (§7), chart-ready time series (§7),
week-over-week deltas ("CPL increased 18%"), placement (Reels vs Feed) and
hour-of-day rollups, and lead-quality breakdowns (§6). Everything here is pure
and JSON-serializable so `agent.py` can hand compact stats straight to Gemini.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta

from . import database as db

CANONICAL = "All"


# ── Small helpers ─────────────────────────────────────────────────────────────
def safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def ctr(clicks: float, impressions: float) -> float:
    return round(safe_div(clicks, impressions) * 100, 2)


def cpc(spend: float, clicks: float) -> float:
    return round(safe_div(spend, clicks), 2)


def cpl(spend: float, leads: float) -> float:
    return round(safe_div(spend, leads), 2)


def conv_rate(leads: float, clicks: float) -> float:
    return round(safe_div(leads, clicks) * 100, 2)


def _canonical_rows(metrics: list[dict]) -> list[dict]:
    """Prefer placement='All' rows; if none exist, aggregate placement rows."""
    canon = [m for m in metrics if m.get("placement", CANONICAL) == CANONICAL]
    if canon:
        return canon
    agg: dict[tuple, dict] = {}
    for m in metrics:
        k = (m["campaign_id"], m["date"])
        row = agg.setdefault(
            k,
            {
                "campaign_id": m["campaign_id"],
                "date": m["date"],
                "placement": CANONICAL,
                "spend": 0.0,
                "reach": 0,
                "impressions": 0,
                "clicks": 0,
                "leads": 0,
            },
        )
        for f in ("spend", "reach", "impressions", "clicks", "leads"):
            row[f] += m.get(f, 0) or 0
    return list(agg.values())


def _totals(rows: list[dict]) -> dict:
    t = {"spend": 0.0, "reach": 0, "impressions": 0, "clicks": 0, "leads": 0}
    for r in rows:
        for f in t:
            t[f] += r.get(f, 0) or 0
    t["ctr"] = ctr(t["clicks"], t["impressions"])
    t["cpc"] = cpc(t["spend"], t["clicks"])
    t["cpl"] = cpl(t["spend"], t["leads"])
    t["conversion_rate"] = conv_rate(t["leads"], t["clicks"])
    t["spend"] = round(t["spend"], 2)
    return t


# ── §1 Per-campaign table ─────────────────────────────────────────────────────
def campaign_table(metrics: list[dict], campaigns: list[dict], leads: list[dict]) -> list[dict]:
    canon = _canonical_rows(metrics)
    by_camp: dict[str, list[dict]] = defaultdict(list)
    for r in canon:
        by_camp[r["campaign_id"]].append(r)

    lead_counts: dict[str, int] = defaultdict(int)
    qualified_counts: dict[str, int] = defaultdict(int)
    for ld in leads:
        lead_counts[ld.get("campaign_id", "")] += 1
        if ld.get("status") in db.QUALIFIED_STATUSES:
            qualified_counts[ld.get("campaign_id", "")] += 1

    out = []
    for c in campaigns:
        rows = by_camp.get(c["id"], [])
        t = _totals(rows)
        rec_leads = lead_counts.get(c["id"], 0)
        out.append(
            {
                "id": c["id"],
                "name": c["name"],
                "status": c.get("status", "Unknown"),
                "budget": round(c.get("budget", 0) or 0, 2),
                "spend": t["spend"],
                "reach": t["reach"],
                "impressions": t["impressions"],
                "clicks": t["clicks"],
                "ctr": t["ctr"],
                "cpc": t["cpc"],
                "cpl": t["cpl"],
                "leads": t["leads"],
                "lead_records": rec_leads,
                "qualified_leads": qualified_counts.get(c["id"], 0),
                "conversion_rate": t["conversion_rate"],
            }
        )
    # Campaigns with spend first, highest spend on top.
    out.sort(key=lambda r: r["spend"], reverse=True)
    return out


# ── §7 Dashboard KPIs ─────────────────────────────────────────────────────────
def dashboard_kpis(metrics: list[dict], leads: list[dict], campaigns: list[dict]) -> dict:
    canon = _canonical_rows(metrics)
    t = _totals(canon)
    today = date.today().isoformat()
    today_spend = round(sum(r["spend"] for r in canon if r["date"] == today), 2)

    qualified = sum(1 for ld in leads if ld.get("status") in db.QUALIFIED_STATUSES)
    rejected = sum(1 for ld in leads if ld.get("status") in db.REJECTED_STATUSES)
    active = sum(1 for c in campaigns if c.get("status") == "Active")

    table = campaign_table(metrics, campaigns, leads)
    ranked = [r for r in table if r["leads"] > 0]
    best = min(ranked, key=lambda r: r["cpl"]) if ranked else None
    worst = max(ranked, key=lambda r: r["cpl"]) if ranked else None

    return {
        "total_spend": t["spend"],
        "today_spend": today_spend,
        "total_leads": len(leads),
        "metrics_leads": t["leads"],
        "qualified_leads": qualified,
        "rejected_leads": rejected,
        "active_campaigns": active,
        "avg_cpl": t["cpl"] if t["leads"] else cpl(t["spend"], len(leads)),
        "avg_ctr": t["ctr"],
        "avg_cpc": t["cpc"],
        "conversion_rate": t["conversion_rate"],
        "best_campaign": {"name": best["name"], "cpl": best["cpl"]} if best else None,
        "worst_campaign": {"name": worst["name"], "cpl": worst["cpl"]} if worst else None,
    }


# ── §7 Chart-ready time series ────────────────────────────────────────────────
def time_series(metrics: list[dict]) -> list[dict]:
    """One row per date with spend, leads, clicks, impressions, ctr, cpl."""
    canon = _canonical_rows(metrics)
    by_date: dict[str, dict] = {}
    for r in canon:
        d = by_date.setdefault(
            r["date"],
            {"date": r["date"], "spend": 0.0, "leads": 0, "clicks": 0, "impressions": 0},
        )
        d["spend"] += r.get("spend", 0) or 0
        d["leads"] += r.get("leads", 0) or 0
        d["clicks"] += r.get("clicks", 0) or 0
        d["impressions"] += r.get("impressions", 0) or 0
    out = []
    for d in sorted(by_date.values(), key=lambda x: x["date"]):
        d["spend"] = round(d["spend"], 2)
        d["cpl"] = cpl(d["spend"], d["leads"])
        d["ctr"] = ctr(d["clicks"], d["impressions"])
        out.append(d)
    return out


def leads_by_day(leads: list[dict]) -> list[dict]:
    """Actual lead records per day (received)."""
    by_day: dict[str, int] = defaultdict(int)
    for ld in leads:
        day = (ld.get("received_at", "") or "")[:10]
        if day:
            by_day[day] += 1
    return [{"date": d, "leads": by_day[d]} for d in sorted(by_day)]


def qualified_vs_rejected(leads: list[dict]) -> dict:
    counts = defaultdict(int)
    for ld in leads:
        counts[ld.get("status", "New")] += 1
    return dict(counts)


def campaign_comparison(metrics: list[dict], campaigns: list[dict], leads: list[dict]) -> list[dict]:
    table = campaign_table(metrics, campaigns, leads)
    return [
        {"name": r["name"], "spend": r["spend"], "leads": r["leads"], "cpl": r["cpl"], "ctr": r["ctr"]}
        for r in table
    ]


# ── §2 Week-over-week + trend deltas ──────────────────────────────────────────
def _window_totals(canon: list[dict], start: date, end: date) -> dict:
    rows = [r for r in canon if start.isoformat() <= r["date"] <= end.isoformat()]
    return _totals(rows)


def week_over_week(metrics: list[dict]) -> dict:
    """Compare the last 7 days with the 7 days before that."""
    canon = _canonical_rows(metrics)
    today = date.today()
    cur = _window_totals(canon, today - timedelta(days=6), today)
    prev = _window_totals(canon, today - timedelta(days=13), today - timedelta(days=7))

    def pct(now: float, before: float) -> float:
        if not before:
            return 0.0
        return round((now - before) / before * 100, 1)

    return {
        "current": cur,
        "previous": prev,
        "delta_pct": {
            "spend": pct(cur["spend"], prev["spend"]),
            "leads": pct(cur["leads"], prev["leads"]),
            "cpl": pct(cur["cpl"], prev["cpl"]),
            "ctr": pct(cur["ctr"], prev["ctr"]),
            "clicks": pct(cur["clicks"], prev["clicks"]),
        },
    }


def campaign_trends(metrics: list[dict], campaigns: list[dict]) -> dict:
    """Classify each campaign as improving / declining by recent-vs-prior CPL."""
    canon = _canonical_rows(metrics)
    today = date.today()
    by_camp: dict[str, list[dict]] = defaultdict(list)
    for r in canon:
        by_camp[r["campaign_id"]].append(r)

    name = {c["id"]: c["name"] for c in campaigns}
    improving, declining = [], []
    for cid, rows in by_camp.items():
        cur = _window_totals(rows, today - timedelta(days=6), today)
        prev = _window_totals(rows, today - timedelta(days=13), today - timedelta(days=7))
        if cur["leads"] == 0 and prev["leads"] == 0:
            continue
        if prev["cpl"] and cur["cpl"]:
            change = round((cur["cpl"] - prev["cpl"]) / prev["cpl"] * 100, 1)
            entry = {"name": name.get(cid, cid), "cpl_now": cur["cpl"], "cpl_prev": prev["cpl"], "change_pct": change}
            if change < -5:
                improving.append(entry)
            elif change > 5:
                declining.append(entry)
    improving.sort(key=lambda e: e["change_pct"])
    declining.sort(key=lambda e: e["change_pct"], reverse=True)
    return {"improving": improving, "declining": declining}


# ── Placement (Reels vs Feed) ─────────────────────────────────────────────────
def placement_breakdown(metrics: list[dict]) -> list[dict]:
    rows = [m for m in metrics if m.get("placement", CANONICAL) != CANONICAL]
    if not rows:
        return []
    by_pl: dict[str, dict] = {}
    for r in rows:
        p = by_pl.setdefault(
            r["placement"],
            {"placement": r["placement"], "spend": 0.0, "impressions": 0, "clicks": 0, "leads": 0},
        )
        p["spend"] += r.get("spend", 0) or 0
        p["impressions"] += r.get("impressions", 0) or 0
        p["clicks"] += r.get("clicks", 0) or 0
        p["leads"] += r.get("leads", 0) or 0
    out = []
    for p in by_pl.values():
        p["spend"] = round(p["spend"], 2)
        p["ctr"] = ctr(p["clicks"], p["impressions"])
        p["cpl"] = cpl(p["spend"], p["leads"])
        out.append(p)
    out.sort(key=lambda x: x["leads"], reverse=True)
    return out


# ── §6 Lead-quality breakdowns ────────────────────────────────────────────────
def _quality_by(leads: list[dict], key: str) -> list[dict]:
    groups: dict[str, dict] = {}
    for ld in leads:
        k = ld.get(key) or "(unknown)"
        g = groups.setdefault(k, {"group": k, "total": 0, "qualified": 0, "rejected": 0})
        g["total"] += 1
        if ld.get("status") in db.QUALIFIED_STATUSES:
            g["qualified"] += 1
        elif ld.get("status") in db.REJECTED_STATUSES:
            g["rejected"] += 1
    out = []
    for g in groups.values():
        g["qualified_rate"] = round(safe_div(g["qualified"], g["total"]) * 100, 1)
        out.append(g)
    out.sort(key=lambda x: (x["qualified_rate"], x["total"]), reverse=True)
    return out


def lead_quality(leads: list[dict]) -> dict:
    return {
        "by_audience": _quality_by(leads, "audience"),
        "by_age_range": _quality_by(leads, "age_range"),
        "by_ad": _quality_by(leads, "ad_name"),
        "by_campaign": _quality_by(leads, "campaign_id"),
        "status_counts": qualified_vs_rejected(leads),
    }


# ── Compact stats payload for the AI ──────────────────────────────────────────
def build_stats_payload(metrics: list[dict], campaigns: list[dict], leads: list[dict]) -> dict:
    """A compact, JSON-serializable snapshot for Gemini — never raw row dumps."""
    name_map = {c["id"]: c["name"] for c in campaigns}
    lq = lead_quality(leads)
    # Replace campaign ids with names in the by_campaign quality breakdown.
    for g in lq["by_campaign"]:
        g["group"] = name_map.get(g["group"], g["group"])

    return {
        "as_of": date.today().isoformat(),
        "kpis": dashboard_kpis(metrics, leads, campaigns),
        "campaigns": campaign_table(metrics, campaigns, leads),
        "week_over_week": week_over_week(metrics),
        "trends": campaign_trends(metrics, campaigns),
        "placements": placement_breakdown(metrics),
        "lead_quality": lq,
        "recent_series": time_series(metrics)[-14:],
    }
