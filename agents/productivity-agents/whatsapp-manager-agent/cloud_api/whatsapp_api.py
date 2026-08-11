"""
whatsapp_api.py — thin client for the Meta WhatsApp Business Cloud API.

Responsibilities
----------------
* verify the webhook subscription handshake (GET challenge)
* optionally verify inbound payload signatures (X-Hub-Signature-256)
* parse inbound webhook JSON into simple message dicts
* send outbound text messages (and simple template messages)

Docs: https://developers.facebook.com/docs/whatsapp/cloud-api
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

import requests

from modules import config

log = config.get_logger("wamanager.whatsapp")

_TIMEOUT = 20


def _base_url() -> str:
    phone_id = config.get_secret("WHATSAPP_PHONE_NUMBER_ID")
    return f"https://graph.facebook.com/{config.WHATSAPP_API_VERSION}/{phone_id}"


def is_configured() -> bool:
    return bool(
        config.get_secret("WHATSAPP_ACCESS_TOKEN")
        and config.get_secret("WHATSAPP_PHONE_NUMBER_ID")
    )


# ── webhook verification ──────────────────────────────────────────────────────
def verify_subscription(mode: str, token: str, challenge: str) -> str | None:
    """Return the challenge string if the verify token matches, else None.

    Meta calls this once (GET) when you save the webhook URL in the App dashboard.
    """
    expected = config.get_secret("WHATSAPP_VERIFY_TOKEN")
    if mode == "subscribe" and token and token == expected:
        log.info("Webhook verification succeeded.")
        return challenge
    log.warning("Webhook verification failed (mode=%s).", mode)
    return None


def verify_signature(app_secret: str, raw_body: bytes, signature_header: str | None) -> bool:
    """Validate X-Hub-Signature-256. If no app secret is configured, skip (return True)."""
    if not app_secret:
        return True  # signature checking is opt-in
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    provided = signature_header.split("=", 1)[1]
    return hmac.compare_digest(expected, provided)


# ── inbound parsing ───────────────────────────────────────────────────────────
def parse_inbound(payload: dict) -> list[dict]:
    """Flatten a webhook payload into a list of inbound message dicts.

    Each dict: {wa_id, profile_name, message_id, type, text, timestamp}.
    Non-text messages are surfaced with a placeholder text so the agent can
    still respond ("I can only read text right now…").
    """
    out: list[dict] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            contacts = {c.get("wa_id"): c for c in value.get("contacts", [])}
            for msg in value.get("messages", []):
                wa_id = msg.get("from")
                contact = contacts.get(wa_id, {})
                profile_name = (contact.get("profile") or {}).get("name")
                mtype = msg.get("type", "unknown")
                text = _extract_text(msg, mtype)
                out.append(
                    {
                        "wa_id": wa_id,
                        "profile_name": profile_name,
                        "message_id": msg.get("id"),
                        "type": mtype,
                        "text": text,
                        "timestamp": msg.get("timestamp"),
                    }
                )
    return out


def _extract_text(msg: dict, mtype: str) -> str:
    if mtype == "text":
        return (msg.get("text") or {}).get("body", "")
    if mtype == "button":
        return (msg.get("button") or {}).get("text", "")
    if mtype == "interactive":
        inter = msg.get("interactive") or {}
        if inter.get("type") == "button_reply":
            return (inter.get("button_reply") or {}).get("title", "")
        if inter.get("type") == "list_reply":
            return (inter.get("list_reply") or {}).get("title", "")
    # Media / location / contacts / etc. — we can't read the content.
    return f"[{mtype} message]"


# ── outbound ──────────────────────────────────────────────────────────────────
def send_text(to: str, body: str, preview_url: bool = False) -> dict:
    """Send a plain-text WhatsApp message. Returns the API response (or error)."""
    token = config.get_secret("WHATSAPP_ACCESS_TOKEN")
    if not token or not config.get_secret("WHATSAPP_PHONE_NUMBER_ID"):
        raise RuntimeError("WhatsApp is not configured (missing token or phone number id).")

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": preview_url, "body": body[:4096]},
    }
    resp = requests.post(
        f"{_base_url()}/messages",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=_TIMEOUT,
    )
    data = _safe_json(resp)
    if resp.status_code >= 400:
        log.error("send_text failed (%s): %s", resp.status_code, data)
    return data


def send_template(to: str, template_name: str, language: str = "en_US",
                  components: list[dict] | None = None) -> dict:
    """Send a pre-approved template message (needed to open a conversation with a
    user outside the 24h customer-service window)."""
    token = config.get_secret("WHATSAPP_ACCESS_TOKEN")
    payload: dict[str, Any] = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {"name": template_name, "language": {"code": language}},
    }
    if components:
        payload["template"]["components"] = components
    resp = requests.post(
        f"{_base_url()}/messages",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=_TIMEOUT,
    )
    data = _safe_json(resp)
    if resp.status_code >= 400:
        log.error("send_template failed (%s): %s", resp.status_code, data)
    return data


def _safe_json(resp: requests.Response) -> dict:
    try:
        return resp.json()
    except Exception:
        return {"status_code": resp.status_code, "text": resp.text}
