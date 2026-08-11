# WhatsApp Manager Agent 💬

A 24/7 AI first-responder for the WhatsApp leads that come from your Instagram/
Facebook ads. When a candidate pings your WhatsApp and the team isn't available, the
agent greets them like a human, answers from your business knowledge base, gently
qualifies, and drives them to book a quick intro call — escalating to the team when
it can't help.

Built with **Python + Gemini + SQLite** for the brain, and a **Node WhatsApp bot**
for the messaging layer. Live for **FutrBridge** (recruiting AI/software engineers).

---

## What it does

| # | Requirement | How it's delivered |
|---|-------------|--------------------|
| 1 | Monitor WhatsApp 24/7 | Always-on bot receives every message and replies in seconds |
| 2 | Start the conversation like a human | Gemini greeting + an editable persona/behavior playbook — sounds like a teammate, not a bot |
| 3 | Qualify + answer | Answers **only** from an editable knowledge base (roles, salary, visa, process, companies…); collects light details |
| 4 | Drive to a call | Shares the Calendly link and moves candidates toward the 15-min intro call |
| 5 | Escalate when stuck | Posts a formatted alert to the team's **WhatsApp group** (real phone number + context); team can reply to relay a message back |

Extras: understands **voice notes** (transcribed), ignores promos/spam/off-topic,
debounces message bursts, and pings **Telegram** if it ever logs out.

---

## Two WhatsApp routes

The AI brain is shared; only the WhatsApp layer differs.

| Route | Folder | Status |
|-------|--------|--------|
| **QR bot** (unofficial, Baileys) — links like WhatsApp Web, no Meta setup | `wa-bot/` + `agent_server.py` | ✅ **Active / deployed** |
| **Cloud API** (official, Meta) — ToS-safe, no session upkeep | `cloud_api/` | 🗄️ Archived alternative / migration target |

> ⚠️ The QR route uses an unofficial library — it violates WhatsApp's ToS and the
> number can be banned. It runs on a **spare number**. For a permanent line, migrate
> to the official Cloud API (see [DEVELOPMENT.md](DEVELOPMENT.md)).

---

## Quick start (no WhatsApp needed)

Test the whole brain with just a Gemini key — the **Simulator** runs the real agent:

```bash
pip install -r requirements.txt
cp .env.example .env          # set GEMINI_API_KEY
streamlit run app.py
```

In the app: **Seed demo business** → **Simulator** → chat as a candidate. Edit the
**Knowledge base** tab and watch answers change instantly (no restart).

## Run the live QR bot (two terminals)

```bash
python agent_server.py        # the brain, on 127.0.0.1:8100
cd wa-bot && npm install && npm start   # scan the QR it prints (spare number)
```

Then message the linked number. Full setup and the official-API path are in
**[Tutorial.md](Tutorial.md)**; architecture and internals are in
**[DEVELOPMENT.md](DEVELOPMENT.md)**.

---

## Configuration (`.env`)

| Key | For |
|-----|-----|
| `GEMINI_API_KEY` | the brain (required) |
| `GEMINI_MODEL` | `gemini-2.5-flash` default; prod uses `gemini-2.5-pro` |
| `TEAM_GROUP_NAME` | WhatsApp group the bot posts escalations to (default `AX Reply`) |
| `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` | logout alerts to a Telegram group |
| `ALERT_WEBHOOK_URL` | logout alerts to Discord/Slack (alternative) |
| `WHATSAPP_*` | official Cloud API route only |

The **business info, behavior, and examples are edited in the dashboard** (stored in
the DB) — no code change or redeploy needed. Prompt rules live in `modules/agent.py`.

---

## Deployment

Runs 24/7 on a VPS under pm2 (auto-restart + reboot-safe), binding only
`127.0.0.1:8100`. See **[DEVELOPMENT.md](DEVELOPMENT.md)** for the full server
setup, the `relink.sh` re-link flow, and Telegram logout alerts.
