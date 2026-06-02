> ⭐ **Star the repo:** https://github.com/adityasharmadotai-hash/amazing-ai-agents
> 💼 **Follow on LinkedIn:** https://www.linkedin.com/in/aditya-hicounselor/
> 📺 **Subscribe on YouTube:** https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ
> 🚀 **Looking for jobs at top AI companies in the U.S.? [Apply here](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

---

# 📧 Email Summary & Action Items Agent

> **Turn your chaotic inbox into a clean, prioritized action list — automatically, every morning.**
> Connects to Gmail, summarizes every email with AI, extracts action items, assigns a priority, and writes it all to a Google Sheet you can act on.

**👉 STEP-BY-STEP TUTORIAL: [TUTORIAL.md](./TUTORIAL.md)**

---

## Overview

Most people lose hours every week reading the same emails twice, hunting for the one line that actually needs a reply, and forgetting follow-ups that quietly slip through the cracks.

**Email Summary & Action Items Agent** solves this. It is a production-ready Streamlit application that:

1. Connects securely to your Gmail with Google OAuth.
2. Reads your inbox, unread mail, or the last 24 hours of messages.
3. Uses OpenAI to write a concise summary, extract the required action, assign a **High / Medium / Low** priority, identify the sender, and pull out any due dates.
4. Writes every result into a **Google Sheet** (and a local SQLite database) with a `Status` column you can flip between `Pending` and `Completed`.
5. Shows it all in a modern dashboard with analytics cards, charts, filters, AI insights, and one-click CSV / Excel / PDF export.

The result: you open one tidy sheet (or dashboard) each morning instead of 60 unread emails, and you never miss an urgent follow-up again.

---

## Features

### 1. Gmail Integration
- 🔐 Google OAuth 2.0 sign-in
- 📥 Read inbox emails
- 📨 Read unread emails
- 🕐 Read emails from the last 24 hours
- 🏷️ Support for labels and folders

### 2. AI Email Analysis
For every email the agent:
- 📝 Generates a concise summary
- ✅ Extracts the required action item
- 🚦 Assigns a priority (High / Medium / Low)
- 👤 Identifies the sender
- 📅 Extracts due dates when mentioned

### 3. Google Sheets Integration
Automatically creates / updates a Google Sheet with columns:
`Date · Sender · Subject · Email Summary · Action Item · Priority · Status`

### 4. Daily Automation
- ⏰ Runs every morning
- 🔄 Processes only new emails
- ➕ Appends results to the Google Sheet

### 5. Dashboard
- Total emails analyzed
- High / Medium / Low priority counts
- Pending vs Completed actions
- Interactive filters and charts

### 6. AI Insights
- 🧠 Daily inbox summary
- 🔥 Top urgent emails
- 📌 Missed follow-ups
- 👉 Recommended next actions

### 7. Export
- CSV
- Excel (.xlsx)
- PDF

### Priority Rules
| Priority | Meaning |
|----------|---------|
| 🔴 **High** | Requires immediate response or action |
| 🟡 **Medium** | Can be addressed within a few days |
| 🟢 **Low** | Promotions, newsletters, notifications, FYI emails |

---

## How It Works

```
        ┌──────────────┐
        │   Gmail API  │  inbox / unread / last 24h / labels
        └──────┬───────┘
               │  raw emails
               ▼
        ┌──────────────┐
        │  Email Fetch │  gmail_client.py
        └──────┬───────┘
               │  cleaned messages
               ▼
        ┌──────────────┐      ┌──────────────────┐
        │  AI Analyzer │─────▶│   OpenAI (LLM)   │
        │  analyzer.py │◀─────│  summary +       │
        └──────┬───────┘      │  action +        │
               │              │  priority + dates│
               │              └──────────────────┘
               ▼
   ┌───────────┴────────────┐
   ▼                        ▼
┌────────────┐      ┌────────────────┐
│   SQLite   │      │  Google Sheet  │
│ (history)  │      │  (live output) │
└─────┬──────┘      └────────────────┘
      │
      ▼
┌──────────────────────────────────────┐
│   Streamlit Dashboard                 │
│   cards · charts · filters · insights │
│   export CSV / Excel / PDF            │
└──────────────────────────────────────┘
```

1. **Fetch** — `gmail_client.py` pulls emails based on the filter you pick.
2. **Analyze** — `analyzer.py` sends each email to OpenAI and gets back structured JSON.
3. **Store** — results are saved to SQLite and appended to a Google Sheet.
4. **Visualize** — the Streamlit dashboard renders metrics, charts, and AI insights.
5. **Automate** — a scheduler re-runs the pipeline every morning.

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Core language |
| Streamlit | Web dashboard / UI |
| OpenAI API | Summaries, action items, priority, insights |
| Gmail API | Read inbox / unread / labels |
| Google Sheets API | Live output sheet |
| google-auth-oauthlib | OAuth 2.0 flow |
| SQLite | Local persistence & dedupe |
| Plotly | Charts and analytics |
| Pandas | Data wrangling & export |
| APScheduler | Daily automation |
| openpyxl / reportlab | Excel & PDF export |

---

## File Structure

```
email-summary-action-agent/
├── app.py                     # Main Streamlit app (dashboard + pages)
├── modules/
│   ├── __init__.py
│   ├── gmail_client.py        # Gmail API + OAuth (fetch inbox/unread/24h/labels)
│   ├── analyzer.py            # OpenAI analysis (summary, action, priority, dates)
│   ├── sheets_client.py       # Google Sheets create/append/update
│   ├── database.py            # SQLite store (history, status, dedupe)
│   ├── insights.py            # AI daily insights + urgent/follow-up detection
│   ├── exporter.py            # CSV / Excel / PDF export
│   └── scheduler.py           # Daily automation (APScheduler)
├── .env.example               # Environment variable template
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── TUTORIAL.md                # Full beginner-friendly walkthrough
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/adityasharmadotai-hash/amazing-ai-agents.git
cd amazing-ai-agents/agents/productivity-agents/email-summary-action-agent
```

### 2. Create a virtual environment & install dependencies

```bash
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set up Google Cloud credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project and enable the **Gmail API** and **Google Sheets API**.
3. Create **OAuth 2.0 Client ID** credentials (Desktop app) and download `credentials.json` into this folder.
4. Add your email as a **Test user** on the OAuth consent screen.

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
OPENAI_API_KEY=sk-...
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_SHEET_NAME=Email Action Items
```

### 5. Run the app

```bash
streamlit run app.py
```

Open `http://localhost:8501`, click **Connect Gmail**, authorize, and hit **Analyze Inbox**.

---

## Deployment

### Streamlit Community Cloud

1. Push this folder to a GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo.
3. Set the main file path to `app.py`.
4. Add your secrets under **App → Settings → Secrets**:

   ```toml
   OPENAI_API_KEY = "sk-..."
   GOOGLE_SHEET_NAME = "Email Action Items"
   ```

5. For Google OAuth in the cloud, use a **Service Account** (recommended for headless deployments) and store its JSON in Streamlit secrets. See [TUTORIAL.md](./TUTORIAL.md) for the full walkthrough.

> 💡 Because Gmail OAuth needs an interactive browser flow, many users run this agent locally (or on a small VM with the scheduler) and use Streamlit Cloud only for the read-only dashboard backed by the Google Sheet.

---

## Contributing

Contributions are welcome! 🎉

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please keep modules small and focused, add error handling, and update the README/TUTORIAL when behavior changes.

---

## License

This project is released under the **MIT License**. See the root `LICENSE` file for details.

---

## 📚 Tutorial

New to this? Follow the complete beginner-friendly guide here:
👉 **[TUTORIAL.md](./TUTORIAL.md)**

You can also check out the companion tutorial format used across these agents:
👉 **[Docs Reader RAG Agent Tutorial](https://github.com/adityasharmadotai-hash/docs-reader-rag-agent/blob/main/TUTORIAL.md)**

---

> ⭐ **Star the repo:** https://github.com/adityasharmadotai-hash/amazing-ai-agents
> 💼 **Follow on LinkedIn:** https://www.linkedin.com/in/aditya-hicounselor/
> 📺 **Subscribe on YouTube:** https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ
> 🚀 **Looking for jobs at top AI companies in the U.S.? [Apply here](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**
