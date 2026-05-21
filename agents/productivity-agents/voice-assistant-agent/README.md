# 🤖 ARIA — AI Voice Assistant Agent

> Record your voice in real-time, upload audio files, or type — ARIA transcribes, understands your intent, creates tasks/notes/reminders/events automatically, and speaks back using 6 AI voices.

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

ARIA is a fully voice-enabled AI assistant that runs entirely in the browser — no app install needed. It combines three OpenAI APIs (Whisper, GPT-4o, TTS) with a custom browser microphone recorder to give you a real conversational AI assistant.

Speak a command → Whisper transcribes it → GPT-4o detects your intent → ARIA takes action and speaks the confirmation back.

---

## Features

| Feature | Description |
|---------|-------------|
| 🔴 **Real-time Mic Recording** | Click-to-record directly in the browser via WebRTC MediaRecorder API |
| 📁 **Audio File Upload** | Upload MP3, WAV, M4A, OGG, WebM, FLAC — up to 25 MB |
| 🎙️ **Whisper Transcription** | OpenAI Whisper speech-to-text, 99 languages supported |
| 🧠 **Conversational AI** | GPT-4o with intent detection — understands 8 command types |
| 🔊 **Text-to-Speech** | 6 OpenAI voices, adjustable speed, auto-play responses |
| ✅ **Task Manager** | Creates tasks automatically from voice — priority, deadline |
| 📝 **Notes** | AI-formatted notes (bullets, summary, action items, formal) |
| 🔔 **Reminders** | Natural-language reminder detection and dismissal |
| 📅 **Calendar** | Schedule events from voice — countdown to upcoming events |
| 💬 **Chat History** | Full log with intent labels, action cards, voice badges, export |
| 📊 **Dashboard** | Priority pie, intent breakdown bar chart, voice usage stats |
| ⚙️ **Settings** | In-app API key entry — any user can test with their own key |

---

## How It Works

```
┌────────────────────────────────────────────────────────────────┐
│                     ARIA AGENT FLOW                            │
│                                                                │
│  Option A: Click mic button → speak → click stop              │
│  Option B: Upload MP3/WAV/MP4 file                            │
│  Option C: Type a message                                      │
│              ↓                                                  │
│  recorder.py — Browser MediaRecorder → WebM audio bytes       │
│  stt.py     — OpenAI Whisper API → transcript text            │
│              ↓                                                  │
│  agent.py → GPT-4o                                            │
│  [INTENT: {"type": "CREATE_TASK", "data": {...}}]             │
│  + spoken response text                                        │
│              ↓                                                  │
│  tasks.py — execute intent automatically                       │
│    CREATE_TASK      → add_task()                              │
│    CREATE_NOTE      → add_note()                              │
│    CREATE_REMINDER  → add_reminder()                          │
│    CALENDAR_EVENT   → add_calendar_event()                    │
│    SEARCH_WEB       → web_search_answer()                     │
│              ↓                                                  │
│  tts.py → OpenAI TTS → MP3 bytes → base64 HTML audio player  │
│  app.py → chat bubble + action card + auto-play audio         │
└────────────────────────────────────────────────────────────────┘
```

---

## 8 Intent Types ARIA Understands

| Intent | Example voice command |
|--------|-----------------------|
| `CHAT` | "What's the capital of Japan?" |
| `CREATE_TASK` | "Add a task to review the proposal by Friday" |
| `CREATE_NOTE` | "Take a note — meeting ideas: use async comms" |
| `CREATE_REMINDER` | "Remind me to call Alice tomorrow at 9 AM" |
| `CALENDAR_EVENT` | "Schedule a team meeting Thursday 2 PM" |
| `SEARCH_WEB` | "What is the latest news about AI?" |
| `UPDATE_TASK` | "Mark the proposal review as done" |
| `SUMMARISE` | "Summarise my tasks for today" |

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Core language |
| Streamlit | Web UI + component framework |
| **Browser MediaRecorder API** | **Real-time microphone recording (JS/WebRTC)** |
| OpenAI Whisper | Speech-to-text transcription |
| OpenAI GPT-4o | Conversational AI + intent detection |
| OpenAI TTS | Text-to-speech (6 voices) |
| Supabase | Optional persistent conversation storage |
| Plotly | Dashboard analytics charts |

