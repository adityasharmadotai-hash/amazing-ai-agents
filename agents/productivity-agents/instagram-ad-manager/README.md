# 📈 Instagram AI Ad Manager

> An AI marketing assistant that monitors your Instagram lead-gen campaigns, explains the numbers in plain English, and recommends daily optimizations — built for recruiting **qualified job seekers in the San Francisco Bay Area** while cutting ad cost. Powered by **Google Gemini 2.5 Pro** + the **Meta Marketing API**.

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
| 📣 **Campaign Monitoring** | Every campaign with status, budget, spend, reach, impressions, clicks, CTR, CPC, **CPL**, leads, and conversion rate |
| 🧠 **AI Performance Analysis** | Gemini explains best/worst campaigns, what's improving vs declining, anomalies, and cost-saving opportunities |
| 💡 **Daily Recommendations** | Concrete actions (scale, pause, budget, new audience, better copy/CTA, A/B tests) — each with a reason |
| 🔁 **Continuous Learning** | Tracks whether each recommendation was implemented and whether performance improved or got worse |
| 👥 **Lead Monitoring** | Every Instagram lead with a one-click status editor (Qualified, Interview, Hired, Rejected, Duplicate, Invalid, No Response) |
| 🎯 **Learn From Feedback** | Finds which audiences, ages, and ads produce your highest-quality candidates |
| 📊 **Dashboard** | KPI cards + charts: spend, leads, CPL trend, CTR trend, qualified vs rejected, campaign comparison |
| 🔎 **Filters** | Today · Yesterday · 7 / 30 days · 10 weeks · custom range · by campaign · ad · lead status |
| 🗞️ **Daily Brief** | Overall health, biggest improvement, biggest concern, and recommended actions |
| 💬 **AI Assistant** | Ask "which campaign is best?", "why did CPL go up?", "compare this week to last" |

---

## Tech Stack

- **Streamlit** — dashboard UI
- **Google Gemini 2.5 Pro** (`google-generativeai`) — analysis, recommendations, chat
- **Meta Marketing API** (Graph API v21.0) — live campaigns, insights, and lead ads
- **SQLite** — local storage for the campaign cache, lead statuses, and recommendation history
- **Plotly + pandas** — charts and metrics

---

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the app → **Settings**:
- **Load sample data** to explore immediately, **or**
- add your keys (below) and **Sync live data from Meta**.

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
├── app.py                 # Streamlit UI (dashboard, pages, filters)
├── modules/
│   ├── meta_api.py        # Meta Marketing API client (campaigns, insights, leads)
│   ├── database.py        # SQLite schema + CRUD
│   ├── analytics.py       # CTR/CPC/CPL, trends, week-over-week, chart data
│   ├── agent.py           # Gemini 2.5 Pro: analysis, recommendations, chat
│   └── demo_seed.py       # Optional sample dataset
├── requirements.txt
└── .env.example
```

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
