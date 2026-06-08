# 🛰️ LinkedIn Opportunity Agent

An AI agent that monitors LinkedIn activity and automatically surfaces the
**high-value opportunities** hiding in your feed — so you stop spending hours
scrolling and start acting on the signals that matter.

It detects, scores, explains, and drafts outreach for:

- 🧑‍💻 **Hiring signals** — "we're hiring", open roles, team expansion
- 💰 **Buying intent** — "looking for a tool", vendor/RFP requests, evaluations
- 🤝 **Partnerships** — alliances, co-marketing, integration partners
- 🚀 **Funding** — seed / Series A-C announcements (fresh budget = new deals)
- 📥 **Leads & clients** — "who can help", agency/consultant requests
- 🌐 **Networking** — founder intros, events, communities
- 🧩 **Collaboration** — joint content, webinars, co-authoring

---

## ✨ Features

| # | Feature | What it does |
|---|---------|--------------|
| 1 | **LinkedIn monitoring** | Track profiles, company pages, keywords, industries & job titles |
| 2 | **Opportunity detection** | Classifies each post into one of 7 opportunity types from explicit signals |
| 3 | **AI analysis** | Summary · why it matters · recommended action · confidence score (Claude) |
| 4 | **Lead scoring** | High / Medium / Low based on relevance, engagement, industry match & buying intent |
| 5 | **Daily opportunity feed** | "Today's Opportunities", ranked by score |
| 6 | **AI outreach assistant** | Connection requests, first messages, follow-ups & intros — one-click sequences |
| 7 | **Search & filters** | By type, industry, date, score, company, person |
| 8 | **Analytics dashboard** | KPIs, top industries, hiring & funding trends, lead-score mix, history |
| 9 | **Alerts** | Daily & weekly email digests (SMTP) with in-app preview |
| 10 | **Settings** | API key, model, keywords, industries, monitored targets, email, manual ingestion |
| 11 | **SQLite database** | Opportunities, profiles, companies, messages & analytics history |
| 12 | **Modern UI** | Streamlit, sidebar navigation, KPI cards, charts, dark-mode-friendly |

---

## 🚀 Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app launches fully populated with realistic demo data — **no API key
required**. Without a key it runs a deterministic keyword/signal engine; add a
Claude API key for nuanced AI analysis and outreach.

### Add your Claude API key (optional but recommended)

- **Locally:** copy `.env.example` → `.env` and set `ANTHROPIC_API_KEY`, **or**
  paste the key on the in-app **Settings** page (stored only in your session).
- **Streamlit Cloud:** add `ANTHROPIC_API_KEY` under **Settings → Secrets**.

Get a key at <https://console.anthropic.com>.

---

## ☁️ Deploy on Streamlit Cloud

1. Push this folder to a GitHub repo.
2. On <https://share.streamlit.io>, create an app pointing at `app.py`.
3. Add your secrets:

   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   # optional:
   LINKEDIN_AGENT_MODEL = "claude-haiku-4-5"   # cheaper bulk scanning
   ```

4. Deploy. The SQLite database is created (and demo-seeded) automatically.

---

## 🔌 Using real LinkedIn data (important & honest)

LinkedIn has **no public posts API**, and scraping it with raw account
credentials violates their Terms of Service and is unreliable. This agent
therefore ships with:

- a **built-in simulation source** (realistic sample posts) so it works out of
  the box, and
- a **manual ingestion** box on the Settings page to paste real post text, and
- a **pluggable source interface** for compliant providers.

To wire in a live, compliant feed (an official partner API, an authorised data
export, or a licensed vendor), implement a fetch function and register it:

```python
from modules import monitor

def my_source(keywords, industries, limit):
    # return a list of dicts: {external_id, author_name, author_headline,
    # company, url, text, industry, posted_at}
    ...

monitor.set_source(my_source)
```

Everything downstream — detection, scoring, outreach, analytics — runs
identically on whatever posts are ingested.

---

## 🧱 Architecture

```
app.py                      # Streamlit entry · sidebar nav (st.navigation)
pages/
  home.py                   # Daily feed + scan trigger + KPIs
  opportunities.py          # Search, filters, triage, CSV export
  outreach.py               # AI outreach assistant
  analytics.py              # Charts, trends, email digests
  settings.py               # Config: key, model, targets, email, ingestion
modules/
  config.py                 # Secret/setting resolution (session → secrets → env)
  database.py               # SQLite persistence layer
  ai.py                     # Claude wrapper (sync + async) with JSON parsing
  detector.py               # Opportunity detection + lead scoring (AI + fallback)
  monitor.py                # Ingestion + async scan pipeline (pluggable source)
  samples.py                # Realistic demo posts / profiles / companies
  outreach.py               # Message generation (AI + templates)
  analytics.py              # Aggregations & trends (pandas)
  alerts.py                 # Email digests (SMTP)
  bootstrap.py              # Init + demo seeding
  ui.py                     # Shared styles & components
```

**Tech:** Python · Streamlit · Claude (Anthropic) API · SQLite · async ·
modular architecture · graceful fallback · environment-variable config.

---

## 🧠 How scoring works

Each opportunity gets a 0-100 score from four weighted components:

- **Relevance** — strength & number of opportunity signals in the post
- **Engagement** — questions, length, hashtags, mentions
- **Industry match** — alignment with your target industries
- **Buying intent** — budget/urgency/decision language

`≥ 75 → High`, `50-74 → Medium`, `< 50 → Low`.

---

## ⚠️ Notes

- Be a good citizen: use this to **prioritise genuine, personalised outreach** —
  not to spam. The outreach assistant is intentionally tuned for warm, concise,
  value-first messages.
- On Streamlit Cloud the SQLite file is ephemeral and resets on container
  restart; demo data re-seeds so the dashboard is never empty.
