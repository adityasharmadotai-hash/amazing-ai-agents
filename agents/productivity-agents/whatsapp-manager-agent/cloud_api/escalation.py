"""
escalation.py — hand a conversation off to the human team.

The chosen channel is a WhatsApp alert to the team's number(s) (e.g. Aditya).
Everything routes through `escalate()` so adding a phone call / Slack / SMS later
is a one-function change — the orchestrator and dashboard don't need to know how
the team is reached.
"""

from __future__ import annotations

from modules import config, database
from . import whatsapp_api

log = config.get_logger("wamanager.escalation")


def _alert_text(*, contact_name: str, wa_id: str, reason: str, question: str,
                qualification: dict) -> str:
    who = contact_name or wa_id
    lines = [
        "🚨 *WhatsApp lead needs you*",
        f"From: {who} (wa.me/{wa_id})",
        f"Reason: {reason}" if reason else "Reason: needs a human",
    ]
    if question:
        lines.append(f"Their message: “{question}”")
    if qualification:
        known = ", ".join(f"{k}: {v}" for k, v in qualification.items() if v)
        if known:
            lines.append(f"Known so far: {known}")
    lines.append("The assistant sent a holding reply. Reply from WhatsApp to take over.")
    return "\n".join(lines)


def escalate(
    *,
    conversation_id: int,
    wa_id: str,
    contact_name: str,
    reason: str,
    question: str,
    qualification: dict,
) -> dict:
    """Record the escalation and notify the team on WhatsApp.

    Returns {"escalation_id", "notified": bool, "channel", "detail"}.
    """
    esc_id = database.create_escalation(conversation_id, wa_id, reason, question)

    team = config.team_numbers()
    if not team:
        log.warning("Escalation %s created but TEAM_WHATSAPP_NUMBERS is empty — nobody notified.", esc_id)
        return {"escalation_id": esc_id, "notified": False, "channel": None,
                "detail": "No team numbers configured."}

    if not whatsapp_api.is_configured():
        log.warning("Escalation %s created but WhatsApp is not configured — nobody notified.", esc_id)
        return {"escalation_id": esc_id, "notified": False, "channel": None,
                "detail": "WhatsApp not configured."}

    text = _alert_text(
        contact_name=contact_name, wa_id=wa_id, reason=reason,
        question=question, qualification=qualification,
    )

    notified_any = False
    errors = []
    for num in team:
        try:
            resp = whatsapp_api.send_text(num, text)
            if "error" in resp:
                errors.append(f"{num}: {resp['error'].get('message', resp['error'])}")
            else:
                notified_any = True
        except Exception as e:  # pragma: no cover
            errors.append(f"{num}: {e}")

    database.mark_escalation(esc_id, "notified" if notified_any else "open", channel="whatsapp")
    detail = "Team notified on WhatsApp." if notified_any else ("; ".join(errors) or "Send failed.")
    log.info("Escalation %s — notified=%s (%s)", esc_id, notified_any, detail)
    return {"escalation_id": esc_id, "notified": notified_any, "channel": "whatsapp", "detail": detail}