---

## Project Structure

```
voice-assistant-agent/
├── app.py                  # Main Streamlit app — 8 pages
├── modules/
│   ├── recorder.py         # ← Browser mic recorder (HTML/JS + WebRTC)
│   ├── stt.py              # OpenAI Whisper speech-to-text
│   ├── tts.py              # OpenAI TTS text-to-speech (6 voices)
│   ├── agent.py            # GPT-4o chat + intent detection
│   ├── tasks.py            # Task/note/reminder/calendar (session state)
│   └── database.py         # Supabase persistence (optional)
├── supabase_schema.sql     # Run once in Supabase SQL Editor
├── .streamlit/
│   └── config.toml         # Theme + server config
├── requirements.txt        # 5 pip packages
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
cd amazing-ai-agents/agents/voice-assistant-agent
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Add your API key

```bash
cp .env.example .env
# Edit .env — set OPENAI_API_KEY=sk-your-key
```

### 3. Run

```bash
streamlit run app.py
# Opens at http://localhost:8501
```

### 4. First time — allow microphone

When you click the **🔴 Record** button for the first time, your browser will ask for microphone permission. Click **Allow**.

> **Note:** Microphone recording requires **HTTPS or localhost**. Streamlit Cloud uses HTTPS by default. For local dev, `localhost` always works.

---

## Deploy to Streamlit Cloud

1. Push to GitHub (`.env` is in `.gitignore` — never committed)
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Set main file: `app.py`
4. **Advanced settings → Secrets** (TOML format, quotes required):

```toml
OPENAI_API_KEY = "sk-your-openai-key"
SUPABASE_URL   = "https://your-project.supabase.co"
SUPABASE_KEY   = "your-anon-key"
```

5. Click **Deploy** ✅

> **Public access:** Users who visit your deployed app can enter their own OpenAI key via **⚙️ Settings** — so you don't need to share yours.

---

## Browser Compatibility (Mic Recording)

| Browser | Status |
|---------|--------|
| ✅ Chrome 70+ | Full support — recommended |
| ✅ Edge 79+ | Full support |
| ✅ Firefox 65+ | Full support |
| ✅ Safari 14.1+ | Supported |
| ❌ IE / old browsers | Not supported |

> Requires **HTTPS** in production (Streamlit Cloud handles this automatically).

---

## Common Errors & Fixes

| Error | Fix |
|-------|-----|
| Mic button does nothing | Allow microphone permission in browser settings |
| `Invalid API key` | Go to ⚙️ Settings and re-enter your key |
| `Audio too short` | Record at least 1 second of clear speech |
| `File too large` | Max 25 MB — compress MP4 to MP3 first |
| TTS not playing | Click the audio player manually (browser autoplay policy) |
| Intent not detected | Normal for very short messages — ARIA defaults to CHAT |
| `relation does not exist` | Run `supabase_schema.sql` in Supabase SQL Editor |
| `Invalid format: TOML` | Use `KEY = "value"` with quotes in Streamlit secrets |

---

## ⭐ If you found this useful

- ⭐ **[Star the repository](https://github.com/adityasharmadotai-hash)** — helps others discover this
- 🌐 **[Visit adityasharma.ai](https://www.adityasharma.ai)** — AI training for professionals
- 💼 **[Follow on LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)** — daily AI updates
- 📺 **[Subscribe on YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)** — AI agent tutorials
- 🚀 **[AI Jobs in the USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

---

*Built with ❤️ by [Aditya Sharma](https://www.adityasharma.ai) · OpenAI Whisper + GPT-4o + TTS + WebRTC + Streamlit*
