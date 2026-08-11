# WhatsApp Manager Agent — Development Guide

A 24/7 AI first-responder for WhatsApp leads (FutrBridge). It greets Instagram
lead-form candidates, answers from a knowledge base, qualifies lightly, and drives
them to book a 15-minute intro call — escalating to the team when needed.

There are **two independent WhatsApp layers** over one shared Python/Gemini brain:

| Route | Folder | Status | Notes |
|-------|--------|--------|-------|
| **QR bot** (unofficial, Baileys) | `wa-bot/` + `agent_server.py` | ✅ **Active / deployed** | Links like WhatsApp Web (scan a QR). No Meta setup. Violates WhatsApp ToS → ban risk; runs on a spare number. |
| **Cloud API** (official, Meta) | `cloud_api/` | 🗄️ Archived alternative | ToS-safe, no session fragility, deploy anywhere. Needs Meta app + Business Verification. The migration target for production. |

The **brain is shared** — swapping WhatsApp layers doesn't change the agent logic.

---

## Architecture (active QR route)

```
 WhatsApp  ──(linked device, QR)──►  wa-bot/index.js  (Node, Baileys)
                                        │  POST {wa_id, text, phone}
                                        ▼
                              agent_server.py  (stdlib HTTP, 127.0.0.1:8100)
                                        │  conversation.handle_inbound(live=False)
                                        ▼
                     modules/  (Gemini brain + SQLite)      escalations →
                     agent · conversation · knowledge          "AX Reply"
                     database · config                       WhatsApp group
```

- **`wa-bot/`** does all WhatsApp I/O: receive, debounce bursts, transcribe voice
  notes, send replies, post escalations to the **AX Reply** group, relay team
  commands, and alert Telegram on logout.
- **`agent_server.py`** is a tiny localhost bridge (no web framework) exposing
  `/reply`, `/transcribe`, `/command`, `/health`. It just calls the brain.
- **`modules/`** is the brain: one `agent.respond()` Gemini call decides the reply,
  what it collected, and whether to escalate. All state (KB, behavior, convos) is
  in SQLite (`data/whatsapp.db`).

---

## Project structure

```
whatsapp-manager-agent/
├── agent_server.py          # localhost HTTP bridge (the QR route's Python entry)
├── app.py                   # Streamlit dashboard (simulator, KB editor, convos)
├── ecosystem.config.cjs     # pm2 config (runs both processes on a server)
├── relink.sh                # re-link the WhatsApp session (clears + restarts + QR)
├── requirements.txt
├── .env.example             # all env vars, documented
├── modules/                 # the shared brain (QR route needs only these)
│   ├── agent.py             #   Gemini: respond(), transcribe_audio(), relay_command()
│   ├── conversation.py      #   orchestrator: handle_inbound() (idempotency→brain→persist)
│   ├── knowledge.py         #   business profile, behavior playbook, examples, questions
│   ├── database.py          #   SQLite (WAL): contacts, conversations, messages, escalations, settings
│   ├── config.py            #   constants, secrets (.env / st.secrets), logging, model id
│   └── demo_seed.py         #   sample business profile
├── wa-bot/                  # unofficial QR WhatsApp bot (Node / Baileys)
│   ├── index.js             #   the bot: I/O, debounce, voice, escalations, group commands, alerts
│   └── package.json
└── cloud_api/               # ARCHIVED official Cloud API route
    ├── webhook.py           #   FastAPI webhook (run: uvicorn cloud_api.webhook:app)
    ├── whatsapp_api.py      #   Meta Graph API client
    └── escalation.py        #   team-notify via Cloud API
```

Cloud API modules are imported **lazily** (only in `handle_inbound(live=True)`), so
the QR route has zero dependency on `cloud_api/`.

---

## Local development

**Prereqs:** Python 3.11+, Node 18+ (the bot uses global `fetch`), a Google AI
Studio key.

```bash
# 1. Python deps + config
pip install -r requirements.txt
cp .env.example .env          # set GEMINI_API_KEY at minimum

# 2. Node deps for the bot
cd wa-bot && npm install && cd ..
```

**Run the QR route (two terminals):**
```bash
python agent_server.py        # terminal 1 — the brain, on :8100
cd wa-bot && npm start        # terminal 2 — scan the QR it prints (spare number)
```

**Dashboard / simulator (no WhatsApp needed):** `streamlit run app.py` — the
**Simulator** tab runs the real brain against typed messages; **Knowledge base**
tab edits the profile / behavior / examples live (stored in the DB — no restart).

**Test the brain directly** (agent_server running):
```bash
curl -s localhost:8100/reply -H 'Content-Type: application/json' \
  -d '{"wa_id":"15551234","text":"hi, do you sponsor visas?","name":"Sam"}'
```

