"""
demo_seed.py — optional sample data for UI exploration.

This is NOT the app's data model. The app is built around the live Meta
Marketing API (`meta_api.py`); this seeder only lets you click through the
dashboard, charts, and filters before a Meta account is connected. It writes
realistic ~10-week campaign metrics and lead records straight into SQLite.
"""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta

from . import database as db

_RNG = random.Random(42)  # deterministic sample

# ── Campaign profiles (tuned so best/worst/trends are interesting) ────────────
# target_cpl drives lead volume so cost-per-lead lands in a realistic recruiting
# range; quality drives how often the team marks those leads Qualified.
_CAMPAIGNS = [
    # id, name, status, budget/day, ctr%, cpm$, target_cpl$, quality, weekly_cpl_drift
    ("c_reels_tech", "SF Tech Jobs — Reels Push", "Active", 22, 2.4, 8.5, 13.0, 0.62, -0.12),
    ("c_healthcare", "Bay Area Healthcare Hiring", "Active", 16, 1.8, 9.0, 24.0, 0.48, 0.05),
    ("c_startups", "Remote-Friendly Startups", "Active", 14, 2.0, 7.5, 20.0, 0.40, -0.04),
    ("c_warehouse", "Warehouse & Logistics — East Bay", "Paused", 10, 1.1, 10.5, 48.0, 0.18, 0.22),
    ("c_newgrad", "New Grad Software Roles", "Active", 18, 2.2, 8.0, 16.0, 0.55, 0.14),
    ("c_finance", "Finance & Ops — SF", "Completed", 9, 1.5, 9.5, 30.0, 0.33, 0.0),
]

# name, spend share, ctr mult, cpl mult (Reels convert cheaper → best placement)
_PLACEMENTS = [("Feed", 0.40, 0.85, 1.0), ("Reels", 0.45, 1.25, 0.72), ("Stories", 0.15, 0.7, 1.5)]

_AUDIENCES = [
    ("Lookalike 1% — Tech", 1.25),
    ("Interest: Job Seekers", 1.0),
    ("Broad 22–45 Bay Area", 0.8),
    ("Retargeting — Site Visitors", 1.35),
    ("Interest: Recent Grads", 0.95),
]
_AGES = [("18-24", 0.9), ("25-34", 1.2), ("35-44", 1.0), ("45-54", 0.7)]
_ADS = ["Reel — Day in the Life", "Carousel — Top Employers", "Story — Apply Now", "Single Image — $120k Roles"]

_FIRST = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Sam", "Jamie", "Priya", "Diego",
          "Wei", "Fatima", "Noah", "Ava", "Liam", "Sofia", "Ethan", "Maya", "Omar", "Grace"]
_LAST = ["Chen", "Patel", "Garcia", "Nguyen", "Smith", "Kim", "Johnson", "Lopez", "Khan", "Brown",
         "Reyes", "Ali", "Wang", "Martin", "Singh", "Rossi", "Adams", "Cruz", "Park", "Diaz"]

_STATUS_WEIGHTS_HIGH = [
    ("Qualified", 0.28), ("Interview Scheduled", 0.14), ("Hired", 0.06),
    ("Rejected", 0.16), ("No Response", 0.14), ("Invalid", 0.06),
    ("Duplicate", 0.04), ("New", 0.12),
]
_STATUS_WEIGHTS_LOW = [
    ("Qualified", 0.08), ("Interview Scheduled", 0.03), ("Hired", 0.01),
    ("Rejected", 0.34), ("No Response", 0.22), ("Invalid", 0.14),
    ("Duplicate", 0.08), ("New", 0.10),
]


def _weighted(rng: random.Random, pairs):
    r = rng.random()
    acc = 0.0
    for label, w in pairs:
        acc += w
        if r <= acc:
            return label
    return pairs[-1][0]


def _campaign_rows() -> list[dict]:
    now = datetime.now().isoformat(timespec="seconds")
    return [
        {"id": c[0], "name": c[1], "status": c[2], "objective": "OUTCOME_LEADS",
         "budget": c[3], "updated_at": now}
        for c in _CAMPAIGNS
    ]


