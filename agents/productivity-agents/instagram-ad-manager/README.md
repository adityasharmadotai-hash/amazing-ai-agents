# 📈 Instagram AI Ad Manager — Premium AI Marketing Assistant

> An enterprise-grade AI marketing assistant that monitors your Instagram lead-gen campaigns, scores their health, forecasts the week ahead, explains everything in plain English, and recommends optimizations with confidence + expected impact — built for recruiting **qualified job seekers in the San Francisco Bay Area** while cutting ad cost. Powered by **Google Gemini 2.5 Pro** + the **Meta Marketing API**, with a modern Instagram-inspired UI.

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

Stop guessing which ads to scale and which to kill. This app pulls your live
Instagram (Meta) ad data, then a Gemini 2.5 Pro analyst reviews it every day:
which campaigns win, which are slipping, where cost per lead is creeping up, and
what to change — all in language a marketer can act on. It also learns from your
team's lead-quality feedback, so its recommendations get sharper over time.

> **No Meta account handy?** Click **Settings → Load sample data** to explore the
> full dashboard, charts, and AI features with a realistic 10-week demo dataset.

---

## Features

| Feature | Description |
|---------|-------------|
| ❤️ **Marketing Health Score** | A single 0–100 grade from a weighted blend of cost efficiency, lead quality, momentum, CTR, conversion, and consistency |
| 🔮 **7-Day Forecast** | Projected spend, leads, and CPL with an 80% confidence band, plus an AI plain-English outlook |
| 🧠 **AI Performance Analysis** | Gemini explains best/worst campaigns, improving vs declining, anomalies, and cost-saving opportunities |
| 💡 **Smart Recommendations** | Actions with **confidence score**, **expected impact**, and priority — and outcome tracking that feeds tomorrow's advice |
| 🎯 **Audience Insights** | Which audiences, ages, and ads produce your highest-quality candidates + an AI targeting plan |
| 🎨 **Creative Studio** | AI-generated ad concepts (format, hook, caption, CTA) tuned to your best-performing data |
| 🔔 **Notification Center** | Automatic alerts on every sync (CPL spikes, lead drops, top performers, health changes) |
| 🗞️ **Executive Brief** | Leadership-ready summary: health read, wins, risks, forecast note, and weekly priorities |
| 📣 **Campaign Monitoring** | Every campaign with status, budget, spend, reach, impressions, clicks, CTR, CPC, **CPL**, leads, conversion |
| 👥 **Lead Monitoring** | Every Instagram lead with a one-click status editor; the AI learns from your feedback |
| 📊 **Premium Dashboard** | Glassmorphism KPI cards with week-over-week deltas + themed Plotly charts |
| 💬 **AI Assistant** | Ask "which campaign is best?", "why did CPL go up?", "compare this week to last" |
| 🔎 **Filters** | Today · Yesterday · 7 / 30 days · 10 weeks · custom range · by campaign · ad · lead status |
| 🔄 **Background Sync** | A separate script (GitHub Actions / cron / Task Scheduler) keeps data fresh; the app shows the latest sync + a **Sync Now** button |

---

## Tech Stack

- **Streamlit** — premium dashboard UI (Instagram-inspired glassmorphism theme)
- **Google Gemini 2.5 Pro** (`google-generativeai`) — analysis, recommendations, creative, chat
- **Meta Marketing API** (Graph API v21.0) — live campaigns, insights, and lead ads
- **SQLite** — campaign cache, lead statuses, recommendation history, notifications, sync log
- **Plotly + pandas + numpy** — charts, metrics, and forecasting
- **GitHub Actions** — scheduled background sync (see `sync.py`)

---

## Architecture

```
Meta Marketing API ─┐
                    ├─► sync.py / sync_service.py ─► SQLite ◄─► app.py (Streamlit)
Gemini 2.5 Pro ─────┘        (background job)                    (Sync Now + display)
```

The heavy lifting (pull data → run AI → generate recommendations & notifications →
compute health) runs in **`sync.py`**, scheduled by GitHub Actions. Streamlit reads
the latest synchronized data and offers a manual **Sync Now**. All reads are cached
and auto-invalidate on any write via a data-version counter.

