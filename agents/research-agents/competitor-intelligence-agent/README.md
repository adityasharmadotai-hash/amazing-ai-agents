> ⭐ **Star the repo:** https://github.com/adityasharmadotai-hash/amazing-ai-agents
> 💼 **Follow on LinkedIn:** https://www.linkedin.com/in/aditya-hicounselor/
> 📺 **Subscribe on YouTube:** https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ
> 🚀 **Looking for jobs at top AI companies in the U.S.? Apply here:** https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform

---

# 🔍 Competitor Intelligence Agent

> An AI-powered Streamlit app that monitors your competitors' websites, pricing, hiring, and product launches — and turns the signals into plain-English insights using OpenAI.

---

## 📖 Overview

Keeping tabs on competitors is tedious: you manually check pricing pages, scan job boards, read changelogs, and try to remember what changed since last week. **Competitor Intelligence Agent** automates that loop.

You add a competitor (name + website), and the app:

- **Scrapes** their website, pricing page, and job postings,
- **Stores** every snapshot and change in a local SQLite database,
- **Analyzes** the changes with OpenAI to explain *what changed and why it matters*,
- **Surfaces** everything on an interactive dashboard with charts, alerts, and downloadable reports.

The result: a single pane of glass for competitive intelligence, instead of a dozen browser tabs and a spreadsheet.

<img width="1810" height="660" alt="image" src="https://github.com/user-attachments/assets/d4f8fa3a-152a-415b-af65-53625f28e8a1" />

---

## ✨ Features

- 🌐 **Website Monitoring** — detect content changes, new sections, and new links via content hashing.
- 💰 **Pricing Intelligence** — scrape pricing/plans pages and track changes over time.
- 👥 **Hiring Activity** — discover job postings and break them down by department.
- 🚀 **Product Launch Detection** — use AI to surface recent launches and announcements.
- 🤖 **AI Insights** — OpenAI (GPT‑4o by default) summarizes changes and strategic implications.
- 📧 **Email Alerts & Digests** — daily/weekly HTML email digests via SMTP.
- 📊 **Interactive Dashboard** — KPI cards, activity timelines, and competitor‑health charts (Plotly).
- 📥 **Downloadable Reports** — export executive and market reports as JSON.
- ⚙️ **Settings Page** — configure your API key, model, alerts, and monitoring features in one place (no code edits).

---

## 🧠 How It Works

You drive the app from a sidebar navigation menu. Each action scrapes data, persists it, optionally runs it through OpenAI, and renders the result.

```
                ┌──────────────────────────────────────────┐
                │            Streamlit UI (app.py)           │
                │  Sidebar nav · Dashboard · Settings page   │
                └───────────────┬────────────────────────────┘
                                │
            ┌───────────────────┼─────────────────────┐
            ▼                   ▼                     ▼
     ┌────────────┐      ┌──────────────┐      ┌────────────┐
     │  Scraper   │      │  AI Analysis │      │   Alerts   │
     │ scraper.py │      │ai_analysis.py│      │  alerts.py │
     │ (requests/ │      │  (OpenAI)    │      │   (SMTP)   │
     │   bs4)     │      │              │      │            │
     └─────┬──────┘      └──────┬───────┘      └─────┬──────┘
           │                    │                    │
           └────────────────────┼────────────────────┘
                                ▼
                        ┌───────────────┐
                        │   Database    │
                        │ database.py   │
                        │   (SQLite)    │
                        └───────────────┘
```

**Flow:** UI action → `scraper` collects data → `database` stores it → `ai_analysis` explains it → results shown on the dashboard, with `alerts` sending email digests on demand.

---

## 🛠️ Tech Stack

| Layer            | Technology                          | Used For                                   |
| ---------------- | ----------------------------------- | ------------------------------------------ |
| **UI**           | [Streamlit](https://streamlit.io)   | Web app, navigation, forms, layout         |
| **AI**           | [OpenAI](https://openai.com) (GPT‑4o) | Change summaries, insights, launch detection |
| **Scraping**     | Requests + BeautifulSoup4 + lxml    | Website / pricing / job data collection    |
| **Database**     | SQLite (`sqlite3`)                  | Persisting competitors, changes, alerts    |
| **Charts**       | [Plotly](https://plotly.com)        | Bar charts, pie charts, timelines          |
| **Email**        | `smtplib` + Jinja2                  | HTML digest & report emails                |
| **Config**       | python-dotenv / Streamlit Secrets   | API keys and environment variables         |

---

## 📂 File Structure

```
competitor-intelligence-agent/
├── app.py                 # Main Streamlit app (UI, navigation, pages)
├── ai_analysis.py         # OpenAI integration: CompetitorAnalyzer + ReportGenerator
├── scraper.py             # WebScraper, PricingScraper, HiringTracker, Social/News monitors
├── alerts.py              # AlertManager: email digests & reports (SMTP + Jinja2)
├── database.py            # SQLite schema and data-access layer
├── generate_test_data.py  # CLI to seed the database with realistic sample data
├── requirements.txt       # Python dependencies
├── .env.example           # Template for environment variables
├── README.md              # You are here
└── TUTORIAL.md            # Step-by-step beginner tutorial
```

---

## 🚀 Getting Started

### Prerequisites

- Python **3.10+**
- An **OpenAI API key** ([platform.openai.com](https://platform.openai.com/api-keys))
- *(Optional)* SMTP credentials (e.g. a Gmail App Password) for email alerts

### 1. Clone the repository

```bash
git clone https://github.com/adityasharmadotai-hash/amazing-ai-agents.git
cd amazing-ai-agents/agents/research-agents/competitor-intelligence-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
# macOS / Linux
source venv/bin/activate
# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API key

Copy the example env file and add your key:

```bash
cp .env.example .env
```

Then edit `.env`:

```bash
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o
```

> 💡 You can also skip the `.env` file entirely and paste your key into the **⚙️ Settings** page after launching the app.

### 5. (Optional) Seed sample data

```bash
python generate_test_data.py --competitors 5 --days 30
```

### 6. Run the app

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## ☁️ Deployment (Streamlit Community Cloud)

1. Push the project to a **public GitHub repository**.
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **New app**.
3. Select your repo, branch, and set the **Main file path** to:
   ```
   agents/research-agents/competitor-intelligence-agent/app.py
   ```
4. Open **Advanced settings → Secrets** and add your key (TOML format):
   ```toml
   OPENAI_API_KEY = "sk-your-api-key-here"
   OPENAI_MODEL = "gpt-4o"
   ```
5. Click **Deploy**. Streamlit installs `requirements.txt` and launches your app.

> The app reads the key from **Settings page → Streamlit Secrets → environment variable**, in that order — so Secrets is the recommended place for a deployed demo.

---

## 📚 Tutorial

New to this? Follow the detailed, beginner-friendly walkthrough:

- 👉 **[TUTORIAL.md](./TUTORIAL.md)** (in this folder)
- 👉 Reference tutorial: https://github.com/adityasharmadotai-hash/docs-reader-rag-agent/blob/main/TUTORIAL.md

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m "Add amazing feature"`
4. Push the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

Please keep PRs focused and include a short description of the change.

---

## 📄 License

Released under the **MIT License**. See the `LICENSE` file for details.

---

<div align="center">

**Built with ❤️ for founders, marketers, and product teams.**

⭐ If this project helped you, please consider giving it a star!

</div>
