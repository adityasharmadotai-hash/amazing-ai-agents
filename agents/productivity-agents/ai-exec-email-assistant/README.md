# 🤖 AI Executive Email Assistant

A production-ready, modular **Streamlit** application that lets you manage
**Gmail** and **Google Calendar** with natural language and voice — powered by
the **OpenAI API**.

---

## ✨ Features

| Area | What it does |
|------|--------------|
| **Gmail** | OAuth sign-in, read inbox/unread, Gmail-syntax search, filter by label, starred & important |
| **AI Assistant** | Inbox summary, daily digest, weekly summary, importance + follow-up detection (async batch triage), follow-up drafting |
| **Smart Drafting** | Generate drafts, context-aware replies from full threads, tone rewriting (Professional / Friendly / Executive / Short) |
| **Voice** | Record a command → Whisper transcription → intent routing → Gmail action, with optional spoken reply (TTS) |
| **Calendar** | Upcoming meetings, AI meeting-prep briefs using prior email history with attendees, talking points, open action items |
| **Daily Briefing** | One-click morning executive briefing (priorities, important mail, follow-ups, today's meetings) |
| **Analytics** | Inbox health score, response time, follow-up rate, volume trend, top contacts (Plotly charts) |
| **Export** | Any content → PDF, DOCX, or Markdown |

---

## 🧱 Architecture

```
ai-exec-email-assistant/
├── app.py                  # Home dashboard + auth gate
├── pages/                  # Streamlit multipage UI
│   ├── 1_Inbox.py
│   ├── 2_AI_Assistant.py
│   ├── 3_Drafting.py
│   ├── 4_Voice.py
│   ├── 5_Calendar.py
│   ├── 6_Briefing.py
│   ├── 7_Analytics.py
│   └── 8_Export.py
├── services/               # Business logic (one concern each)
│   ├── auth_service.py     # Google OAuth (web + installed flows)
│   ├── gmail_service.py    # Gmail read/search/draft/send
│   ├── calendar_service.py # Calendar events
│   ├── ai_service.py       # OpenAI: summaries, classify, draft, brief (sync + async)
│   ├── voice_service.py    # Whisper STT + OpenAI TTS
│   ├── briefing_service.py # Orchestrates the daily briefing
│   ├── analytics_service.py# Metric computation
│   └── export_service.py   # PDF / DOCX / Markdown
├── database/               # SQLite cache + repositories
│   ├── db.py
│   └── models.py
├── prompts/templates.py    # All LLM prompts in one place
├── utils/                  # Helpers, logging, UI components, auth gate
├── config/settings.py      # Env-driven configuration
├── docs/                   # OAUTH_SETUP.md, DEPLOYMENT.md
├── requirements.txt
├── .env.example
└── .streamlit/config.toml  # Dark theme
```

**Design principles:** modular services, environment-driven config, structured
logging, retry/backoff on transient API errors, async batch AI calls, and a
SQLite cache so the dashboard renders fast.

---

## 🚀 Quick start (local)

```bash
# 1. Clone & enter
cd ai-exec-email-assistant

# 2. Create a virtualenv
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env        # then edit .env with your keys

# 5. Run
streamlit run app.py
```

Open <http://localhost:8501>, click **Continue with Google**, grant access, and
you're in.

You need:
1. An **OpenAI API key** → <https://platform.openai.com/api-keys>
2. **Google OAuth credentials** → see [`docs/OAUTH_SETUP.md`](docs/OAUTH_SETUP.md)

---

## 🔐 Security notes

- `.env`, `.tokens/`, and the SQLite DB are git-ignored.
- Calendar access is **read-only**. Gmail scope allows reading and *creating
  drafts*; **emails are never sent automatically** — sending is always an
  explicit button press.
- Tokens are cached locally so you don't re-auth every session; sign out clears them.

---

## 🧪 Notes & extension ideas

- Swap `OPENAI_MODEL` / `OPENAI_REASONING_MODEL` in `.env` to trade cost vs. quality.
- Add scheduled briefings via a cron job that calls `BriefingService.generate()`.
- Extend `prompts/templates.py` to tune the assistant's voice.

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for Streamlit Community Cloud,
Docker, and VM deployment.

---

## 📄 License

MIT — use it, ship it, learn from it.
