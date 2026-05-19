# 🎬 AI Content Repurposing Agent

> Turn any YouTube video into LinkedIn posts, Twitter threads, Instagram captions, viral hooks, carousel slides, and blog summaries — in seconds, powered by OpenAI GPT-4o.

---

> ⭐ **Star the repo:** [github.com/adityasharmadotai-hash](https://github.com/adityasharmadotai-hash)
> 💼 **Follow on LinkedIn:** [linkedin.com/in/aditya-hicounselor](https://www.linkedin.com/in/aditya-hicounselor/)
> 📺 **Subscribe on YouTube:** [YouTube Channel](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)
> 🚀 **AI Jobs in the USA:** [Apply Now](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)

---

**👉 STEP-BY-STEP TUTORIAL: [Tutorial.md](./Tutorial.md)**

---

## Overview

Content creators spend hours manually repurposing their video content across platforms. This agent automates the entire process: paste a YouTube URL, pick a writing style, and get 6 platform-optimised content formats in under 60 seconds.

Built on **OpenAI GPT-4o (gpt-4o)** with a clean modular Python architecture, **Supabase** for persistent history + analytics, and a beautiful Streamlit UI.

---

## Features

| Feature | Description |
|---------|-------------|
| 🔗 **YouTube Transcript** | Extracts transcript from any public YouTube video (no API key needed) |
| 💼 **LinkedIn Post** | Professional post optimised for reach and comments |
| 🐦 **Twitter/X Thread** | 8-12 tweet viral thread with numbering |
| 📸 **Instagram Caption** | Hook + body + 15-20 hashtags |
| 🎣 **Viral Hooks** | 10 scroll-stopping opening hooks |
| 🎠 **Carousel Slides** | 10-slide content with headlines and bullet points |
| 📝 **Blog Summary** | SEO-optimised blog article with proper structure |
| 🎨 **4 Writing Styles** | Viral · Educational · Founder · Technical |
| 📄 **Transcript Viewer** | Full text + timestamped segments |
| 📊 **Analytics Dashboard** | Content breakdown, daily activity, top videos |
| 📁 **History Database** | All generated content saved permanently in Supabase |
| ⚙️ **Prompt Manager** | View, edit, and create custom prompt templates |
| ⬇️ **Export** | Download any piece as .txt |

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
│     agent.py → OpenAI GPT-4o API                   │
│            ↓                                                 │
│     database.py → Supabase — saves to history               │
│            ↓                                                 │
│  4. Copy / Download / Export All                             │
└──────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Core language |
| Streamlit | Web UI |
| OpenAI GPT-4o | Content generation |
| youtube-transcript-api | Transcript extraction (no key needed) |
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
│   ├── agent.py             # Claude API calls
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
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 3. Set credentials

```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

### 4. Run

```bash
streamlit run app.py
```

---

## Deploy to Streamlit Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Set main file: `app.py`
4. Add secrets:

```toml
OPENAI_API_KEY = "sk-your-openai-key-here"
SUPABASE_URL      = "https://your-project.supabase.co"
SUPABASE_KEY      = "your-anon-key"
```

5. Deploy ✅

> **Note:** Supabase is optional. The app works without it — history and analytics are disabled, everything else works perfectly.

---

## Common Errors & Fixes

| Error | Fix |
|-------|-----|
| `No English transcript available` | Try a video with English captions enabled |
| `Invalid API key` | Check `OPENAI_API_KEY` in secrets |
| `relation does not exist` | Run `supabase_schema.sql` in Supabase SQL Editor |
| `Invalid format: TOML` | Use `KEY = "value"` not `KEY=value` in Streamlit secrets |
| `RateLimitError` | Wait a moment and retry — or check your OpenAI quota |

---

## License

MIT — free to use, modify, and share.

---

## ⭐ If you found this useful...

- ⭐ **[Star the repository](https://github.com/adityasharmadotai-hash)**
- 💼 **[Follow on LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)**
- 📺 **[Subscribe on YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)**
- 🚀 **[AI Jobs in the USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

---

*Built with ❤️ using Python, OpenAI GPT-4o, Supabase, and Streamlit*
