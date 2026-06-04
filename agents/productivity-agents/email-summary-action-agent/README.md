> ⭐ **Star the repo:** https://github.com/adityasharmadotai-hash/amazing-ai-agents
> 💼 **Follow on LinkedIn:** https://www.linkedin.com/in/aditya-hicounselor/
> 📺 **Subscribe on YouTube:** https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ
> 🚀 **Looking for jobs at top AI companies in the U.S.?** [Apply here](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)

---

# 📬 Email Summary & Action Items Agent

**An AI agent that reads your Gmail every morning, tells you what matters, and turns your inbox into a clean, prioritized action list in Google Sheets.**

---

## Overview

Your inbox is a to-do list someone else wrote — and it's a mess. Real action items hide between newsletters, receipts, and "just looping you in" threads. By the time you've read everything, you've spent 40 minutes and still aren't sure what actually needs a reply.

This agent fixes that. It connects to Gmail, pulls your recent or unread emails, and runs each one through an LLM that produces:

- a **one-line summary** of what the email is about,
- the **single action item** it implies (if any),
- a **priority** — High, Medium, or Low,
- the **sender** and any **due date** mentioned in the text.

Results land in a **Google Sheet** you can share with anyone, get tracked in a local **SQLite** database so nothing is analyzed twice, and show up in a **Streamlit dashboard** with cards, charts, AI insights, and one-click export to CSV / Excel / PDF.

Run it once by hand, or schedule it to run every morning before you've had coffee.

### Priority rules

| Priority | Meaning |
|----------|---------|
| 🔴 **High** | Requires an immediate response or action — deadlines, urgent asks, anything blocking you or a customer |
| 🟠 **Medium** | Can be addressed within a few days — scheduling, reviews, non-urgent requests |
| ⚪ **Low** | Promotions, newsletters, notifications, receipts, FYI emails |

---

## Features

- **Gmail integration** — Google OAuth, read inbox / unread / last-24-hours, filter by label or folder
- **AI analysis** — per-email summary, action item, priority, sender, and due-date extraction
- **Google Sheets output** — auto-creates and appends to a shareable sheet (`Date · Sender · Subject · Summary · Action Item · Priority · Due Date · Status`)
- **Daily automation** — run every morning via the built-in scheduler, cron, or GitHub Actions
- **Modern dashboard** — analytics cards, priority + status charts, filters, and an editable status table
- **AI insights** — daily inbox briefing, top urgent emails, likely missed follow-ups, recommended next actions
- **Export** — download everything as CSV, Excel, or PDF
- **Built to last** — modular architecture, async email analysis, SQLite dedup, and error handling throughout

---

## How it works

```text
        ┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌───────────────┐
        │    Gmail    │ ──> │  AI Analyzer │ ──> │    SQLite    │ ──> │ Google Sheet  │
        │  (OAuth)    │     │  (OpenAI)    │     │ (dedup +     │     │ (shareable    │
        │  fetch mail │     │  summary,    │     │  source of   │     │  output)      │
        │             │     │  priority,   │     │  truth)      │     │               │
        │             │     │  action item │     │              │     │               │
        └─────────────┘     └──────────────┘     └──────┬───────┘     └───────────────┘
                                                        │
                                                        v
                                            ┌───────────────────────┐
                                            │  Streamlit Dashboard   │
                                            │  cards · charts ·      │
                                            │  insights · export     │
                                            └───────────────────────┘
```

1. **Fetch** — Gmail API pulls messages matching your filter (last 24h / unread / a label).
2. **Dedup** — anything already in SQLite is skipped *before* paying for an OpenAI call.
3. **Analyze** — new emails are sent to the model concurrently (async) and come back as structured JSON.
4. **Store** — results are written to SQLite (the source of truth) and mirrored to a Google Sheet.
5. **Review** — the Streamlit dashboard shows the numbers, an AI briefing, and a filterable, editable table.

---

## Tech stack

| Layer | Technology | Why |
|-------|-----------|-----|
| UI | **Streamlit** | Fast, Pythonic dashboards with charts and widgets |
| AI | **OpenAI API** | Email summarization, action extraction, prioritization, insights |
| Email | **Gmail API** | OAuth + read access to messages and labels |
| Output | **Google Sheets API** | Shareable, always-up-to-date action list |
| Storage | **SQLite** | Zero-config local persistence and dedup |
| Charts | **Plotly** | Interactive priority and status visualizations |
| Export | **pandas · openpyxl · reportlab** | CSV, Excel, and PDF reports |
| Scheduling | **schedule** / cron / GitHub Actions | Daily morning runs |
| Concurrency | **asyncio** | Analyze a full inbox in seconds |

