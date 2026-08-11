"""
conversation.py — the orchestrator.

`handle_inbound()` is the single entry point for one customer message. It runs
the same flow whether the message arrived from the live WhatsApp webhook or from
the dashboard's simulator:

    idempotency → persist inbound → (human-takeover check) → ask Gemini →
    update qualification → escalate if needed → send + persist the reply

`live=True` actually sends over WhatsApp and pings the team; `live=False`
(simulator) does everything except touch the WhatsApp API, so you can rehearse
the whole agent with no phone number connected.
"""

from __future__ import annotations

import re

from . import agent, config, database, knowledge

# The official Cloud API modules (cloud_api/) are imported lazily, only when
# live=True — the QR-bot route (live=False) has no dependency on them.

log = config.get_logger("wamanager.conversation")

# Grab a real phone number the candidate typed (e.g. the lead-form line
# "phone_number: +16614548052"). Requires a leading '+' so it never matches the
# 15-digit WhatsApp LID, which has no '+'.
_PHONE_RE = re.compile(r"\+\d[\d\s().\-]{8,}\d")


def _extract_phone(text: str) -> str:
    m = _PHONE_RE.search(text or "")
    if not m:
        return ""
    digits = re.sub(r"\D", "", m.group(0))
    return "+" + digits if 10 <= len(digits) <= 15 else ""


