"""
Email / ESP integration layer.

Produces ready-to-send drafts and (where credentials are supplied) pushes them
to the selected provider. Every adapter returns a uniform result dict:

    {"ok": bool, "message": str, "payload": dict}

Providers
---------
Gmail       SMTP send (app password) OR a .eml draft you can import.
Mailchimp   Creates a campaign + content via the Marketing API.
ConvertKit  Creates a broadcast via the v3 API.
Beehiiv     Creates a post draft via the Beehiiv API.

When credentials are missing, adapters return the exact API payload that WOULD
be sent, so the integration is transparent and testable without secrets.
"""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

from modules.exporters import to_html


def _result(ok: bool, message: str, payload: dict | None = None) -> dict:
    return {"ok": ok, "message": message, "payload": payload or {}}


# --------------------------------------------------------------------------- #
# Gmail
# --------------------------------------------------------------------------- #
def send_gmail(news: dict, creds: dict) -> dict:
    """Send via Gmail SMTP using an App Password, or return a draft .eml string."""
    html = to_html(news)
    subject = news.get("subject_line") or news.get("title", "Newsletter")
    sender = creds.get("gmail_address", "")
    app_password = creds.get("gmail_app_password", "")
    recipient = creds.get("recipient", sender)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender or "you@example.com"
    msg["To"] = recipient or "subscribers@example.com"
    msg.attach(MIMEText("View this newsletter in an HTML-capable client.", "plain"))
    msg.attach(MIMEText(html, "html"))

    if not (sender and app_password):
        return _result(
            False,
            "Gmail credentials not set — returning a ready-to-import .eml draft instead.",
            {"eml": msg.as_string(), "subject": subject},
        )
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
            server.login(sender, app_password)
            server.sendmail(msg["From"], [msg["To"]], msg.as_string())
        return _result(True, f"Sent via Gmail to {recipient}.", {"subject": subject})
    except Exception as exc:
        return _result(False, f"Gmail send failed: {exc}", {"eml": msg.as_string()})


# --------------------------------------------------------------------------- #
# Mailchimp
# --------------------------------------------------------------------------- #
def send_mailchimp(news: dict, creds: dict) -> dict:
    api_key = creds.get("mailchimp_api_key", "")
    list_id = creds.get("mailchimp_list_id", "")
    html = to_html(news)
    dc = api_key.split("-")[-1] if "-" in api_key else "us1"

    campaign_payload = {
        "type": "regular",
        "recipients": {"list_id": list_id},
        "settings": {
            "subject_line": news.get("subject_line", news.get("title", "")),
            "title": news.get("title", "Newsletter"),
            "from_name": creds.get("from_name", "Newsletter"),
            "reply_to": creds.get("reply_to", "hello@example.com"),
        },
    }
    if not (api_key and list_id):
        return _result(False, "Mailchimp credentials not set — showing the campaign payload.",
                       {"campaign": campaign_payload, "html": html})
    try:
        base = f"https://{dc}.api.mailchimp.com/3.0"
        auth = ("anystring", api_key)
        camp = requests.post(f"{base}/campaigns", json=campaign_payload, auth=auth, timeout=20)
        camp.raise_for_status()
        cid = camp.json()["id"]
        content = requests.put(f"{base}/campaigns/{cid}/content", json={"html": html}, auth=auth, timeout=20)
        content.raise_for_status()
        return _result(True, f"Mailchimp draft campaign created (id={cid}).", {"campaign_id": cid})
    except Exception as exc:
        return _result(False, f"Mailchimp request failed: {exc}", {"campaign": campaign_payload})


# --------------------------------------------------------------------------- #
# ConvertKit
# --------------------------------------------------------------------------- #
def send_convertkit(news: dict, creds: dict) -> dict:
    api_secret = creds.get("convertkit_api_secret", "")
    html = to_html(news)
    payload = {
        "api_secret": api_secret,
        "subject": news.get("subject_line", news.get("title", "")),
        "content": html,
        "description": news.get("title", "Newsletter"),
        "public": False,
    }
    if not api_secret:
        return _result(False, "ConvertKit API secret not set — showing the broadcast payload.",
                       {"broadcast": {k: v for k, v in payload.items() if k != "api_secret"}})
    try:
        resp = requests.post("https://api.convertkit.com/v3/broadcasts", json=payload, timeout=20)
        resp.raise_for_status()
        bid = resp.json().get("broadcast", {}).get("id")
        return _result(True, f"ConvertKit broadcast draft created (id={bid}).", {"broadcast_id": bid})
    except Exception as exc:
        return _result(False, f"ConvertKit request failed: {exc}", payload)


# --------------------------------------------------------------------------- #
# Beehiiv
# --------------------------------------------------------------------------- #
def send_beehiiv(news: dict, creds: dict) -> dict:
    api_key = creds.get("beehiiv_api_key", "")
    pub_id = creds.get("beehiiv_publication_id", "")
    html = to_html(news)
    payload = {
        "title": news.get("title", "Newsletter"),
        "subtitle": news.get("subject_line", ""),
        "body_content": html,
        "status": "draft",
    }
    if not (api_key and pub_id):
        return _result(False, "Beehiiv credentials not set — showing the post payload.",
                       {"post": payload})
    try:
        url = f"https://api.beehiiv.com/v2/publications/{pub_id}/posts"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        resp.raise_for_status()
        return _result(True, "Beehiiv draft post created.", {"response": resp.json()})
    except Exception as exc:
        return _result(False, f"Beehiiv request failed: {exc}", {"post": payload})


PROVIDERS = {
    "Gmail": send_gmail,
    "Mailchimp": send_mailchimp,
    "ConvertKit": send_convertkit,
    "Beehiiv": send_beehiiv,
}


def deliver(provider: str, news: dict, creds: dict) -> dict:
    fn = PROVIDERS.get(provider)
    if not fn:
        return _result(False, f"Unknown provider: {provider}")
    return fn(news, creds)
