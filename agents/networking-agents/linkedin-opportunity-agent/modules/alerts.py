"""
alerts.py — Email alerts & digests.

Builds a daily / weekly opportunity digest and (optionally) sends it via SMTP.
When SMTP is not configured the digest is still generated for in-app preview, so
the feature is demonstrable without any mail server.
"""

from __future__ import annotations

import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from . import config, database as db


def _since(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def build_digest(period: str = "daily") -> dict:
    """Return {subject, text, html, count} for the requested period."""
    days = 1 if period == "daily" else 7
    opps = db.list_opportunities(since=_since(days), order="score")
    title = "Today's Opportunities" if period == "daily" else "This Week's Opportunities"
    date_str = datetime.now().strftime("%b %d, %Y")
    subject = f"[LinkedIn Opportunity Agent] {title} — {date_str} ({len(opps)})"

    if not opps:
        text = f"{title} ({date_str})\n\nNo new opportunities in this window. Run a scan to refresh."
        html = f"<h2>{title}</h2><p>{date_str}</p><p>No new opportunities in this window.</p>"
        return {"subject": subject, "text": text, "html": html, "count": 0}

    lines = [f"{title} ({date_str})", ""]
    rows_html = []
    for i, o in enumerate(opps[:15], 1):
        lines.append(
            f"{i}. {o['person_name']} ({o.get('company','')}) — {o['opp_type']}\n"
            f"   {o['summary']}\n"
            f"   Opportunity Score: {o['score_value']}  [{o['score_label']}]\n"
            f"   Action: {o.get('recommended_action','')}\n"
        )
        badge = {"High": "#16a34a", "Medium": "#d97706", "Low": "#64748b"}.get(
            o["score_label"], "#64748b"
        )
        rows_html.append(
            f"<tr><td style='padding:10px 0;border-bottom:1px solid #e5e7eb'>"
            f"<b>{i}. {o['person_name']}</b> "
            f"<span style='color:#64748b'>· {o.get('company','')}</span><br>"
            f"<span style='color:#0a66c2'>{o['opp_type']}</span> "
            f"<span style='background:{badge};color:#fff;padding:1px 8px;border-radius:10px;"
            f"font-size:12px'>{o['score_label']} {o['score_value']}</span><br>"
            f"<span>{o['summary']}</span><br>"
            f"<span style='color:#475569'>→ {o.get('recommended_action','')}</span>"
            f"</td></tr>"
        )

    text = "\n".join(lines)
    html = (
        f"<div style='font-family:Inter,Arial,sans-serif;max-width:640px'>"
        f"<h2 style='color:#0a66c2'>{title}</h2>"
        f"<p style='color:#64748b'>{date_str} · {len(opps)} opportunities</p>"
        f"<table style='width:100%;border-collapse:collapse'>{''.join(rows_html)}</table>"
        f"</div>"
    )
    return {"subject": subject, "text": text, "html": html, "count": len(opps)}


def send_digest(period: str = "daily") -> tuple[bool, str]:
    """Send the digest via SMTP. Returns (ok, message)."""
    digest = build_digest(period)
    if not config.smtp_configured():
        return False, "SMTP is not configured — add email settings on the Settings page."

    s = config.get_smtp_settings()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = digest["subject"]
    msg["From"] = s["sender"] or s["user"]
    msg["To"] = s["recipient"]
    msg.attach(MIMEText(digest["text"], "plain"))
    msg.attach(MIMEText(digest["html"], "html"))

    try:
        with smtplib.SMTP(s["host"], s["port"], timeout=20) as server:
            server.starttls()
            server.login(s["user"], s["password"])
            server.sendmail(msg["From"], [s["recipient"]], msg.as_string())
        return True, f"Digest sent to {s['recipient']} ({digest['count']} opportunities)."
    except Exception as e:  # surface the real error to the user
        return False, f"Failed to send: {e}"
