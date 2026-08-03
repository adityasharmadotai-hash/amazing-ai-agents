"""
sync_service.py — the one place that performs a full sync.

Shared by the background job (`sync.py`, run from GitHub Actions / cron / Task
Scheduler) and the app's "Sync Now" button. A sync:

  1. pulls campaigns, insights, and leads from the Meta Marketing API
     (or seeds the sample dataset when asked),
  2. recomputes analytics + the marketing health score,
  3. runs Gemini analysis, recommendations, lead-learning, and an executive summary,
  4. generates notifications, and
  5. records everything (analyses, sync_log, last-sync time) in SQLite.

Every stage is defensive: a failure in the AI stage downgrades the sync to
"partial" rather than losing the freshly pulled data.
"""

from __future__ import annotations

from datetime import date, datetime

from . import agent, analytics, config, database as db, demo_seed, meta_api

log = config.get_logger("admanager.sync")


def _noop(_msg: str, _pct: float) -> None:
    pass


def _notif_exists_today(title: str) -> bool:
    today = date.today().isoformat()
    for n in db.get_notifications(limit=60):
        if n["title"] == title and (n.get("created_at", "") or "").startswith(today):
            return True
    return False


def _notify(title: str, body: str, severity: str, category: str) -> int:
    if _notif_exists_today(title):
        return 0
    db.add_notification(title, body, severity, category)
    return 1


def generate_notifications(stats: dict) -> int:
    """Deterministic threshold-based notifications. Returns how many were added."""
    added = 0
    kpis = stats["kpis"]
    wow = stats["week_over_week"]["delta_pct"]
    health = stats["health"]
    ai = stats["audience_insights"]
    fc = stats.get("forecast", {})

    if wow.get("cpl", 0) >= 15:
        added += _notify("Cost per lead is rising",
                         f"CPL is up {wow['cpl']:.0f}% week over week (now ${kpis['avg_cpl']:.2f}). "
                         "Review the declining campaigns.", "warning", "Performance")
    elif wow.get("cpl", 0) <= -10:
        added += _notify("Cost per lead improving",
                         f"CPL is down {abs(wow['cpl']):.0f}% week over week (now ${kpis['avg_cpl']:.2f}). "
                         "Consider scaling the winners.", "success", "Performance")

    if wow.get("leads", 0) <= -20:
        added += _notify("Lead volume dropping",
                         f"Leads are down {abs(wow['leads']):.0f}% week over week. "
                         "Check budgets and creative fatigue.", "warning", "Leads")

    if health["score"] < 45:
        added += _notify("Marketing health at risk",
                         f"Health score is {health['score']}/100 ({health['label']}). "
                         f"Weakest area: {health['weakest']}.", "critical", "Health")
    elif health["score"] >= 80:
        added += _notify("Marketing health is strong",
                         f"Health score is {health['score']}/100 ({health['label']}). "
                         f"Strongest area: {health['strongest']}.", "success", "Health")

    if kpis.get("best_campaign"):
        bc = kpis["best_campaign"]
        added += _notify(f"Top performer: {bc['name']}",
                         f"Lowest cost per lead at ${bc['cpl']:.2f}. A candidate to scale.",
                         "success", "Campaigns")
    if kpis.get("worst_campaign") and kpis["avg_cpl"] and kpis["worst_campaign"]["cpl"] > 2 * kpis["avg_cpl"]:
        wc = kpis["worst_campaign"]
        added += _notify(f"High-cost campaign: {wc['name']}",
                         f"CPL ${wc['cpl']:.2f} is over 2× the account average. Consider pausing or refreshing.",
                         "warning", "Campaigns")

    if ai.get("best_audience"):
        top = ai["by_audience"]["top"][0]
        added += _notify(f"High-quality source: {top['group']}",
                         f"{top['qualified_rate']:.0f}% of these leads are qualified — worth more budget.",
                         "info", "Audience")

    if fc.get("leads_direction") == "falling":
        added += _notify("Forecast: leads trending down",
                         f"Next {fc.get('horizon_days',7)} days project ~{fc.get('next7_leads',0):.0f} leads "
                         f"at ~${fc.get('projected_cpl',0):.2f} CPL. Act early.", "info", "Forecast")

    return added


