# 🤖 ARIA — AI Voice Assistant Agent

> Talk or type — ARIA creates tasks, takes notes, sets reminders, schedules events, and answers questions in real-time using OpenAI Whisper, GPT-4o, and TTS.

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

ARIA is a fully voice-enabled AI assistant built with Streamlit and OpenAI. Upload a voice recording or type a message — ARIA understands your intent, takes action, and speaks back.

---

## Features

| Feature | Description |
|---------|-------------|
| 🎙️ **Voice Input** | Upload MP3/WAV/M4A — Whisper AI transcribes instantly |
| 🧠 **Conversational AI** | GPT-4o with intent detection and context awareness |
| 🔊 **Text-to-Speech** | 6 OpenAI voices with speed control, auto-play responses |
| ✅ **Task Manager** | Create, complete, and track tasks — via voice or text |
| 📝 **Notes** | Save notes with AI formatting (bullets, summary, action items) |
| 🔔 **Reminders** | Set and dismiss reminders — detected from natural language |
| 📅 **Calendar** | Add and track events — schedule from voice commands |
| 💬 **Chat History** | Full conversation log with intent labels, exportable |
| 📊 **Dashboard** | Task analytics, intent breakdown, voice usage charts |
| ⚙️ **Settings** | User-provided API key — anyone can test on Streamlit Cloud |

---

## How It Works

```
User speaks / types
      ↓
stt.py → Whisper API → transcript text
      ↓
agent.py → GPT-4o
[INTENT: {"type": "CREATE_TASK", "data": {...}}]
+ spoken response
      ↓
tasks.py → execute intent (add task / note / reminder / event)
      ↓
tts.py → OpenAI TTS → audio playback
      ↓
Streamlit UI renders chat bubble + audio player
```

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Core language |
| Streamlit | Web UI |
| OpenAI Whisper | Speech-to-text |
| OpenAI GPT-4o | Conversational AI + intent detection |
| OpenAI TTS | Text-to-speech (6 voices) |
| Supabase | Optional persistent storage |
| Plotly | Dashboard charts |

---

## Project Structure

```
voice-assistant-agent/
├── app.py                 # Main Streamlit app — 8 pages
├── modules/
│   ├── stt.py             # Whisper speech-to-text
│   ├── tts.py             # OpenAI text-to-speech
│   ├── agent.py           # GPT-4o chat + intent detection
│   ├── tasks.py           # Task/note/reminder/calendar manager
│   └── database.py        # Supabase persistence (optional)
├── supabase_schema.sql
├── .streamlit/config.toml
├── requirements.txt
├── .env.example
└── README.md / Tutorial.md
```

---

## Getting Started

```bash
git clone https://github.com/adityasharmadotai-hash/amazing-ai-agents.git
cd amazing-ai-agents/agents/voice-assistant-agent
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your OPENAI_API_KEY
streamlit run app.py
```

---

## Deploy to Streamlit Cloud

```toml
OPENAI_API_KEY = "sk-your-key"
SUPABASE_URL   = "https://xxx.supabase.co"   # optional
SUPABASE_KEY   = "your-anon-key"              # optional
```

> Users can also enter their own key via the **⚙️ Settings** page.

---

## ⭐ If you found this useful

- ⭐ **[Star the repository](https://github.com/adityasharmadotai-hash)**
- 🌐 **[Visit adityasharma.ai](https://www.adityasharma.ai)**
- 💼 **[Follow on LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)**
- 📺 **[Subscribe on YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)**
- 🚀 **[AI Jobs in the USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

---

*Built with ❤️ by [Aditya Sharma](https://www.adityasharma.ai) · OpenAI Whisper + GPT-4o + TTS + Streamlit*