---

## File structure

```text
email-action-agent/
├── app.py                  # Streamlit dashboard (entry point)
├── config.py               # Central settings (scopes, model, paths)
├── requirements.txt
├── .env.example            # Copy to .env and fill in
├── .gitignore
├── .streamlit/
│   └── config.toml         # Theme + server config
├── data/                   # SQLite db + OAuth token live here (git-ignored)
└── src/
    ├── __init__.py
    ├── gmail_client.py     # OAuth + email fetching
    ├── ai_analyzer.py      # OpenAI analysis (sync + async)
    ├── sheets_client.py    # Create/update Google Sheet
    ├── database.py         # SQLite persistence + stats
    ├── insights.py         # AI daily briefing
    ├── exporter.py         # CSV / Excel / PDF export
    ├── pipeline.py         # Orchestrator: Gmail → AI → DB → Sheet
    └── scheduler.py        # Daily automation
```

---

## Getting started

### 1. Clone and install

```bash
git clone https://github.com/adityasharmadotai-hash/amazing-ai-agents.git
cd amazing-ai-agents/email-action-agent

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Get your API keys

- **OpenAI** — create a key at [platform.openai.com](https://platform.openai.com/api-keys).
- **Google** — in the [Google Cloud Console](https://console.cloud.google.com/):
  1. Create a project and enable the **Gmail API** and **Google Sheets API**.
  2. Configure the OAuth consent screen (External → add yourself as a test user).
  3. Create an **OAuth client ID** of type **Desktop app**.
  4. Download the JSON and save it as `credentials.json` in the project root.

### 3. Configure

```bash
cp .env.example .env
# open .env and paste your OPENAI_API_KEY
```

### 4. Run

```bash
streamlit run app.py
```

The first scan opens a browser window to authorize Gmail + Sheets access. After you approve, a `data/token.json` is saved and you won't be asked again.

### 5. Automate (optional)

```bash
# Long-running scheduler (runs every morning at DAILY_RUN_TIME)
python -m src.scheduler

# Or a single run for cron / Task Scheduler / GitHub Actions
python -m src.pipeline
```

---

## Deployment

### Streamlit Community Cloud (free)

1. Push your fork to GitHub (the `.gitignore` already keeps secrets out).
2. Go to [share.streamlit.io](https://share.streamlit.io), connect the repo, and set the main file to `email-action-agent/app.py`.
3. In **App settings → Secrets**, add your environment values:
   ```toml
   OPENAI_API_KEY = "sk-..."
   SHEET_TITLE = "Email Action Items"
   ```
4. For Google OAuth on a hosted app, use a **service account** (recommended for headless deploys) and share your Sheet with the service-account email — the interactive desktop OAuth flow is best kept for local use. See the [tutorial](https://github.com/adityasharmadotai-hash/docs-reader-rag-agent/blob/main/TUTORIAL.md) for the full walkthrough.

### Other options

- **Docker / VPS** — run `streamlit run app.py` behind a reverse proxy; schedule daily runs with system cron calling `python -m src.pipeline`.
- **GitHub Actions** — a scheduled workflow can run the pipeline daily and commit nothing (data lives in your Sheet + a persisted DB artifact).

---

## Contributing

Contributions are welcome! 🙌

1. Fork the repo and create a branch: `git checkout -b feature/your-idea`
2. Make your change with a clear commit message.
3. Open a pull request describing what and why.

Good first issues: add Outlook support, swap OpenAI for a local model, add a "snooze" status, or build a weekly digest email.

---

## License

Released under the **MIT License** — free to use, modify, and share. See [`LICENSE`](LICENSE) for details.

---

## 📘 Full tutorial

New to this? The step-by-step beginner guide walks through every file with plain-English explanations:
**[👉 Read the TUTORIAL](https://github.com/adityasharmadotai-hash/docs-reader-rag-agent/blob/main/TUTORIAL.md)**

---

> Built in public by [Aditya](https://www.linkedin.com/in/aditya-hicounselor/). If this saved you time, a ⭐ on the repo means a lot.