---

## The brain: where behavior lives

Everything the agent knows/does is **data in the DB `settings` table**, editable in
the dashboard's **Knowledge base** tab (no code change / restart):

- **`business_profile`** — facts it may state (about, roles, salary, visa, companies,
  `scheduling_link`, `knowledge_doc`, `jobs`, `escalate_topics`, `resume_email`).
- **`agent_config.behavior`** — the conversation-flow playbook (the biggest lever):
  lead with the call+link, answer factual questions directly, silence off-topic,
  wrap up after N questions, escalate on operational issues, etc.
- **`conversation_examples`** — few-shot examples that set the tone.
- **`qualifying_questions`** — currently empty (the intro call does the real qualifying).

Prompt assembly + the hard rules (never claim to be human, relevance gate, booking
intent vs. confirmed, etc.) live in `modules/agent.py`. Changing those **is** a code
change → restart `agent_server`. Data edits are picked up live.

---

## Environment variables (`.env`)

| Var | For | Notes |
|-----|-----|-------|
| `GEMINI_API_KEY` | brain | required |
| `GEMINI_MODEL` | brain | default `gemini-2.5-flash`; prod uses `gemini-2.5-pro` |
| `TEAM_WHATSAPP_NUMBERS` | escalation | fallback if the AX Reply group isn't found |
| `TEAM_GROUP_NAME` | wa-bot | escalation group name (default `AX Reply`) |
| `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` | wa-bot | logout alerts to a Telegram group |
| `ALERT_WEBHOOK_URL` | wa-bot | logout alerts to Discord/Slack/custom (alt to Telegram) |
| `WHATSAPP_*` | cloud_api only | tokens/ids for the official route |

The bot reads the shared `../.env` via dotenv; `config.py` loads it for Python.

---

## Production deployment (current)

Deployed on a VPS under an unprivileged user, **no sudo**, isolated from other apps:

- **Location:** `~/whatsapp-agent` (user home). Node 22 in `~/node22`; Python deps
  via `pip --user` (no venv — the OS `python3.12-venv` needs sudo).
- **Process manager:** pm2 (per-user). `wa-agent-server` = `python3 agent_server.py`,
  `wa-bot` = `node index.js` (cwd `wa-bot/`). `pm2 save` + crontab `@reboot pm2
  resurrect` = restart-on-crash + reboot persistence, all without sudo.
- **Binds only `127.0.0.1:8100`** — no public ports.

### Managing it on the server

The app runs under the **`claude-temp`** user (Node/pm2 live in its home), and **pm2
runs a separate daemon per user** — so root has no `pm2` and can't see these
processes. Manage them as `claude-temp`.

**One-off commands (straight from root):**
```bash
su - claude-temp -c 'pm2 list'                    # status
su - claude-temp -c 'pm2 logs wa-bot --lines 40'  # recent activity
su - claude-temp -c 'pm2 restart wa-bot'          # restart the bot
su - claude-temp -c 'pm2 restart all'             # restart both processes
```

**Interactive session:**
```bash
su - claude-temp
pm2 list
pm2 logs wa-bot        # live activity: 💬 in · 🤖 out · 📣 escalations
exit
```
> `pm2 restart wa-agent-server` after a Python/brain change; `pm2 restart wa-bot`
> after a bot-code change. Data edits (KB/behavior in the DB) need no restart.

### Re-linking WhatsApp (after a logout)

You're pinged in the **Telegram alert group** when the bot logs out. To re-link, run
the helper as `claude-temp` — it clears the session, restarts the bot, and prints a
fresh scannable QR:
```bash
su - claude-temp
~/whatsapp-agent/relink.sh          # full path — works from anywhere
# or, from inside the folder:
cd ~/whatsapp-agent && ./relink.sh  # note the ./  (a bare name isn't on PATH)
```

**Team ops in the AX Reply group:** escalations arrive formatted with the real
phone number. **Reply to an alert** (or type `Ax, tell <name> …`) and the bot
relays a composed message to that candidate.

---

## Migrating to the official Cloud API (future)

The durable production path — no QR, no re-links, no session fragility, deploy
anywhere. The brain is unchanged; only the WhatsApp layer swaps:

1. Meta app + WhatsApp number + **Business Verification** + permanent token.
2. Run `uvicorn cloud_api.webhook:app` (from project root), expose over HTTPS,
   register the webhook + `messages` field in Meta.
3. `cloud_api/webhook.py` calls `conversation.handle_inbound(live=True)`, which
   sends replies + escalations via `cloud_api/whatsapp_api.py` and
   `cloud_api/escalation.py`.

A number can be on the Business App **or** the Cloud API, not both — migrating a
live number means deregistering it from the app first (loses app chat history).
