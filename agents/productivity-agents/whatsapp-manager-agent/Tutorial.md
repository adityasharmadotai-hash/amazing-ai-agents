# Tutorial — WhatsApp Manager Agent, from zero to live

Get from an empty folder to an agent answering real WhatsApp leads 24/7.

- **Part A — Test in 5 minutes** (only a Gemini key needed)
- **Part B — Go live with the QR bot** (the active route — no Meta setup)
- **Part C — Run it 24/7 on a server**
- **Appendix — Official Cloud API route** (the ToS-safe alternative)

For architecture and internals, see **[DEVELOPMENT.md](DEVELOPMENT.md)**.

---

## Part A — Test the agent in 5 minutes (no WhatsApp yet)

The dashboard ships a **Simulator** that runs the *real* Gemini brain — you chat as
a candidate and it stores everything in the same DB the live agent uses. Best way to
shape your knowledge base before going live.

```bash
cd agents/productivity-agents/whatsapp-manager-agent
pip install -r requirements.txt
cp .env.example .env          # set GEMINI_API_KEY (from https://aistudio.google.com/apikey)
streamlit run app.py
```

In the app: sidebar **Seed demo business** → **Simulator** → chat as a candidate
(e.g. *"Hi, I'm a backend engineer — do you have roles?"*). Try an off-topic message
(it stays silent) and a booking ("can I book a call?"). Then open **Knowledge base**
and edit the profile/behavior — changes apply instantly.

---

## Part B — Go live with the QR bot

The active route links WhatsApp like **WhatsApp Web** (scan a QR). No Meta account,
no verification — it works in minutes.

> ⚠️ This uses an **unofficial** library (Baileys). It violates WhatsApp's ToS and
> the number **can be banned**. Use a **spare number**, never your main line.

### 1. Install the bot's Node deps
Requires **Node 18+** (the bot uses the built-in `fetch`).
```bash
cd wa-bot && npm install && cd ..
```

### 2. Start both processes (two terminals)
```bash
python agent_server.py        # terminal 1 — the brain, on 127.0.0.1:8100
cd wa-bot && npm start        # terminal 2 — prints a QR
```

### 3. Scan the QR
On the spare phone: **WhatsApp → Settings → Linked devices → Link a device** → scan
the QR from terminal 2. It prints `✅ Connected` and saves the session to
`wa-bot/auth/` (survives restarts — no re-scan).

### 4. Try it
Message the linked number from another phone. The agent (Alex) replies, drives
toward the intro call, and handles voice notes, bursts, and off-topic messages.

### Team escalations (WhatsApp group)
Create a WhatsApp **group named `AX Reply`** and **add the bot's number to it**. When
the agent can't help (booking issue, callback request, off-KB question), it posts a
formatted alert there with the candidate's real phone number. Your team can:
- **Reply to the alert** with an instruction → the bot relays it to that candidate, or
- Type **`Ax, tell <name> …`** to relay to a candidate by name.

(Set `TEAM_GROUP_NAME` in `.env` to use a different group name.)

### Re-linking
If the linked device ever logs out, run **`./relink.sh`** — it clears the session,
restarts the bot, and prints a fresh QR to scan.

---

## Part C — Run it 24/7 on a server

The bot must stay connected, so run it on an always-on machine (a small VPS is
ideal). It needs a **persistent disk** for `wa-bot/auth` (the WhatsApp session) and
`data/whatsapp.db`. Serverless (Vercel/Lambda) won't work.

```bash
# on the server (Node 18+ and Python 3.11+ available):
git clone <repo> && cd whatsapp-manager-agent
pip install -r requirements.txt
cd wa-bot && npm install && cd ..
cp .env.example .env          # set GEMINI_API_KEY etc.

npm i -g pm2
pm2 start ecosystem.config.cjs   # runs agent_server + wa-bot together
pm2 logs wa-bot                  # scan the QR once
pm2 save && pm2 startup          # restart-on-crash + survive reboots
```

**Logout alerts (Telegram):** create a bot via **@BotFather**, add it to a group,
and get the group's chat id, then set in `.env`:
```
TELEGRAM_BOT_TOKEN=123456:AA...
TELEGRAM_CHAT_ID=-1001234567890
```
`pm2 restart wa-bot` — now you're pinged in Telegram if the bot ever logs out (and
you just run `relink.sh`). Discord/Slack work too via `ALERT_WEBHOOK_URL`.

> **No sudo?** You can still deploy: install Node in user-space (a binary tarball or
> nvm), `pip install --user`, install pm2 into your user Node prefix, and use a
> crontab `@reboot pm2 resurrect` for boot persistence.

---

## Appendix — Official WhatsApp Cloud API (the ToS-safe route)

The durable production path: no QR, no re-links, no ban risk, deploy anywhere. Needs
a Meta app + WhatsApp Business number + **Business Verification** (2–10 business days)
+ a permanent token. Code lives in `cloud_api/`.

1. **Meta app:** developers.facebook.com → Create App (Business) → Add product
   **WhatsApp** → API Setup gives a temporary token, a **Phone Number ID**, and a
   test number.
2. **`.env`:** `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`,
   `WHATSAPP_VERIFY_TOKEN` (any secret you invent), `TEAM_WHATSAPP_NUMBERS`.
3. **Run the webhook** (from project root) and expose it over HTTPS:
   ```bash
   uvicorn cloud_api.webhook:app --host 0.0.0.0 --port 8000
   ngrok http 8000
   ```
4. In Meta → WhatsApp → **Configuration**, set the callback URL to
   `https://…/webhook` + your verify token, and **subscribe to `messages`**.
5. Message the test number — the same brain replies, now via the official API.

**Going fully live** needs Business Verification, publishing the app, and (usually) a
permanent System-User token. A number can be on the WhatsApp Business **App** *or*
the Cloud API — not both — so migrating a live number means removing it from the app
first (which loses that number's in-app chat history).
