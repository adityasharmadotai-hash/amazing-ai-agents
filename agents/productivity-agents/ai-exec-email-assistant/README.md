<div align="center">

### ⭐ Support & Connect

[![Star the repo](https://img.shields.io/badge/⭐_Star_the_repo-amazing--ai--agents-FFD43B?style=for-the-badge&logo=github&logoColor=black)](https://github.com/adityasharmadotai-hash/amazing-ai-agents)

💼 **Follow on LinkedIn:** [aditya-hicounselor](https://www.linkedin.com/in/aditya-hicounselor/) &nbsp;•&nbsp; 📺 **Subscribe on YouTube:** [@adityasharma](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)

🚀 **Looking for jobs at top AI companies in the U.S.?** [**Apply here →**](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)

</div>

---

# 🤖 AI Executive Email Assistant

> A voice-first, AI-powered command center for Gmail — triage, draft, brief, and analyze your inbox by simply speaking, powered by the OpenAI API.

---

## 📖 Overview

Executives and busy professionals lose hours every day to email: reading, sorting, deciding what matters, and writing replies. **AI Executive Email Assistant** turns that grind into a conversation.

It connects securely to your Gmail, uses large language models to understand and summarize your inbox, and lets you **run the entire workflow with your voice** — "summarize my unread mail," "draft a reply to Priya," "give me my morning briefing." When typing is easier, every feature is also available through a clean, modern dashboard.

**The problem it solves:** email triage is repetitive, high-volume, and cognitively draining. This app offloads the reading, prioritizing, and first-draft writing to an AI assistant so you spend your attention only where it counts.

---

## ✨ Features

| Area | What it does |
|------|--------------|
| 🎤 **Voice Command (primary)** | Speak a command → Whisper transcribes it → an LLM routes it to the right action → the assistant acts on Gmail and can speak the result back |
| 📥 **Inbox** | OAuth sign-in, read inbox & unread, full Gmail-syntax search, filter by label, view starred & important mail |
| 🤖 **AI Assistant** | Inbox summary, daily digest, weekly review, and concurrent AI triage that flags importance and follow-ups |
| ✍️ **Smart Drafting** | Generate drafts from a prompt, context-aware replies from a full thread, and one-click tone rewriting (Professional / Friendly / Executive / Short) |
| 📋 **Daily Briefing** | A one-click morning executive briefing: top priorities, important mail, and follow-ups needed |
| 📊 **Analytics** | Inbox health score, follow-up rate, average response time, 14-day volume trend, and top contacts (Plotly charts) |
| 📤 **Export** | Turn any briefing, draft, or text into a **PDF, DOCX, or Markdown** file |
| ⚙️ **In-app Settings** | Configure API keys, models, and personalization from the UI — changes apply instantly, no redeploy |

> 🔒 **Safety by design:** the assistant can *create* drafts but **never sends email automatically** — sending is always an explicit button press.

---

## 🔧 How It Works

The app follows a clean layered flow from your voice or click all the way to Gmail and back:

```
        ┌──────────────────────────────────────────────────────────┐
        │                     YOU (voice or UI)                     │
        └───────────────────────────┬───────────────────────────────┘
                                     │
                 🎤 speak            │            🖱  click
                                     ▼
        ┌──────────────────────────────────────────────────────────┐
        │              Streamlit UI  (app.py + pages/)              │
        └───────────────────────────┬───────────────────────────────┘
                                     │
                                     ▼
        ┌──────────────────────────────────────────────────────────┐
        │                     Services layer                        │
        │                                                           │
        │   voice_service ──▶ Whisper (speech → text)               │
        │        │                                                  │
        │        ▼                                                  │
        │   ai_service ─────▶ OpenAI  (route intent, summarize,     │
        │        │             classify, draft, brief)              │
        │        ▼                                                  │
        │   gmail_service ──▶ Gmail API (read / search / draft)     │
        │        │                                                  │
        │        ▼                                                  │
        │   analytics / briefing / export services                 │
        └───────────────────────────┬───────────────────────────────┘
                                     │
                                     ▼
        ┌──────────────────────────────────────────────────────────┐
        │            SQLite cache  (fast dashboards)                │
        └──────────────────────────────────────────────────────────┘
```

**In plain English:** you speak or click → the UI hands the request to a service → the voice service turns speech into text → the AI service decides what you meant and does the language work → the Gmail service performs the action → results are cached in SQLite so the dashboard stays fast.

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|------------|
| **Language** | Python 3.10+ |
| **Web / UI** | Streamlit (multipage app, custom dark theme) |
| **AI models** | OpenAI — `gpt-4o-mini` / `gpt-4o` (text), `whisper-1` (speech-to-text), `gpt-4o-mini-tts` (text-to-speech) |
| **Email** | Gmail API via `google-api-python-client` |
| **Auth** | Google OAuth 2.0 (`google-auth-oauthlib`, PKCE flow) |
| **Data & charts** | SQLite (cache), pandas, Plotly |
| **Export** | ReportLab (PDF), python-docx (DOCX) |
| **Config** | python-dotenv + an in-app settings layer |

---

## 📁 File Structure

```
ai-exec-email-assistant/
├── app.py                      # Home dashboard + auth gate (entry point)
├── pages/                      # Streamlit multipage UI
│   ├── 1_Inbox.py              # Read / search / filter mail
│   ├── 2_AI_Assistant.py       # Summaries, digests, triage
│   ├── 3_Drafting.py           # Draft, reply, rewrite tone
│   ├── 4_Voice.py              # 🎤 Voice command center (primary)
│   ├── 6_Briefing.py           # One-click daily briefing
│   ├── 7_Analytics.py          # Charts & inbox metrics
│   ├── 8_Export.py             # PDF / DOCX / Markdown export
│   └── 9_Settings.py           # In-app configuration
├── services/                   # Business logic (one concern each)
│   ├── auth_service.py         # Google OAuth (PKCE web flow)
│   ├── gmail_service.py        # Gmail read / search / draft / send
│   ├── ai_service.py           # OpenAI: summarize, classify, draft, brief
│   ├── voice_service.py        # Whisper STT + OpenAI TTS
│   ├── briefing_service.py     # Orchestrates the daily briefing
│   ├── analytics_service.py    # Metric computation
│   └── export_service.py       # PDF / DOCX / Markdown generation
├── database/
│   ├── db.py                   # SQLite connection + schema
│   └── models.py               # Email dataclass + repository functions
├── prompts/
│   └── templates.py            # All LLM prompts in one place
├── utils/
│   ├── ui.py                   # Auth gate, service factory, sidebar
│   ├── theme.py                # Centralized design system / CSS
│   ├── components.py           # Reusable render components
│   ├── helpers.py              # Async, retry, parsing helpers
│   └── logging_config.py       # Logging setup
├── config/
│   └── settings.py             # Env-driven settings + runtime overrides
├── docs/
│   ├── OAUTH_SETUP.md          # Google OAuth setup guide
│   └── DEPLOYMENT.md           # Deployment guide
├── .streamlit/config.toml      # Native theme + server config
├── requirements.txt
└── .env.example                # Copy to .env and fill in
```

---

## 🚀 Getting Started

### Prerequisites

- Python **3.10 or newer**
- An **OpenAI API key** — <https://platform.openai.com/api-keys>
- **Google OAuth credentials** for the Gmail API (see [`docs/OAUTH_SETUP.md`](docs/OAUTH_SETUP.md))

### 1. Clone the repository

```bash
git clone https://github.com/adityasharmadotai-hash/amazing-ai-agents.git
cd amazing-ai-agents/agents/productivity-agents/ai-exec-email-assistant
```

### 2. Create a virtual environment & install dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure your secrets

```bash
cp .env.example .env
```

Open `.env` and fill in your `OPENAI_API_KEY`, `GOOGLE_CLIENT_ID`, and `GOOGLE_CLIENT_SECRET`.
(You can also skip this and enter everything in the in-app **⚙️ Settings** page after launching.)

### 4. Run it

```bash
streamlit run app.py
```

Open <http://localhost:8501>, click **Continue with Google**, and you're in. 🎉

---

## ☁️ Deployment (Streamlit Community Cloud)

1. Push your fork to GitHub (`.gitignore` already excludes secrets).
2. Go to <https://share.streamlit.io> → **New app**, select your repo, and set the **Main file path** to this project's `app.py`.
3. In **Advanced settings → Secrets**, paste your config in TOML form:

   ```toml
   OPENAI_API_KEY = "sk-..."
   GOOGLE_CLIENT_ID = "xxxx.apps.googleusercontent.com"
   GOOGLE_CLIENT_SECRET = "GOCSPX-..."
   GOOGLE_REDIRECT_URI = "https://your-app.streamlit.app/"
   ```

4. Add that exact `GOOGLE_REDIRECT_URI` (trailing slash included) as an **Authorized redirect URI** in your Google Cloud OAuth client.
5. Deploy. Full details — including Docker and VM options — are in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

> **Note:** Streamlit Community Cloud has an ephemeral filesystem, so the saved login resets when the app restarts and you'll re-authenticate. That's expected on the free tier.

---

## 📚 Step-by-Step Tutorial

New to this kind of project? Follow the complete beginner-friendly build:

👉 **[Full Tutorial — TUTORIAL.md](https://github.com/adityasharmadotai-hash/docs-reader-rag-agent/blob/main/TUTORIAL.md)**

---

## 🤝 Contributing

Contributions are welcome and appreciated!

1. **Fork** the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. **Commit** your changes: `git commit -m "Add your feature"`
4. **Push** the branch: `git push origin feature/your-feature`
5. Open a **Pull Request** describing what you changed and why

Please keep changes focused, add a short description, and make sure the app still runs (`streamlit run app.py`) before submitting.

---

## 📄 License

Released under the **MIT License** — free to use, modify, and distribute. See the `LICENSE` file for details.

---

<div align="center">

If this project helped you, please consider giving it a ⭐ — it really helps!

[![Star](https://img.shields.io/badge/⭐_Star_on_GitHub-amazing--ai--agents-FFD43B?style=flat-square&logo=github&logoColor=black)](https://github.com/adityasharmadotai-hash/amazing-ai-agents)

</div>
