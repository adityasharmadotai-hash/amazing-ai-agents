"""
webhook.py — the always-on brain (FastAPI).

Meta's WhatsApp Cloud API delivers every inbound message to this server as an
HTTP POST, 24/7. We verify it, hand it to the orchestrator, and return 200 fast
(the agent reply is sent via the Cloud API, not in the HTTP response).

Run locally:
    uvicorn webhook:app --host 0.0.0.0 --port 8000
Then expose it over HTTPS (ngrok / Cloudflare Tunnel / a deployed host) and paste
that URL + your WHATSAPP_VERIFY_TOKEN into Meta → App → WhatsApp → Configuration.

Health check:  GET /            → {"status": "ok", ...}
Verification:  GET /webhook     → Meta's hub.challenge handshake
Messages:      POST /webhook    → inbound messages
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response

from modules import config, conversation, database, knowledge
from cloud_api import whatsapp_api

log = config.get_logger("wamanager.webhook")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: make sure the DB + default knowledge base exist.
    database.init_db()
    knowledge.seed_defaults()
    log.info(
        "%s webhook up. WhatsApp configured=%s, Gemini configured=%s",
        config.APP_NAME, whatsapp_api.is_configured(),
        bool(config.get_secret("GEMINI_API_KEY")),
    )
    yield


app = FastAPI(title=config.APP_NAME, lifespan=lifespan)


@app.get("/")
def health() -> dict:
    return {
        "status": "ok",
        "app": config.APP_NAME,
        "whatsapp_configured": whatsapp_api.is_configured(),
        "counts": database.counts(),
    }


@app.get("/webhook")
def verify(request: Request):
    """Meta's one-time subscription handshake."""
    params = request.query_params
    challenge = whatsapp_api.verify_subscription(
        params.get("hub.mode", ""),
        params.get("hub.verify_token", ""),
        params.get("hub.challenge", ""),
    )
    if challenge is not None:
        return Response(content=challenge, media_type="text/plain")
    return Response(content="verification failed", status_code=403)


@app.post("/webhook")
async def inbound(request: Request):
    """Inbound message events from WhatsApp."""
    raw = await request.body()

    # Optional signature verification (enabled when WHATSAPP_APP_SECRET is set).
    app_secret = config.get_secret("WHATSAPP_APP_SECRET")
    if app_secret and not whatsapp_api.verify_signature(
        app_secret, raw, request.headers.get("X-Hub-Signature-256")
    ):
        log.warning("Rejected webhook with bad signature.")
        return Response(status_code=403)

    try:
        payload = await request.json()
    except Exception:
        return Response(status_code=200)  # ack anything unparseable so Meta stops retrying

    for msg in whatsapp_api.parse_inbound(payload):
        if not msg.get("wa_id"):
            continue
        try:
            result = conversation.handle_inbound(
                msg["wa_id"],
                msg.get("text", ""),
                profile_name=msg.get("profile_name"),
                message_id=msg.get("message_id"),
                live=True,
            )
            log.info(
                "Handled %s: status=%s escalated=%s delivery=%s",
                msg["wa_id"], result.get("status"),
                result.get("escalated"), result.get("delivery"),
            )
        except Exception:  # pragma: no cover - never let one bad message 500 the webhook
            log.exception("Error handling inbound message from %s", msg.get("wa_id"))

    # Always 200 quickly — Meta retries aggressively on non-200.
    return Response(status_code=200)


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("webhook:app", host="0.0.0.0", port=8000, reload=False)
