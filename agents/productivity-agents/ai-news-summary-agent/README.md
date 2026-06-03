# 📰 AI News Summary Agent

> **Your personal AI-powered news intelligence platform.**
> Aggregate news from 20+ sources, let GPT-4o detect high-signal stories, remove duplicates, generate executive digests, and deliver them to your email or WhatsApp — automatically.

<img width="1921" height="2547" alt="screencapture-ai-news-summary-agent-streamlit-app-2026-05-30-16_45_26" src="https://github.com/user-attachments/assets/c2795150-2d2b-44af-bf6b-afc6da502cf6" />

**👉 STEP-BY-STEP TUTORIAL: [Tutorial.md](./Tutorial.md)**

---

## Features

- 📡 **20+ News Sources** — RSS feeds, Google News, Hacker News, Reddit, NewsAPI.org
- 🧠 **AI Triage** — Signal scoring (0-10), sentiment analysis, topic classification
- 🔍 **Duplicate Removal** — Title similarity + AI-powered deduplication
- ✨ **Executive Digest** — GPT-4o morning briefing with sections, talking points, action items
- 🔥 **High-Signal Detection** — Surface the 5-10 stories that actually matter
- 📊 **Analytics Dashboard** — Topic distribution, sentiment trends, source rankings
- 🔖 **Saved Stories** — Personal reading list with notes
- ⚙️ **Preferences** — Topics, keywords, companies, countries, sources
- 📬 **Email Delivery** — HTML digest via SMTP (Gmail App Password supported)
- 💬 **WhatsApp** — wa.me link with pre-filled message
- 🕐 **Scheduler** — Daily at 6 AM UTC, hourly, or custom schedule
- ❓ **Ask the News** — GPT-4o Q&A over today's news feed
- 🎭 **Demo Mode** — Full functionality without any API keys

<img width="1797" height="778" alt="image" src="https://github.com/user-attachments/assets/b49023c4-44c7-4509-a8a9-82c905ea2c25" />

---

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Demo Mode is on by default — no API keys needed to explore.

---

## Connecting Real Sources

### OpenAI (for AI features)
Add to `.env`: `OPENAI_API_KEY=sk-...`

### NewsAPI.org (optional, free tier)
1. Get a free key at [newsapi.org](https://newsapi.org)
2. Add: `NEWS_API_KEY=your_key`

### Email Delivery (Gmail)
1. Enable 2FA on Gmail
2. Generate an App Password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Add to `.env`: `SMTP_USER=you@gmail.com` + `SMTP_PASS=your_app_password`

---

## Pages

| Page | What it does |
|------|-------------|
| 📰 News Feed | Full feed with search, filter, signal score, article detail |
| ✨ AI Digest | GPT-4o executive brief with sections and action items |
| 🔥 High Signal | Top stories ≥7.0 signal + trending theme detection |
| 📊 Analytics | Topic distribution, sentiment pie, source rankings |
| 🔖 Saved Stories | Bookmarked articles with delete |
| ⚙️ Preferences | Topics, keywords, companies, countries, RSS sources |
| 📬 Delivery | Email digest + WhatsApp wa.me link |
| 🕐 Scheduler | Daily/hourly fetch schedule + manual run now |
| ❓ Ask the News | GPT-4o Q&A about today's news |
| ⚙️ Settings | API keys, model config, DB export |

---

## Project Structure

```
ai-news-summary-agent/
├── app.py                  # Streamlit UI (10 pages)
├── modules/
│   ├── agent.py            # 8 GPT-4o functions
│   ├── fetcher.py          # 7 news source adapters
│   ├── database.py         # SQLite (7 tables)
│   ├── delivery.py         # Email + WhatsApp delivery
│   ├── scheduler.py        # Background scheduling
│   └── demo_data.py        # 15 demo articles + demo digest
├── .streamlit/config.toml  # Dark green theme
├── requirements.txt
└── .env.example
```
<img width="1656" height="689" alt="image" src="https://github.com/user-attachments/assets/c4b8f254-031e-4c74-ae98-d800a1690c06" />

---

## License

MIT
