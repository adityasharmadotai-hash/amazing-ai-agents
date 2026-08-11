# wa-bot — unofficial QR WhatsApp auto-reply (no Meta / no Facebook)

Links a WhatsApp number as a **device** (scan a QR, like WhatsApp Web) and
auto-replies to incoming messages using the **same FutrBridge Gemini brain** as the
rest of this project. No Meta app, no Business Verification, works today.

> ## ⚠️ Read this first
> This uses an **unofficial** library (Baileys) over WhatsApp's linked-device
> protocol. It **violates WhatsApp's Terms of Service**, and Meta can
> **permanently ban** the linked number — you'd lose the number *and* its
> contacts. **Test on a spare number.** Do not point it at your main business
> line (650‑623‑2627) until you're comfortable with the risk.

## How it fits together

```
WhatsApp  ──QR/linked device──►  wa-bot (Node/Baileys)
                                     │  POST {wa_id, text}
                                     ▼
                          agent_server.py  (Python, :8100)
                                     │  reuses conversation.handle_inbound
                                     ▼
                        FutrBridge Gemini brain  +  SQLite (shared with dashboard)
```

The Node bot only does WhatsApp I/O. All the intelligence (greeting, answering
from the knowledge base, qualifying, escalation) is the existing Python agent —
so anything you edit in the dashboard's **Knowledge base** tab applies here too,
and every conversation still shows up in the dashboard.

## Run it (two terminals)

**Terminal 1 — the brain** (from the project root, needs `GEMINI_API_KEY` in `.env`):
```bash
python agent_server.py
```

**Terminal 2 — the WhatsApp bot** (from this `wa-bot/` folder):
```bash
npm install
npm start
```

Then on the phone with your **spare** number: **WhatsApp → Settings → Linked
devices → Link a device → scan the QR** printed in Terminal 2.

Once it says `✅ Connected`, message that number from any other phone — the agent
replies as Alex from FutrBridge. If it can't answer, it also pings the numbers in
`TEAM_WHATSAPP_NUMBERS`.

## Notes
- The `auth/` folder stores the linked-session credentials — it's gitignored;
  keep it private. Delete it to force a fresh QR / re-link.
- Groups and status broadcasts are ignored; it only replies to 1:1 chats.
- It won't auto-reply to your own team numbers (from `TEAM_WHATSAPP_NUMBERS`).
- Point it at a different agent host with `AGENT_URL=http://host:8100 npm start`.