def run_sync(days: int = None, source: str = "manual", run_ai: bool = True,
             use_sample: bool = False, force_recs: bool = False, skip_fetch: bool = False,
             on_progress=None) -> dict:
    """
    Perform a full sync. `on_progress(message, pct)` is called for UI progress.
    `skip_fetch=True` re-runs analytics/AI/notifications on the data already in the
    database (used to refresh insights on sample data without re-pulling).
    Returns a result dict: {ok, status, counts, health, ai_ran, notifications, messages}.
    """
    days = days or config.DEFAULT_SYNC_DAYS
    progress = on_progress or _noop
    sync_id = db.start_sync(source)
    messages: list[str] = []
    counts = {"campaigns": 0, "metrics": 0, "leads": 0}
    ai_ran = False
    status = "success"

    try:
        # 1) Acquire data ------------------------------------------------------
        progress("Pulling data…", 0.1)
        if skip_fetch:
            log.info("Recomputing insights on existing data")
            counts = {"campaigns": len(db.get_campaigns()),
                      "metrics": len(db.get_metrics()), "leads": len(db.get_leads())}
        elif use_sample:
            log.info("Seeding sample data (%d days)", days)
            counts = demo_seed.seed(days)
        elif meta_api.is_configured():
            log.info("Syncing from Meta Marketing API (%d days)", days)
            payload = meta_api.pull_all(days=days)
            counts["campaigns"] = db.upsert_campaigns(payload["campaigns"])
            counts["metrics"] = db.upsert_metrics(payload["metrics"])
            counts["leads"] = db.upsert_leads(payload["leads"])
        else:
            raise meta_api.MetaAPIError(
                "No data source: set META_ACCESS_TOKEN + META_AD_ACCOUNT_ID, or pass use_sample=True."
            )
        messages.append(f"Data: {counts['campaigns']} campaigns, "
                        f"{counts['metrics']} metric rows, {counts['leads']} leads.")

        # 2) Analytics ---------------------------------------------------------
        progress("Computing analytics…", 0.4)
        metrics = db.get_metrics()
        campaigns = db.get_campaigns()
        leads = db.get_leads()
        stats = analytics.build_stats_payload(metrics, campaigns, leads)
        health = stats["health"]
        db.save_analysis("health", health)
        messages.append(f"Health score: {health['score']}/100 ({health['label']}).")

        # 3) AI ----------------------------------------------------------------
        if run_ai and agent.is_configured():
            progress("Running Gemini analysis…", 0.6)
            try:
                db.save_analysis("performance", agent.analyze_performance(stats))
                db.save_analysis("exec_summary", agent.executive_summary(stats))
                db.save_analysis("lead_learning", agent.learn_from_leads(stats["lead_quality"]))

                progress("Generating recommendations…", 0.8)
                if force_recs or not db.has_recommendation_today():
                    recs = agent.daily_recommendations(stats, db.get_recommendations(limit=20))
                    for r in recs:
                        db.add_recommendation(
                            r.get("type", "Action"), r.get("target", ""), r.get("rationale", ""),
                            confidence=r.get("confidence", 0),
                            expected_impact=r.get("expected_impact", ""),
                            priority=r.get("priority", "medium"),
                        )
                    messages.append(f"Added {len(recs)} recommendations.")
                else:
                    messages.append("Recommendations already exist for today (skipped).")
                ai_ran = True
            except agent.AgentError as e:
                status = "partial"
                messages.append(f"AI stage skipped: {e}")
                log.warning("AI stage failed: %s", e)
        elif run_ai:
            status = "partial"
            messages.append("AI stage skipped: GEMINI_API_KEY not set.")

        # 4) Notifications -----------------------------------------------------
        progress("Updating notifications…", 0.92)
        n_added = generate_notifications(stats)
        messages.append(f"{n_added} new notification(s).")

        progress("Done.", 1.0)
        db.finish_sync(sync_id, status, counts["campaigns"], counts["metrics"],
                       counts["leads"], ai_ran, " ".join(messages))
        log.info("Sync %s: %s", status, " ".join(messages))
        return {"ok": True, "status": status, "counts": counts, "health": health,
                "ai_ran": ai_ran, "notifications": n_added, "messages": messages}

    except Exception as e:
        db.finish_sync(sync_id, "error", counts["campaigns"], counts["metrics"],
                       counts["leads"], ai_ran, str(e))
        log.error("Sync failed: %s", e)
        return {"ok": False, "status": "error", "counts": counts, "error": str(e),
                "messages": messages + [str(e)]}