---

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the app → **Settings**:
- **Load sample data** to explore immediately, **or**
- add your keys (below) and **Sync from Meta + AI**.

Run the background sync manually any time:

```bash
python sync.py --sample --no-ai     # demo data, no API keys needed
python sync.py --days 70            # live Meta sync + Gemini (uses env vars)
```

### Keys (`.env` locally, or Streamlit **Secrets** when deployed)

```
GEMINI_API_KEY=your_google_ai_studio_key
META_ACCESS_TOKEN=your_long_lived_meta_token
META_AD_ACCOUNT_ID=act_1234567890
```

- **Gemini key** → [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- **Meta token + account id** → see **[Tutorial.md](./Tutorial.md)** for the full walkthrough (needs `ads_read` + `leads_retrieval`).

> The AI features need only the Gemini key. Live campaign sync needs the Meta
> credentials. The sample data needs neither.

---

## Project Structure

```
instagram-ad-manager/
├── app.py                 # Premium Streamlit UI (13 pages, filters, Sync Now, caching)
├── sync.py                # Background sync CLI (GitHub Actions / cron / Task Scheduler)
├── modules/
│   ├── theme.py           # Design system: Instagram-gradient glassmorphism CSS + HTML builders
│   ├── ui.py              # Streamlit + Plotly render helpers (charts, gauge, notifications)
│   ├── config.py          # Constants, benchmarks, logging
│   ├── meta_api.py        # Meta Marketing API client (campaigns, insights, leads)
│   ├── database.py        # SQLite schema, migrations, versioned CRUD, notifications, sync log
│   ├── analytics.py       # CTR/CPC/CPL, trends, health score, forecasting, audience insights
│   ├── agent.py           # Gemini 2.5 Pro: analysis, recommendations, creative, exec summary, chat
│   ├── sync_service.py    # Full sync orchestration (shared by sync.py and Sync Now)
│   └── demo_seed.py       # Optional sample dataset
├── requirements.txt
└── .env.example
# repo root: .github/workflows/instagram-ad-manager-sync.yml  (scheduled sync)
```

---

## Automated Background Sync

Streamlit **cannot** run autonomous jobs, so a standalone script does the periodic work.

- **GitHub Actions (preferred):** `.github/workflows/instagram-ad-manager-sync.yml` (at the
  repo root) runs daily, executes `python sync.py`, and commits the refreshed database back so
  the deployed app shows fresh data. Add `GEMINI_API_KEY`, `META_ACCESS_TOKEN`, and
  `META_AD_ACCOUNT_ID` as repository **Secrets**, then optionally run it once from the
  **Actions** tab (*Run workflow*).
- **cron (Linux/macOS):** `0 6 * * *  cd /path/app && python sync.py --days 70`
- **Task Scheduler (Windows):** run `python sync.py --days 70` on a daily trigger.

Set `ADMANAGER_DB_PATH` to a shared/persistent path so the job and the app use one database.
The **Sync Now** button in the app runs the exact same pipeline on demand.

---

## Common Errors & Fixes

| Error | Fix |
|-------|-----|
| `No campaign data yet` | Settings → **Load sample data**, or add Meta keys and **Sync** |
| `GEMINI_API_KEY is not set` | Add the key to `.env` / Streamlit Secrets and reload |
| `Meta API error (190)` | Access token expired — regenerate a long-lived token (see Tutorial) |
| `(#100) ... nonexisting field` | Wrong ad account id — include the `act_` prefix |
| No leads after sync | Your token needs the **`leads_retrieval`** permission and a page-scoped grant |
| Data disappears after redeploy | Streamlit Cloud's disk is ephemeral — re-sync, or move storage to Postgres |

---

## ⭐ If you found this useful

- ⭐ **[Star the repository](https://github.com/adityasharmadotai-hash)**
- 🌐 **[Visit adityasharma.ai](https://www.adityasharma.ai)** — AI training for professionals
- 💼 **[Follow on LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)**
- 📺 **[Subscribe on YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)**
- 🚀 **[AI Jobs in the USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

---

*Built with ❤️ by [Aditya Sharma](https://www.adityasharma.ai) · Google Gemini 2.5 Pro + Meta Marketing API + Streamlit*