def _metric_rows(days: int) -> tuple[list[dict], dict[str, int]]:
    """Return (metric rows, ad-reported leads per campaign)."""
    rows: list[dict] = []
    camp_leads: dict[str, int] = {}
    today = date.today()
    for cid, name, status, budget, ctr_base, cpm, target_cpl, quality, drift in _CAMPAIGNS:
        active_days = days if status != "Completed" else days // 2
        total_leads = 0
        carry = {p[0]: 0.0 for p in _PLACEMENTS}  # fractional-lead accumulator
        for d in range(active_days):
            day = today - timedelta(days=d)
            if status == "Paused" and d < 5:
                continue  # paused recently → no fresh spend
            # Recency drift: the last 7 days move CPL up or down for some campaigns.
            recent = 1.0 + (drift * (7 - d) / 7.0) if d < 7 else 1.0
            fill = _RNG.uniform(0.7, 1.05)
            day_spend = budget * fill
            all_row = {"campaign_id": cid, "date": day.isoformat(), "placement": "All",
                       "spend": 0.0, "reach": 0, "impressions": 0, "clicks": 0, "leads": 0}
            for pname, share, ctr_mult, cpl_mult in _PLACEMENTS:
                spend = day_spend * share * _RNG.uniform(0.9, 1.1)
                impressions = int(spend / cpm * 1000)
                ctr = ctr_base * ctr_mult / 100.0 * _RNG.uniform(0.85, 1.15)
                clicks = int(impressions * ctr)
                # Leads derived from a target CPL (so cost-per-lead is realistic);
                # a higher recent multiplier makes leads more expensive (fewer).
                # Fractional expectations accumulate so low-budget days aren't lost.
                eff_cpl = target_cpl * cpl_mult * recent
                carry[pname] += spend / eff_cpl * _RNG.uniform(0.8, 1.2)
                leads = int(carry[pname])
                carry[pname] -= leads
                reach = int(impressions * _RNG.uniform(0.6, 0.8))
                rows.append({
                    "campaign_id": cid, "date": day.isoformat(), "placement": pname,
                    "spend": round(spend, 2), "reach": reach, "impressions": impressions,
                    "clicks": clicks, "leads": leads,
                })
                all_row["spend"] += spend
                all_row["reach"] += reach
                all_row["impressions"] += impressions
                all_row["clicks"] += clicks
                all_row["leads"] += leads
            all_row["spend"] = round(all_row["spend"], 2)
            rows.append(all_row)
            total_leads += all_row["leads"]
        camp_leads[cid] = total_leads
    return rows, camp_leads


def _lead_rows(days: int, camp_leads: dict[str, int]) -> list[dict]:
    """One CRM lead record per ad-reported lead, so counts match the metrics."""
    quality_of = {c[0]: c[7] for c in _CAMPAIGNS}
    rows = []
    now = datetime.now()
    i = 0
    for cid, count in camp_leads.items():
        quality = quality_of.get(cid, 0.4)
        for _ in range(count):
            audience, aud_mult = _RNG.choice(_AUDIENCES)
            age, age_mult = _RNG.choice(_AGES)
            ad = _RNG.choice(_ADS)
            eff_quality = min(0.9, max(0.05, quality * aud_mult * age_mult))
            weights = _STATUS_WEIGHTS_HIGH if _RNG.random() < eff_quality else _STATUS_WEIGHTS_LOW
            status = _weighted(_RNG, weights)
            received = now - timedelta(days=_RNG.randint(0, days - 1),
                                       hours=_RNG.randint(0, 23), minutes=_RNG.randint(0, 59))
            name = f"{_RNG.choice(_FIRST)} {_RNG.choice(_LAST)}"
            email = name.lower().replace(" ", ".") + f"{_RNG.randint(1, 99)}@example.com"
            phone = f"+1 415 {_RNG.randint(200, 999)} {_RNG.randint(1000, 9999)}"
            rows.append({
                "id": f"lead_{i:05d}", "name": name, "email": email, "phone": phone,
                "campaign_id": cid, "ad_name": ad, "received_at": received.isoformat(timespec="seconds"),
                "status": status, "audience": audience, "age_range": age,
            })
            i += 1
    return rows


def seed(days: int = 70) -> dict:
    """Wipe existing data and load a fresh deterministic sample. Returns counts."""
    db.clear_all()
    metric_rows, camp_leads = _metric_rows(days)
    c = db.upsert_campaigns(_campaign_rows())
    m = db.upsert_metrics(metric_rows)
    ld = db.upsert_leads(_lead_rows(days, camp_leads))
    return {"campaigns": c, "metrics": m, "leads": ld}
