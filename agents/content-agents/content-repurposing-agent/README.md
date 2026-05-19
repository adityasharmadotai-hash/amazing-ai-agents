# 🎬 AI Content Repurposing Agent

> Turn any YouTube video into LinkedIn posts, Twitter threads, Instagram captions, viral hooks, carousel slides, and blog summaries — in seconds, powered by OpenAI GPT-4o.

<img width="3024" height="1964" alt="image" src="https://github.com/user-attachments/assets/3dde5d57-2359-4328-8db3-2f504e262fdf" />

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

Content creators spend hours manually repurposing their video content across platforms. This agent automates the entire process: paste a YouTube URL, pick a writing style, and get 6 platform-optimised content formats in under 60 seconds.

Built on **OpenAI GPT-4o** with a clean modular Python architecture, **Supabase** for persistent history + analytics, and a beautiful Streamlit UI. Fully deployable on **Streamlit Community Cloud — free**.

---

## Features

| Feature | Description |
|---------|-------------|
| 🔗 **YouTube Transcript** | Extracts transcript from any public YouTube video — no API key needed |
| 💼 **LinkedIn Post** | Professional post optimised for reach and comments |
| 🐦 **Twitter/X Thread** | 8-12 tweet viral thread with numbered format |
| 📸 **Instagram Caption** | Hook + body + 15-20 hashtags |
| 🎣 **Viral Hooks** | 10 scroll-stopping opening hooks across 10 types |
| 🎠 **Carousel Slides** | 10-slide content with headlines and bullet points |
| 📝 **Blog Summary** | SEO-optimised blog article with proper structure |
| 🎨 **4 Writing Styles** | 🔥 Viral · 📚 Educational · 🚀 Founder · ⚙️ Technical |
| 📄 **Transcript Viewer** | Full text + timestamped segments |
| 📊 **Analytics Dashboard** | Content breakdown, daily activity, top videos |
| 📁 **History Database** | All generated content saved permanently in Supabase |
| ⚙️ **Prompt Manager** | View, edit, and create custom prompt templates |
| ⬇️ **Export** | Download any piece as .txt |

<img width="3024" height="1964" alt="image" src="https://github.com/user-attachments/assets/a7f5b629-35c8-492c-b338-86271102c949" />

---

## How It Works

```
┌──────────────────────────────────────────────────────────────┐
│                      AGENT FLOW                              │
│                                                              │
│  1. Paste YouTube URL                                        │
│            ↓                                                 │
│     transcript.py — youtube-transcript-api (no key needed)  │
│            ↓                                                 │
│  2. Pick Writing Style (Viral / Educational / Founder / Tech)│
│            ↓                                                 │
│  3. Click Generate                                           │
│            ↓                                                 │
│     prompts.py — builds system + user prompt                 │
│            ↓                                                 │
│     agent.py → OpenAI GPT-4o API                            │
│            ↓                                                 │
│     database.py → Supabase — saves to history               │
│            ↓                                                 │
│  4. Copy / Download / Export All                             │
└──────────────────────────────────────────────────────────────┘
```
<img width="3024" height="1964" alt="image" src="https://github.com/user-attachments/assets/7903a582-afda-4f29-a7ab-55dfc1b028fc" />

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Core language |
| Streamlit | Web UI |
| OpenAI GPT-4o | Content generation |
| youtube-transcript-api | Transcript extraction (no API key needed) |
| Supabase | Persistent history + analytics DB |
| Plotly | Analytics charts |

---

## Project Structure

```
content-repurposing-agent/
├── app.py                   # Main Streamlit app — 7 pages
├── modules/
│   ├── __init__.py
│   ├── transcript.py        # YouTube URL → transcript text
│   ├── prompts.py           # All prompt templates + style definitions
│   ├── agent.py             # OpenAI GPT-4o API calls
│   └── database.py          # Supabase CRUD + analytics
├── supabase_schema.sql      # Run once in Supabase SQL Editor
├── .streamlit/
│   └── config.toml          # Theme settings
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── Tutorial.md
```

---

## Getting Started

### 1. Clone

```bash
git clone https://github.com/adityasharmadotai-hash/amazing-ai-agents.git
cd amazing-ai-agents/agents/content-agents/content-repurposing-agent
```

### 2. Install

```bash
python3 -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

### 3. Set credentials

```bash
cp .env.example .env
# Edit .env — add your OpenAI API key
```

### 4. Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) 🎉

---

## Deploy to Streamlit Cloud (Free)

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Set main file: `app.py`
4. Go to **App → Settings → Secrets** and paste:

```toml
OPENAI_API_KEY = "sk-your-openai-key-here"
SUPABASE_URL   = "https://your-project.supabase.co"
SUPABASE_KEY   = "your-anon-key-here"
```

> ⚠️ Use TOML format: `KEY = "value"` with quotes. Not `KEY=value`.

5. Click **Deploy** — live in ~2 minutes ✅

> **Note:** Supabase is optional. The app works without it — history and analytics show a setup prompt, all content generation works perfectly.

---

## Supabase Setup (Optional — for History & Analytics)

1. Go to [supabase.com](https://supabase.com) → **New Project** (free)
2. Go to **SQL Editor → New Query**, paste `supabase_schema.sql`, click **Run ▶**
3. Go to **Project Settings → API** → copy your URL and anon key

---

## Common Errors & Fixes

| Error | Fix |
|-------|-----|
| `No English transcript available` | Try a video with English captions (CC badge) |
| `Invalid API key` | Check `OPENAI_API_KEY` in Streamlit secrets |
| `relation does not exist` | Run `supabase_schema.sql` in Supabase SQL Editor |
| `Invalid format: TOML` | Use `KEY = "value"` not `KEY=value` in secrets |
| `RateLimitError` | Wait a moment or check your OpenAI quota |

---

## Contributing

Pull requests are welcome! Fork → feature branch → PR.

---

## License

MIT — free to use, modify, and share.

---

## ⭐ If you found this useful

- ⭐ **[Star the repository](https://github.com/adityasharmadotai-hash)** — helps others discover this project
- 🌐 **[Visit adityasharma.ai](https://www.adityasharma.ai)** — AI training & tools for professionals
- 💼 **[Follow on LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)** — daily AI news, tools, and updates
- 📺 **[Subscribe on YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)** — AI agents, tutorials, and the latest in AI
- 🚀 **[AI Jobs in the USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)** — apply now

---

*Built with ❤️ by [Aditya Sharma](https://www.adityasharma.ai) · Powered by OpenAI GPT-4o + Streamlit*