def handle_inbound(
    wa_id: str,
    text: str,
    *,
    profile_name: str | None = None,
    message_id: str | None = None,
    phone_hint: str | None = None,
    live: bool = True,
) -> dict:
    """Process one inbound message end-to-end.

    Returns an action dict: {status, reply, escalated, escalation, conversation_id, stage}.
    """
    # 1) Idempotency — WhatsApp re-delivers webhooks; never double-process.
    if message_id and database.message_exists(message_id):
        log.info("Duplicate webhook for message %s — skipping.", message_id)
        return {"status": "duplicate", "reply": None, "escalated": False,
                "escalation": None, "conversation_id": None, "stage": None}

    # 2) Contact + conversation.
    database.upsert_contact(wa_id, profile_name=profile_name)
    conv = database.get_or_create_conversation(wa_id)
    conv_id = conv["id"]
    is_first_contact = len(database.get_messages(conv_id, limit=1)) == 0

    database.add_message(conv_id, wa_id, "in", "customer", text, wa_message_id=message_id)

    # 3) Human takeover — if a teammate disabled the agent for this thread, stay quiet.
    if not conv.get("agent_enabled", True):
        log.info("Agent disabled for conversation %s — recording only.", conv_id)
        return {"status": "human_handling", "reply": None, "escalated": False,
                "escalation": None, "conversation_id": conv_id, "stage": conv.get("stage")}

    # 4) Gather context and ask Gemini for the next action.
    profile = knowledge.get_profile()
    questions = knowledge.get_questions()
    cfg = knowledge.get_config()
    examples = knowledge.get_examples()
    collected = dict(conv.get("qualification") or {})
    # WhatsApp already gives us the sender's profile name — treat it as known so
    # the agent greets them by name instead of asking "what's your name?".
    if profile_name and not collected.get("name"):
        collected["name"] = profile_name
    # Capture the candidate's real phone number (from the lead form or the WhatsApp
    # key hint) so the team gets a dialable number — NOT WhatsApp's internal LID.
    if not collected.get("phone"):
        ph = _extract_phone(text) or (phone_hint or "")
        if ph:
            collected["phone"] = ph
    # Remember once they've booked so we never push the calendar link again.
    low = text.lower()
    if any(w in low for w in ("booked", "i've booked", "just booked", "scheduled the call",
                              "scheduled a call", "booked a slot", "booked the call")):
        collected["booked"] = True

    # Auto-wrap-up: after too many candidate messages without booking, close it out
    # once (a final friendly nudge), then stay quiet.
    all_msgs = database.get_messages(conv_id)
    inbound_count = sum(1 for m in all_msgs if m["direction"] == "in")
    # Space out the calendar link — skip it if the previous reply already had it.
    sched_link = (profile.get("scheduling_link") or "").strip()
    last_out = next((m for m in reversed(all_msgs) if m["direction"] == "out"), None)
    link_recently_sent = bool(sched_link and last_out and sched_link in (last_out.get("body") or ""))
    limit = int(cfg.get("max_questions_before_handoff", 6))
    wrap_up = (
        not collected.get("booked")
        and not collected.get("ended")
        and inbound_count > limit
    )
    if wrap_up:
        collected["ended"] = True  # this turn is the final wrap-up message

    history = database.get_history_for_model(conv_id, config.HISTORY_TURNS)

    try:
        action = agent.respond(
            profile=profile,
            questions=questions,
            config_cfg=cfg,
            collected=collected,
            history=history,
            user_message=text,
            is_first_contact=is_first_contact,
            examples=examples,
            wrap_up=wrap_up,
            link_recently_sent=link_recently_sent,
        )
    except agent.AgentError as e:
        log.error("Agent error on conversation %s: %s", conv_id, e)
        action = {
            "reply": "Thanks for your message! Someone from our team will get back to you very shortly. 🙏",
            "collected": {}, "answered": False, "confidence": 0,
            "escalate": True, "escalation_reason": f"Agent error: {e}", "stage": "escalated",
        }

    # 5) Merge any newly collected qualification details.
    new_bits = {k: v for k, v in (action.get("collected") or {}).items() if v}
    if new_bits:
        collected.update(new_bits)

    reply_text = (action.get("reply") or "").strip()
    escalate = bool(action.get("escalate"))
    stage = "escalated" if escalate else action.get("stage", "qualifying")

    database.update_conversation(
        conv_id,
        stage=stage,
        status="escalated" if escalate else "active",
        qualification=collected,
    )

    # 6) Escalate (record always; notify team only when live).
    escalation_result = None
    if escalate:
        contact = database.get_contact(wa_id) or {}
        if live:
            from cloud_api import escalation  # official Cloud API route only
            escalation_result = escalation.escalate(
                conversation_id=conv_id,
                wa_id=wa_id,
                contact_name=collected.get("name") or contact.get("profile_name") or "",
                reason=action.get("escalation_reason", ""),
                question=text,
                qualification=collected,
            )
        else:
            esc_id = database.create_escalation(
                conv_id, wa_id, action.get("escalation_reason", ""), text
            )
            escalation_result = {"escalation_id": esc_id, "notified": False,
                                 "channel": "simulator", "detail": "Simulated — team not pinged."}

    # 7) Deliver + persist the reply.
    delivery = "not_sent"
    if reply_text:
        if live:
            from cloud_api import whatsapp_api  # official Cloud API route only
            _wa_ok = whatsapp_api.is_configured()
        else:
            _wa_ok = False
        if _wa_ok:
            try:
                resp = whatsapp_api.send_text(wa_id, reply_text)
                delivery = "error" if "error" in resp else "sent"
            except Exception as e:  # pragma: no cover
                log.error("Failed to send reply on conversation %s: %s", conv_id, e)
                delivery = "error"
        elif not live:
            delivery = "simulated"
        database.add_message(conv_id, wa_id, "out", "agent", reply_text)

    return {
        "status": "ok",
        "reply": reply_text,
        "delivery": delivery,
        "escalated": escalate,
        "escalation": escalation_result,
        "escalation_reason": action.get("escalation_reason", ""),
        "confidence": action.get("confidence"),
        "collected": collected,
        "conversation_id": conv_id,
        "stage": stage,
    }


def send_manual_reply(conv_id: int, text: str, *, live: bool = True) -> dict:
    """A human teammate sends a message from the dashboard. Disables the agent for
    this thread so it stops auto-replying, then delivers the message."""
    conv = database.get_conversation(conv_id)
    if not conv:
        return {"status": "no_such_conversation"}
    wa_id = conv["wa_id"]
    database.update_conversation(conv_id, agent_enabled=False, status="active")

    delivery = "simulated"
    if live:
        from cloud_api import whatsapp_api  # official Cloud API route only
        if whatsapp_api.is_configured():
            try:
                resp = whatsapp_api.send_text(wa_id, text)
                delivery = "error" if "error" in resp else "sent"
            except Exception as e:  # pragma: no cover
                delivery = "error"
                log.error("Manual reply failed on %s: %s", conv_id, e)
    database.add_message(conv_id, wa_id, "out", "human", text)
    return {"status": "ok", "delivery": delivery}
