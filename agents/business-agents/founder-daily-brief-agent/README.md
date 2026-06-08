# ☀️ Founder Daily Brief Agent

> Stop checking Gmail, Calendar, Notion, Slack & Stripe every morning. One AI dashboard pulls them all into a single daily briefing — important emails, meetings, follow-ups, revenue, risks, and your suggested focus for the day.

---

<div align="center">

⭐ **[Star the repo](https://github.com/adityasharmadotai-hash)** &nbsp;·&nbsp;
🌐 **[adityasharma.ai](https://www.adityasharma.ai)** &nbsp;·&nbsp;
💼 **[LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)** &nbsp;·&nbsp;
📺 **[YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)**

</div>

---

**👉 STEP-BY-STEP TUTORIAL: [Tutorial.md](./Tutorial.md)**

---

## What it does

Every morning a founder juggles 7 tabs. This agent collapses them into **one brief**:

```
Good Morning Aditya 👋

Meetings Today: 4     Important Emails: 4     Pending Follow-Ups: 7
Customer Issues: 2    Open Actions: 8         Revenue Yesterday: $1,349

🎯 Suggested Focus:
Finalise the ABC Corp proposal pricing, follow up with Priya & Marcus,
and resolve Northwind's stale-dashboard issue before it hits their board prep.
```

## Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | ☀️ **Daily Founder Brief** | Greeting, 6 headline metrics, executive summary, highlights, watch-outs, and an AI-suggested focus |
| 2 | 📧 **Gmail / Inbox** | Important-email detection, unread summaries, follow-up flags, priority + category, customer-issue triage |
| 3 | 📅 **Google Calendar** | Today's schedule, meeting load, and one-click **AI meeting-prep briefs** |
| 4 | 📝 **Notion** | Open tasks, blocked items, projects, due dates — add/complete tasks inline |
| 5 | 💬 **Slack** | Mentions, unanswered messages, important threads by channel |
| 6 | 💰 **Revenue** | Stripe & Razorpay-style feed, MRR estimate, 14-day trend, manual entry |
| 7 | 🧠 **AI Insights** | Priorities, risks, opportunities, follow-up recs, recommended next actions |
| 8 | 📊 **Analytics** | Inbox health, productivity, task-completion, meeting load, follow-up status, charts |
| 9 | 🔍 **Search Assistant** | Ask "what needs my attention today?", "which clients need follow-up?", etc. |
| 10 | 🔑 **Settings** | OpenAI API key, founder profile, connection toggles, demo-data reset |

**Works with zero setup** — rich demo data is seeded on first run, and every AI feature has a deterministic rule-based fallback. Add an OpenAI key to upgrade the briefs, insights, and answers to GPT-4o quality.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the **🔑 Settings** page and paste your OpenAI key (optional — the app runs without it).

To configure the key via environment instead:

```bash
echo 'OPENAI_API_KEY=sk-...' > .env
```

## Deploy to Streamlit Cloud

Add to your app secrets:

```toml
OPENAI_API_KEY = "sk-your-key"
```

## Structure

```
founder-daily-brief-agent/
├── app.py                 # 10-page Streamlit dashboard
├── modules/
│   ├── ai.py              # OpenAI wrapper + key resolution
│   ├── connectors.py      # Gmail/Calendar/Notion/Slack/revenue data + scores
│   ├── brief.py           # AI brief, insights, assistant, meeting prep (+ fallbacks)
│   └── storage.py         # Founder profile & connection settings
├── requirements.txt
├── .env.example
└── .streamlit/config.toml
```

## Connecting real tools

The `seed_*` functions in [`modules/connectors.py`](./modules/connectors.py) are the integration points. Replace each one's body with a real API call (Gmail OAuth, Google Calendar, Notion, Slack, Stripe/Razorpay) returning the same shape, and the rest of the app — brief, insights, analytics, assistant — keeps working unchanged.

## Cost

Free in rule-based mode. With a key: ~$0.01–0.02 per full brief + insights (GPT-4o), a fraction of a cent per assistant answer.

---

*Built with ❤️ by [Aditya Sharma](https://www.adityasharma.ai)*
