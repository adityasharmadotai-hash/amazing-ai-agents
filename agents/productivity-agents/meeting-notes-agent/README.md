# 🎙️ AI Meeting Notes Agent

> Upload any meeting recording → get instant summaries, action items, decisions, tasks by person, and a follow-up email draft — powered by OpenAI Whisper + GPT-4o.

---

<div align="center">

⭐ **[Star the repo](https://github.com/adityasharmadotai-hash)** &nbsp;·&nbsp;
🌐 **[adityasharma.ai](https://www.adityasharma.ai)** &nbsp;·&nbsp;
💼 **[LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)** &nbsp;·&nbsp;
📺 **[YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)** &nbsp;·&nbsp;
🚀 **[AI Jobs USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

</div>

---

**👉 STEP-BY-STEP TUTORIAL: [Tutorial.md](./Tutorial.md)**

---

## Overview

Stop taking meeting notes manually. Upload your Zoom, Teams, or Google Meet recording — Whisper AI transcribes it and GPT-4o extracts everything you need in under 60 seconds.

---

## Features

| Feature | Description |
|---------|-------------|
| 🎙️ **Speech-to-Text** | OpenAI Whisper — supports MP3, WAV, MP4, M4A, WebM, OGG |
| 📝 **AI Summary** | 3-5 sentence executive summary with key topics |
| ✅ **Action Items** | Task, owner, deadline, and priority for each item |
| ⚖️ **Decisions** | Every decision with context and owner |
| 👤 **Tasks by Person** | Individual task lists per attendee |
| ✉️ **Follow-up Email** | Professional email draft ready to send |
| 💬 **Meeting Q&A** | Ask any question about the meeting content |
| 🔍 **Search** | Find past meetings by title |
| 📊 **Analytics** | Sentiment trends, duration distribution, activity charts |
| 📥 **Export** | PDF, DOCX, and Markdown export |
| 🗃️ **Supabase** | Persistent cloud storage (optional) |

---

## How It Works

```
Upload MP3/WAV/MP4
      ↓
transcriber.py → OpenAI Whisper API
Speech → Text transcript
      ↓
agent.py → GPT-4o
Transcript → Structured JSON (summary, actions, decisions...)
      ↓
database.py → Supabase (optional)
Save permanently
      ↓
exporter.py → PDF / DOCX / Markdown
Download your notes
```

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Core language |
| Streamlit | Web UI |
| OpenAI Whisper | Speech-to-text transcription |
| OpenAI GPT-4o | Meeting analysis and content generation |
| Supabase | Persistent PostgreSQL database (optional) |
| ReportLab | PDF export |
| python-docx | DOCX export |
| Plotly | Analytics charts |

---

## Project Structure

```
meeting-notes-agent/
├── app.py                   # Main Streamlit app — 7 pages
├── modules/
│   ├── __init__.py
│   ├── transcriber.py       # Audio/video → text via Whisper API
│   ├── agent.py             # GPT-4o analysis calls
│   ├── database.py          # Supabase CRUD + analytics
│   └── exporter.py          # PDF, DOCX, Markdown export
├── supabase_schema.sql      # Run once in Supabase SQL Editor
├── .streamlit/
│   └── config.toml          # Theme + server settings
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── Tutorial.md
```

---

## Getting Started

### 1. Clone & install

```bash
git clone https://github.com/adityasharmadotai-hash/amazing-ai-agents.git
cd amazing-ai-agents/agents/meeting-notes-agent
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set credentials

```bash
cp .env.example .env
# Edit .env — add OPENAI_API_KEY (required) and Supabase keys (optional)
```

### 3. Run

```bash
streamlit run app.py
```

---

## Deploy to Streamlit Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Set main file: `app.py`
4. Add secrets (TOML format with quotes):

```toml
OPENAI_API_KEY = "sk-your-openai-key"
SUPABASE_URL   = "https://your-project.supabase.co"
SUPABASE_KEY   = "your-anon-key"
```

5. Deploy ✅

> Supabase is **optional**. The app works without it — history, search, and analytics are disabled, all other features work.

---

## Supabase Setup (Optional)

1. [supabase.com](https://supabase.com) → New Project (free)
2. SQL Editor → New Query → paste `supabase_schema.sql` → Run ▶
3. Project Settings → API → copy URL and anon key

---

## Common Errors & Fixes

| Error | Fix |
|-------|-----|
| `audio_too_short` | File must be >1 second of audio |
| `Invalid API key` | Check `OPENAI_API_KEY` in secrets |
| `File too large` | Max 25 MB — compress MP4 to MP3 first |
| `relation does not exist` | Run `supabase_schema.sql` in Supabase SQL Editor |
| `Invalid format: TOML` | Use `KEY = "value"` with quotes in Streamlit secrets |

---

## ⭐ If you found this useful

- ⭐ **[Star the repository](https://github.com/adityasharmadotai-hash)**
- 🌐 **[Visit adityasharma.ai](https://www.adityasharma.ai)** — AI training for professionals
- 💼 **[Follow on LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)**
- 📺 **[Subscribe on YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)**
- 🚀 **[AI Jobs in the USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

---

*Built with ❤️ by [Aditya Sharma](https://www.adityasharma.ai) · OpenAI Whisper + GPT-4o + Streamlit*
