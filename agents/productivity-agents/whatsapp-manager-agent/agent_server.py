"""
agent_server.py — a tiny localhost bridge between the Node WhatsApp bot and the
existing Python/Gemini FutrBridge brain.

The unofficial QR bot (wa-bot/, Baileys) does the WhatsApp I/O; whenever a message
comes in it POSTs here, we run the SAME `conversation.handle_inbound` the Cloud-API
path uses (live=False, so this layer never calls Meta — the Node bot sends the
reply itself), and we return the reply text + whether to escalate.

Zero web-framework dependencies (uses the stdlib http.server) so it doesn't touch
the FastAPI/Starlette stack.

Run:  python agent_server.py       # listens on http://127.0.0.1:8100
"""

from __future__ import annotations

import base64
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from modules import agent, config, conversation, database, knowledge

log = config.get_logger("wamanager.agent_server")

HOST = "127.0.0.1"
PORT = 8100


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        if self.path in ("/", "/health"):
            self._send(200, {
                "status": "ok",
                "app": config.APP_NAME,
                "business": knowledge.get_profile().get("business_name"),
                "gemini_configured": bool(config.get_secret("GEMINI_API_KEY")),
                "team_numbers": config.team_numbers(),
                "counts": database.counts(),
            })
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):  # noqa: N802
        if self.path not in ("/reply", "/transcribe", "/command"):
            self._send(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length) or b"{}")
        except Exception as e:
            self._send(400, {"error": f"bad json: {e}"})
            return

        # A teammate's instruction from the group ("Ax, tell <name> …") → identify
        # the candidate and compose the message for the bot to relay.
        if self.path == "/command":
            try:
                cmd = str(data.get("text", "")).strip()
                target = None
                if data.get("target_wa_id"):
                    target = {"wa_id": str(data["target_wa_id"]), "name": data.get("target_name") or ""}
                cands = database.recent_candidates(limit=30)
                out = agent.relay_command(
                    cmd, cands, knowledge.get_profile(), knowledge.get_config(), target=target
                )
                self._send(200, out)
            except Exception as e:  # pragma: no cover
                log.exception("command error")
                self._send(500, {"found": False, "note": f"error: {e}"})
            return

        # Voice notes → transcribe with Gemini, return the text for the bot to
        # feed back through /reply.
        if self.path == "/transcribe":
            try:
                audio = base64.b64decode(data.get("audio_b64", ""))
                mime = data.get("mime") or "audio/ogg"
                text = agent.transcribe_audio(audio, mime) if audio else ""
                self._send(200, {"text": text})
            except Exception as e:  # pragma: no cover
                log.exception("transcription error")
                self._send(500, {"error": str(e), "text": ""})
            return

        wa_id = str(data.get("wa_id", "")).strip()
        text = str(data.get("text", "")).strip()
        name = data.get("name")
        if not wa_id or not text:
            self._send(400, {"error": "wa_id and text are required"})
            return

        try:
            # live=False → run the full agent + persist, but don't call the Meta API.
            # The Node bot is responsible for actually delivering the reply.
            phone = data.get("phone") or None
            result = conversation.handle_inbound(
                wa_id, text, profile_name=name, phone_hint=phone, live=False
            )
            self._send(200, {
                "reply": result.get("reply"),
                "escalate": bool(result.get("escalated")),
                "escalation_reason": result.get("escalation_reason", ""),
                "collected": result.get("collected", {}),
                "stage": result.get("stage"),
                "status": result.get("status"),
                "team_numbers": config.team_numbers(),
            })
        except Exception as e:  # pragma: no cover
            log.exception("agent error for %s", wa_id)
            self._send(500, {"error": str(e),
                             "reply": "Thanks for your message! Someone from our team will get back to you shortly.",
                             "escalate": True})

    def log_message(self, *args):  # silence default noisy logging
        return


def main() -> None:
    database.init_db()
    knowledge.seed_defaults()
    biz = knowledge.get_profile().get("business_name")
    gem = bool(config.get_secret("GEMINI_API_KEY"))
    log.info("Agent server for '%s' on http://%s:%d  (Gemini configured=%s)", biz, HOST, PORT, gem)
    if not gem:
        log.warning("GEMINI_API_KEY not set — replies will fall back to a holding message.")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
