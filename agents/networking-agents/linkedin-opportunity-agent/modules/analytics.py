"""
analytics.py — Aggregations & trend computations for the dashboard.

Pure functions over the opportunities table — no Streamlit imports — so they are
easy to test and reuse. Returns plain dicts / pandas DataFrames.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime

import pandas as pd

from . import database as db


def opportunities_df() -> pd.DataFrame:
    rows = db.list_opportunities(order="recent")
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["created_dt"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
    df["date"] = df["created_dt"].dt.date
    return df


def kpis() -> dict:
    c = db.counts()
    df = opportunities_df()
    avg_score = int(df["score_value"].mean()) if not df.empty else 0
    avg_conf = int(df["confidence"].mean()) if not df.empty else 0
    return {
        "total": c["total"],
        "high": c["high"],
        "medium": c["medium"],
        "low": c["low"],
        "avg_score": avg_score,
        "avg_confidence": avg_conf,
    }


def by_type() -> pd.DataFrame:
    c = db.counts()["by_type"]
    if not c:
        return pd.DataFrame(columns=["Type", "Count"])
    return pd.DataFrame(
        sorted(c.items(), key=lambda kv: kv[1], reverse=True), columns=["Type", "Count"]
    )


def by_industry(top: int = 8) -> pd.DataFrame:
    c = db.counts()["by_industry"]
    if not c:
        return pd.DataFrame(columns=["Industry", "Count"])
    items = sorted(c.items(), key=lambda kv: kv[1], reverse=True)[:top]
    return pd.DataFrame(items, columns=["Industry", "Count"])


def by_score_label() -> pd.DataFrame:
    c = db.counts()
    return pd.DataFrame(
        [("High", c["high"]), ("Medium", c["medium"]), ("Low", c["low"])],
        columns=["Score", "Count"],
    )


def opportunities_over_time() -> pd.DataFrame:
    df = opportunities_df()
    if df.empty:
        return pd.DataFrame(columns=["date", "count"])
    series = df.groupby("date").size().reset_index(name="count")
    series["date"] = pd.to_datetime(series["date"])
    return series.sort_values("date")


def hiring_trends() -> pd.DataFrame:
    """Daily count of hiring-type opportunities — a simple hiring-demand signal."""
    df = opportunities_df()
    if df.empty:
        return pd.DataFrame(columns=["date", "count"])
    hiring = df[df["opp_type"] == "Hiring"]
    if hiring.empty:
        return pd.DataFrame(columns=["date", "count"])
    s = hiring.groupby("date").size().reset_index(name="count")
    s["date"] = pd.to_datetime(s["date"])
    return s.sort_values("date")


def funding_trends() -> pd.DataFrame:
    df = opportunities_df()
    if df.empty:
        return pd.DataFrame(columns=["date", "count"])
    funding = df[df["opp_type"] == "Funding"]
    if funding.empty:
        return pd.DataFrame(columns=["date", "count"])
    s = funding.groupby("date").size().reset_index(name="count")
    s["date"] = pd.to_datetime(s["date"])
    return s.sort_values("date")


def top_industry() -> str:
    c = db.counts()["by_industry"]
    if not c:
        return "—"
    return max(c.items(), key=lambda kv: kv[1])[0]


def top_companies(n: int = 5) -> pd.DataFrame:
    df = opportunities_df()
    if df.empty:
        return pd.DataFrame(columns=["Company", "Opportunities"])
    counts = Counter(df[df["company"] != ""]["company"])
    items = counts.most_common(n)
    return pd.DataFrame(items, columns=["Company", "Opportunities"])


def save_today_snapshot() -> None:
    """Persist a daily KPI snapshot for the opportunity-history chart."""
    k = kpis()
    db.save_analytics_snapshot(
        {
            "snapshot_date": datetime.utcnow().date().isoformat(),
            "opportunities_found": k["total"],
            "high": k["high"],
            "medium": k["medium"],
            "low": k["low"],
            "top_industry": top_industry(),
            "payload": {"avg_score": k["avg_score"]},
        }
    )
