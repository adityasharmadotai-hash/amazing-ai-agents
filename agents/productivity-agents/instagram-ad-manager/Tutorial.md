# 📈 Build an Instagram AI Ad Manager from Scratch

### A Step-by-Step Tutorial for Beginners to Intermediate Developers

---

<div align="center">

⭐ **[Star the repo](https://github.com/adityasharmadotai-hash)** &nbsp;·&nbsp;
🌐 **[adityasharma.ai](https://www.adityasharma.ai)** &nbsp;·&nbsp;
💼 **[LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)** &nbsp;·&nbsp;
📺 **[YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)** &nbsp;·&nbsp;
🚀 **[AI Jobs USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

</div>

---

> **What you'll build:** A premium Streamlit app that pulls live Instagram ad data
> from the Meta Marketing API, computes campaign metrics (CTR/CPC/CPL), a **marketing
> health score**, and a **7-day forecast**, then uses **Google Gemini 2.5 Pro** to
> analyze performance, recommend optimizations (with confidence + expected impact),
> propose ad creative, and answer questions. A modern Instagram-inspired UI, a
> **notification center**, and a **background sync job** (GitHub Actions) round it out.
> Data lives in SQLite so recommendations, lead statuses, and history persist.

> 🛠️ **Want the honest, first-person build story** — the wrong assumptions, the
> $990 cost-per-lead bug, the "Streamlit can't run itself" pivot, and the
> Cloud-only crash? Read **[DEVELOPMENT_JOURNEY.md](./DEVELOPMENT_JOURNEY.md)**.

---

## 📋 Table of Contents

1. [What Are We Building?](#1-what-are-we-building)
2. [How It Works](#2-how-it-works)
3. [Prerequisites](#3-prerequisites)
4. [Project Setup](#4-project-setup)
5. [File 1 — database.py](#5-file-1--databasepy)
6. [File 2 — meta_api.py](#6-file-2--meta_apipy)
7. [File 3 — analytics.py](#7-file-3--analyticspy)
8. [File 4 — agent.py](#8-file-4--agentpy)
9. [File 5 — app.py](#9-file-5--apppy)
10. [Getting Your Gemini Key](#10-getting-your-gemini-key)
11. [Getting Your Meta Access Token](#11-getting-your-meta-access-token)
12. [Running Locally](#12-running-locally)
13. [Deploying to Streamlit Cloud](#13-deploying-to-streamlit-cloud)
14. [Common Errors & Fixes](#14-common-errors--fixes)
15. [What You Learned](#15-what-you-learned)
16. [Premium Upgrade: Health, Forecast, Notifications](#16-premium-upgrade-health-forecast-notifications)
17. [Automating Sync with GitHub Actions](#17-automating-sync-with-github-actions)

---

## 1. What Are We Building?

Marketing teams running Instagram lead-gen ads face the same daily grind:

- Spend is scattered across many campaigns and it's hard to see what's working.
- Cost per lead creeps up and no one notices until the budget is gone.
- The best leads come from *some* audience or ad — but which one?
- Someone has to log into Ads Manager every morning and interpret the numbers.

This app is an **AI marketing analyst** that does that every day. It reads your
live campaign data, explains it in plain English, recommends what to change, and
learns from your team's feedback on lead quality — all aimed at getting **more
qualified Bay Area job seekers for less money**.

---

## 2. How It Works

```
Meta Marketing API ──► meta_api.py ──► SQLite (database.py)
                                          │
                                          ▼
                                    analytics.py  (CTR/CPC/CPL, trends)
                                          │
                                          ▼
              ┌───────────────────────────┴───────────────────────────┐
              ▼                                                         ▼
        agent.py (Gemini 2.5 Pro)                               app.py (Streamlit)
   analysis · recommendations · chat                       dashboard · leads · chat
```

- **meta_api.py** pulls campaigns, daily insights, and lead-ads from Meta.
- **database.py** caches them in SQLite and stores your lead statuses + AI history.
- **analytics.py** computes metrics deterministically (no AI) — so numbers are exact.
- **agent.py** hands *compact stats* (never raw dumps) to Gemini for the reasoning.
- **app.py** ties it together with a filterable dashboard and chat.

---

## 3. Prerequisites

- **Python 3.10+**
- A **Google AI Studio** account (free Gemini key)
- A **Meta Business** account with an ad account running Instagram lead ads
  *(optional — you can use the built-in sample data to follow along)*

```bash
pip install -r requirements.txt
```

`requirements.txt`:

```
streamlit>=1.50.0
google-generativeai>=0.8.0
requests>=2.31.0
plotly>=5.20.0
pandas>=2.2.0
python-dotenv>=1.0.0
python-dateutil>=2.9.0
```

---

## 4. Project Setup

```
instagram-ad-manager/
├── app.py
├── modules/
│   ├── __init__.py
│   ├── database.py
│   ├── meta_api.py
│   ├── analytics.py
│   ├── agent.py
│   └── demo_seed.py
├── requirements.txt
└── .env.example
```

Create a `.env` (copy from `.env.example`):

```
GEMINI_API_KEY=your_google_ai_studio_key
META_ACCESS_TOKEN=your_long_lived_meta_token
META_AD_ACCOUNT_ID=act_1234567890
```

---

## 5. File 1 — database.py

SQLite is perfect here: zero setup, one file, and it persists your lead statuses
and recommendation history between runs. We keep five tables:

- `campaigns` — the campaign list synced from Meta
- `metrics_daily` — one row per campaign/day/placement (the time series behind every chart)
- `leads` — each Instagram lead, with an **editable status** your team controls
- `recommendations` — every AI recommendation + whether it was implemented and if it helped
- `analyses` — stored AI outputs (so the last analysis shows instantly on reload)

The key idea for **continuous learning** is the `recommendations` table: each row
has a `status` (pending/implemented/dismissed) and an `outcome`
(improved/worse/neutral). Tomorrow's recommendations are generated with yesterday's
outcomes in the prompt — so the AI stops repeating what didn't work.

> See the full file in [`modules/database.py`](./modules/database.py). Note the
> `@st.cache_resource` connection and `check_same_thread=False` so Streamlit's
> threads can share one SQLite connection.

---

## 6. File 2 — meta_api.py

A thin `requests` wrapper over the Graph API (`https://graph.facebook.com/v21.0`).
Three jobs:

1. **Campaigns** — `GET /act_XXX/campaigns` (name, status, objective, budget).
2. **Insights** — `GET /act_XXX/insights?level=campaign&time_increment=1` for daily
   spend/reach/impressions/clicks, plus `actions` (we sum the `lead` action types).
   A second call with `breakdowns=publisher_platform,platform_position` gives the
   **Reels vs Feed** split.
3. **Lead ads** — for each ad, `GET /{ad_id}/leads` and flatten `field_data` into
   name/email/phone.

Everything degrades gracefully: `is_configured()` returns `False` when secrets are
missing, and every failure raises a typed `MetaAPIError` the UI can catch — so a
missing token shows a friendly "connect your account" message instead of a crash.

```python
def _leads_from_actions(actions):
    total = 0.0
    for a in actions or []:
        if a.get("action_type") in _LEAD_ACTION_TYPES:
            total += float(a.get("value", 0))
    return int(round(total))
```

> Full file: [`modules/meta_api.py`](./modules/meta_api.py).

---

## 7. File 3 — analytics.py

Do the math in Python, not in the model. This module turns raw rows into:

- The **per-campaign table** (CTR, CPC, CPL, conversion rate).
- **Dashboard KPIs** (total/today spend, qualified vs rejected, best/worst campaign).
- **Time series** for the charts, and **week-over-week deltas** (that's how we say
  "CPL increased 18%").
- **Placement** (Reels/Feed/Stories) and **lead-quality** breakdowns (by audience,
  age, ad, campaign) — the raw material for §6 learning.

```python
def cpl(spend, leads):        # cost per lead
    return round(spend / leads, 2) if leads else 0.0
```

`build_stats_payload()` packs all of this into one compact, JSON-serializable dict.
That dict — not the raw database — is what we send to Gemini.

> Full file: [`modules/analytics.py`](./modules/analytics.py).

---

## 8. File 4 — agent.py

This is where **Gemini 2.5 Pro** comes in. We configure the SDK and ask for JSON:

```python
import google.generativeai as genai

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    "gemini-2.5-pro",
    generation_config={"temperature": 0.4, "response_mime_type": "application/json"},
)
resp = model.generate_content(prompt)
```

Five functions, each fed the compact stats:

- `analyze_performance()` → best/worst, improving/declining, anomalies, opportunities
- `daily_recommendations()` → typed actions with a rationale, **aware of past outcomes**
- `learn_from_leads()` → what distinguishes high- vs low-quality lead sources
- `daily_summary()` → the morning brief (health, wins, concerns, actions)
- `chat()` → free-form Q&A grounded only in your data

A persona string keeps every answer on-task: *"You are the marketing analyst for a
recruiting company running Instagram lead ads for Bay Area job seekers… increase
qualified applicants while reducing cost… never invent data."*

> Full file: [`modules/agent.py`](./modules/agent.py).

---

## 9. File 5 — app.py

The Streamlit front end: a sidebar with navigation + the global **filters**
(Today / Yesterday / 7d / 30d / 10 weeks / custom / by campaign / ad / status), and
eight pages — Dashboard, Campaigns, Leads, AI Analysis, Recommendations, Daily
Brief, AI Assistant, and Settings.

Two patterns worth copying:

- **Editable leads** via `st.data_editor` with a `SelectboxColumn` for status; on
  each rerun we diff the edited rows against the DB and persist changes.
- **Cheap empty-state**: if there's no data and you're not on Settings, show a
  friendly prompt and `st.stop()`.

> Full file: [`app.py`](./app.py).

---

## 10. Getting Your Gemini Key

1. Go to **[aistudio.google.com/apikey](https://aistudio.google.com/apikey)**.
2. Click **Create API key** (free tier is fine to start).
3. Paste it into `.env` as `GEMINI_API_KEY=...`.

That's all the AI features need.

---

## 11. Getting Your Meta Access Token

Live campaign sync needs a token with the right scopes. The quickest path:

1. Create an app at **[developers.facebook.com](https://developers.facebook.com/)**
   → *My Apps* → *Create App* → type **Business**.
2. Add the **Marketing API** product.
3. Open **Graph API Explorer**, select your app, and request these permissions:
   `ads_read`, `ads_management` (optional), `leads_retrieval`, `pages_show_list`,
   `pages_read_engagement`.
4. Generate a **User Token**, then exchange it for a **long-lived token** (valid ~60
   days) via *Access Token Debugger → Extend Access Token*.
5. Find your **ad account id** in Ads Manager (format `act_1234567890`).

Put both in `.env`:

```
META_ACCESS_TOKEN=EAAG...long_lived...
META_AD_ACCOUNT_ID=act_1234567890
```

> **Leads not showing up?** Lead retrieval is permission-sensitive: the token must
> have `leads_retrieval` **and** the connected Page must grant your app access. For
> production, use a **System User** token so it doesn't expire.

---

## 12. Running Locally

```bash
streamlit run app.py
```

Open the app → **Settings**:

- **Load sample data** to explore instantly (no keys needed), **or**
- **Sync live data from Meta** (with your token) to pull real campaigns.

Then walk the pages: **Dashboard** for the numbers, **AI Analysis** and
**Recommendations** for Gemini's read, **Leads** to mark quality, **AI Assistant**
to just ask.

---

## 13. Deploying to Streamlit Cloud

1. Push this folder to GitHub.
2. On **[share.streamlit.io](https://share.streamlit.io)**, create an app pointing at
   `app.py`.
3. In **Settings → Secrets**, add (TOML format):

```toml
GEMINI_API_KEY = "your_google_ai_studio_key"
META_ACCESS_TOKEN = "your_long_lived_meta_token"
META_AD_ACCOUNT_ID = "act_1234567890"
```

4. Deploy ✅

> **Heads-up:** Streamlit Cloud's filesystem is **ephemeral** — the SQLite file
> resets on every redeploy. That's fine for a demo (just re-sync), but for durable
> multi-user use, swap `database.py` for a hosted Postgres/Supabase.
>
> If the build fails on the Python version, pin **Python 3.12** in the app's
> *Advanced settings* rather than loosening the dependency pins.

---

## 14. Common Errors & Fixes

| Error | Fix |
|-------|-----|
| `No campaign data yet` | Settings → **Load sample data**, or add Meta keys and **Sync** |
| `GEMINI_API_KEY is not set` | Add the key to `.env` / Secrets and reload |
| `Meta API error (190)` | Token expired — regenerate a long-lived (or System User) token |
| `(#100) nonexisting field` / empty results | Ad account id must include the `act_` prefix |
| No leads after a successful sync | Token needs `leads_retrieval` **and** a Page grant |
| `429 / rate limit` | Reduce the sync window (Settings slider) and retry |
| Data resets after redeploy | Expected on Streamlit Cloud — re-sync or move to Postgres |
| `Invalid format: TOML` | In Secrets use `KEY = "value"` **with quotes** |

---

## 15. What You Learned

- Pulling **live ad data** from the Meta Marketing API (campaigns, insights, lead ads)
- Separating **deterministic metrics** (Python) from **reasoning** (the LLM)
- Driving **Gemini 2.5 Pro** with JSON output and a focused persona
- Building a **continuous-learning loop**: store recommendations → track outcomes →
  feed them back into tomorrow's prompt
- Shipping it all as a filterable **Streamlit** dashboard with editable leads and chat

---

## 16. Premium Upgrade: Health, Forecast, Notifications

The app grew from a solid dashboard into a **Premium AI Marketing Assistant**. The key
additions, and where they live:

- **Design system** — [`modules/theme.py`](./modules/theme.py) holds the Instagram-gradient
  glassmorphism CSS plus HTML builders (`kpi_card`, `hero`, `section`, pills). [`modules/ui.py`](./modules/ui.py)
  wraps Streamlit + Plotly with a consistent chart theme, a health gauge, and a forecast chart.
- **Marketing health score** — `analytics.marketing_health()` blends cost efficiency, lead
  quality, momentum (week-over-week), CTR, conversion, and consistency into a weighted 0–100
  grade with a component breakdown. Fully deterministic, so the number is reproducible.
- **Forecasting** — `analytics.forecast()` fits a linear trend (numpy) over recent daily data
  to project the next 7 days of spend, leads, and CPL with an 80% band.
- **Richer AI** — `agent.py` gained `creative_suggestions()`, `audience_recommendations()`,
  `executive_summary()`, and `forecast_narrative()`, and `daily_recommendations()` now returns
  a **confidence score** and **expected impact** for each action.
- **Notifications** — `sync_service.generate_notifications()` turns thresholds (CPL spikes, lead
  drops, top performers, health changes) into alerts stored in a `notifications` table and shown
  in the Notification Center.
- **Performance** — every DB write bumps a `data_version` counter; Streamlit's `@st.cache_data`
  loaders key on it, so reads are cached and auto-invalidate on any change. `database.py` also
  gained indexes and idempotent column migrations.

> Nothing was removed — the original Dashboard, Campaigns, Leads, AI Analysis, Recommendations,
> and Assistant all still work, just prettier and faster.

---

## 17. Automating Sync with GitHub Actions

Streamlit **cannot** run background jobs, so the periodic work lives in a standalone script,
[`sync.py`](./sync.py), which calls [`modules/sync_service.py`](./modules/sync_service.py) —
the same pipeline the in-app **Sync Now** button uses.

```bash
python sync.py --days 70          # live Meta sync + Gemini AI
python sync.py --no-ai            # data only
python sync.py --sample           # seed demo data (no Meta needed)
```

A full sync: pulls campaigns/insights/leads → recomputes analytics + health → runs Gemini
analysis, recommendations, lead-learning, and an executive summary → generates notifications →
records a `sync_log` row and the last-sync time. If the AI stage fails, the sync degrades to
**partial** rather than losing the freshly pulled data.

### The workflow

`.github/workflows/instagram-ad-manager-sync.yml` (at the **repo root** — Actions only run from
there) is scheduled daily and can be run on demand:

```yaml
on:
  schedule:
    - cron: "0 13 * * *"   # daily 13:00 UTC
  workflow_dispatch: { }
```

It checks out the repo, installs deps, runs `python sync.py`, then **commits the refreshed
`data/admanager.db` back** so a Streamlit Cloud deployment auto-redeploys with fresh data.

**Set up:**
1. Repo **Settings → Secrets and variables → Actions** → add `GEMINI_API_KEY`,
   `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID`.
2. Open the **Actions** tab and run *Instagram Ad Manager — scheduled sync* once (*Run workflow*).
3. It then runs automatically on the cron schedule.

> **Persistence tip:** committing a binary DB works for a demo, but for heavier use point
> `ADMANAGER_DB_PATH` at a mounted disk or swap SQLite for hosted Postgres. Then the workflow
> only needs to run the sync — no commit-back required.

**cron / Task Scheduler** are drop-in alternatives — schedule the same `python sync.py` command.

---

## ⭐ If you found this useful

- ⭐ **[Star the repository](https://github.com/adityasharmadotai-hash)**
- 🌐 **[Visit adityasharma.ai](https://www.adityasharma.ai)** — AI training for professionals
- 💼 **[Follow on LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)**
- 📺 **[Subscribe on YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)**
- 🚀 **[AI Jobs in the USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

---

*Built with ❤️ by [Aditya Sharma](https://www.adityasharma.ai) · Google Gemini 2.5 Pro + Meta Marketing API + Streamlit*
