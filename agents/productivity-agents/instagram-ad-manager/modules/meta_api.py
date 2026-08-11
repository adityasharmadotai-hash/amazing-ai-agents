"""
meta_api.py — Live Meta (Instagram) Marketing API client.

Thin `requests` wrapper over the Graph API (v21.0). Pulls campaigns, daily
insights (spend/reach/impressions/clicks/leads), a placement breakdown
(Feed vs Reels vs Stories), and Instagram lead-ads submissions.

Requires a long-lived access token with `ads_read` + `leads_retrieval`, and an
ad account id (with the `act_` prefix). See Tutorial.md for the token walkthrough.
The whole module degrades gracefully: `is_configured()` is False when secrets are
missing, and every call raises the typed `MetaAPIError` on failure so the UI can
show a "Connect your Meta account" state instead of crashing.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta

import requests

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None

API_VERSION = "v21.0"
BASE = f"https://graph.facebook.com/{API_VERSION}"

# action_types that represent a lead conversion in the insights `actions` array.
_LEAD_ACTION_TYPES = {
    "lead",
    "leadgen.other",
    "onsite_conversion.lead_grouped",
    "offsite_conversion.fb_pixel_lead",
}

# publisher_platform + platform_position → friendly placement label.
_PLACEMENT_LABELS = {
    "feed": "Feed",
    "instagram_reels": "Reels",
    "instagram_stories": "Stories",
    "story": "Stories",
    "reels": "Reels",
    "explore": "Explore",
    "instagram_explore": "Explore",
}


class MetaAPIError(RuntimeError):
    """Raised for any Meta Graph API failure (auth, network, or bad response)."""


def _secret(name: str) -> str:
    if st is not None:
        try:
            val = st.secrets.get(name)
            if val:
                return str(val)
        except Exception:
            pass
    return os.environ.get(name, "")


def get_token() -> str:
    return _secret("META_ACCESS_TOKEN")


def get_account_id() -> str:
    acct = _secret("META_AD_ACCOUNT_ID").strip()
    if acct and not acct.startswith("act_"):
        acct = f"act_{acct}"
    return acct


def is_configured() -> bool:
    return bool(get_token() and get_account_id())


# ── Low-level GET with paging ─────────────────────────────────────────────────
def _get(path: str, params: dict) -> dict:
    params = {**params, "access_token": get_token()}
    try:
        resp = requests.get(f"{BASE}/{path}", params=params, timeout=45)
    except requests.RequestException as e:
        raise MetaAPIError(f"Network error contacting Meta: {e}") from e
    if resp.status_code != 200:
        try:
            err = resp.json().get("error", {})
            msg = err.get("message", resp.text)
        except Exception:
            msg = resp.text
        raise MetaAPIError(f"Meta API error ({resp.status_code}): {msg}")
    return resp.json()


def _get_all(path: str, params: dict, max_pages: int = 25) -> list[dict]:
    """Follow cursor pagination and return the concatenated `data` arrays."""
    out: list[dict] = []
    payload = _get(path, params)
    out.extend(payload.get("data", []))
    pages = 1
    while pages < max_pages:
        nxt = payload.get("paging", {}).get("next")
        if not nxt:
            break
        try:
            resp = requests.get(nxt, timeout=45)
            payload = resp.json()
        except requests.RequestException as e:
            raise MetaAPIError(f"Network error during paging: {e}") from e
        out.extend(payload.get("data", []))
        pages += 1
    return out


# ── Campaigns ─────────────────────────────────────────────────────────────────
def list_campaigns() -> list[dict]:
    acct = get_account_id()
    rows = _get_all(
        f"{acct}/campaigns",
        {
            "fields": "id,name,status,effective_status,objective,daily_budget,lifetime_budget",
            "limit": 200,
        },
    )
    out = []
    for r in rows:
        budget_cents = r.get("daily_budget") or r.get("lifetime_budget") or 0
        out.append(
            {
                "id": r["id"],
                "name": r.get("name", ""),
                "status": _norm_status(r.get("effective_status") or r.get("status", "")),
                "objective": r.get("objective", ""),
                "budget": float(budget_cents) / 100.0,
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
    return out


def _norm_status(s: str) -> str:
    s = (s or "").upper()
    if s in ("ACTIVE", "CAMPAIGN_ACTIVE"):
        return "Active"
    if s in ("PAUSED", "CAMPAIGN_PAUSED", "ADSET_PAUSED"):
        return "Paused"
    if s in ("COMPLETED", "ARCHIVED"):
        return "Completed"
    return s.title() if s else "Unknown"


# ── Insights ──────────────────────────────────────────────────────────────────
def _leads_from_actions(actions: list[dict] | None) -> int:
    if not actions:
        return 0
    total = 0.0
    for a in actions:
        if a.get("action_type") in _LEAD_ACTION_TYPES:
            try:
                total += float(a.get("value", 0))
            except (TypeError, ValueError):
                pass
    return int(round(total))


def _time_range(days: int) -> dict:
    until = date.today()
    since = until - timedelta(days=days - 1)
    return {"since": since.isoformat(), "until": until.isoformat()}


def get_daily_insights(days: int = 70, breakdown_placement: bool = False) -> list[dict]:
    """
    Daily campaign insights. When `breakdown_placement` is True the rows are split
    by publisher_platform + platform_position (for the Reels-vs-Feed analysis);
    otherwise a single canonical 'All' row is returned per campaign per day.
    """
    acct = get_account_id()
    tr = _time_range(days)
    params = {
        "level": "campaign",
        "time_increment": 1,
        "time_range": _json(tr),
        "fields": "campaign_id,spend,reach,impressions,clicks,actions",
        "limit": 500,
    }
    if breakdown_placement:
        params["breakdowns"] = "publisher_platform,platform_position"

    rows = _get_all(f"{acct}/insights", params)
    out = []
    for r in rows:
        placement = "All"
        if breakdown_placement:
            plat = (r.get("publisher_platform") or "").lower()
            # Instagram-only account: drop Facebook / Audience Network / Messenger rows.
            if plat and plat != "instagram":
                continue
            pos = (r.get("platform_position") or plat or "").lower()
            placement = _PLACEMENT_LABELS.get(pos, pos.title() or "Other")
        out.append(
            {
                "campaign_id": r.get("campaign_id", ""),
                "date": r.get("date_start", ""),
                "placement": placement,
                "spend": float(r.get("spend", 0) or 0),
                "reach": int(float(r.get("reach", 0) or 0)),
                "impressions": int(float(r.get("impressions", 0) or 0)),
                "clicks": int(float(r.get("clicks", 0) or 0)),
                "leads": _leads_from_actions(r.get("actions")),
            }
        )
    return out


def _json(obj: dict) -> str:
    import json

    return json.dumps(obj)


# ── Lead ads ──────────────────────────────────────────────────────────────────
def _list_ads() -> list[dict]:
    acct = get_account_id()
    rows = _get_all(
        f"{acct}/ads",
        {"fields": "id,name,campaign_id", "limit": 200},
    )
    return rows


def _parse_lead(field_data: list[dict]) -> dict:
    """Meta lead field_data is a list of {name, values:[...]}. Flatten it."""
    flat = {}
    for f in field_data or []:
        vals = f.get("values") or []
        flat[f.get("name", "").lower()] = vals[0] if vals else ""
    name = flat.get("full_name") or " ".join(
        v for v in (flat.get("first_name"), flat.get("last_name")) if v
    )
    return {
        "name": name.strip(),
        "email": flat.get("email", ""),
        "phone": flat.get("phone_number") or flat.get("phone", ""),
        "raw": flat,
    }


def get_leads(days: int = 70) -> list[dict]:
    """Fetch lead-ads submissions across all ads in the account."""
    cutoff = datetime.now() - timedelta(days=days)
    out = []
    for ad in _list_ads():
        try:
            rows = _get_all(
                f"{ad['id']}/leads",
                {"fields": "id,created_time,field_data,ad_name,campaign_id", "limit": 200},
                max_pages=10,
            )
        except MetaAPIError:
            # An ad without a lead form (or without retrieval scope) — skip it.
            continue
        for r in rows:
            created = r.get("created_time", "")[:19]
            try:
                if created and datetime.fromisoformat(created.replace("T", " ")) < cutoff:
                    continue
            except ValueError:
                pass
            parsed = _parse_lead(r.get("field_data"))
            out.append(
                {
                    "id": r.get("id", ""),
                    "name": parsed["name"],
                    "email": parsed["email"],
                    "phone": parsed["phone"],
                    "campaign_id": r.get("campaign_id") or ad.get("campaign_id", ""),
                    "ad_name": r.get("ad_name") or ad.get("name", ""),
                    "received_at": created or datetime.now().isoformat(timespec="seconds"),
                    # Leads arrive pre-qualified (conditional application form gates the form).
                    "status": "Qualified",
                    "audience": "",
                    "age_range": "",
                }
            )
    return out


# ── Orchestration ─────────────────────────────────────────────────────────────
def pull_all(days: int = 70) -> dict:
    """
    Pull everything needed for a full sync. Returns normalized dicts ready for
    `database.upsert_*`. Raises MetaAPIError on any hard failure.
    """
    if not is_configured():
        raise MetaAPIError("Meta credentials are not configured.")

    campaigns = list_campaigns()
    metrics = get_daily_insights(days=days, breakdown_placement=False)
    try:
        placement = get_daily_insights(days=days, breakdown_placement=True)
    except MetaAPIError:
        placement = []  # placement breakdown is best-effort
    leads = get_leads(days=days)

    return {
        "campaigns": campaigns,
        "metrics": metrics + placement,
        "leads": leads,
    }
