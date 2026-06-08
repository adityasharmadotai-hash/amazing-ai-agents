# 📘 Tutorial — Founder Daily Brief Agent

A complete walkthrough: from install to your first AI-powered morning brief.

---

## 1. Install

You need **Python 3.9+**.

```bash
cd agents/business-agents/founder-daily-brief-agent
pip install -r requirements.txt
```

## 2. Run

```bash
streamlit run app.py
```

Your browser opens at `http://localhost:8501`. The app is **immediately usable** — it seeds a realistic founder's morning (emails, meetings, tasks, Slack, revenue) so you can explore every page before connecting anything.

## 3. (Optional) Add your OpenAI key

The app runs in **rule-based mode** with no key. To unlock GPT-4o briefs, insights, and the natural-language assistant:

1. Get a key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys) (starts with `sk-`).
2. Open the **🔑 Settings** page → paste it under *OpenAI API Key* → **Save Key**.

The key lives only in your browser session — it's never written to disk. You can also set `OPENAI_API_KEY` in a `.env` file or Streamlit secrets.

---

## 4. The pages

### ☀️ Daily Brief
Your command center. Six headline metrics, an executive summary, today's highlights, watch-outs, and the single **Suggested Focus** for the day. Hit **🔄 Regenerate** any time.

### 📧 Inbox
Gmail-style triage. Filter by Unread / Important / Needs Follow-Up / Customer Issues. Each email shows priority, category, and follow-up/issue flags. The **Inbox Health** score summarizes how on-top-of-it you are.

### 📅 Calendar
Today's schedule with meeting load in hours. Expand any meeting and click **🧠 Generate AI Prep Brief** for an objective, talking points, likely questions, and the desired outcome — built from related emails.

### 📝 Notion
Tasks and projects. Filter to open / blocked / high-priority, add a task inline, and mark items done. Tracks completion rate and blocked items.

### 💬 Slack
Mentions, unanswered messages, and important threads grouped by channel.

### 💰 Revenue
Stripe & Razorpay-style transaction feed with a 14-day trend chart, MRR estimate, and 7/30-day totals. Add manual entries or delete rows.

### 🧠 AI Insights
Priorities, risks, opportunities, follow-up recommendations, and recommended next actions — synthesized across all your tools.

### 📊 Analytics
Inbox health, productivity, task completion, meeting load, and follow-up status, with charts for task status and revenue by source.

### 🔍 Ask
Type or tap a suggestion:
- *What needs my attention today?*
- *Which clients need follow-up?*
- *What meetings do I have today?*
- *What are the biggest risks this week?*
- *Show revenue summary.*

### 🔑 Settings
API key, founder profile (name, company, role, currency), connection toggles, and a **Reset demo data** button.

---

## 5. Connect your real tools

Open [`modules/connectors.py`](./modules/connectors.py). Each data source is a `seed_*` function returning a list of dicts. Swap the body for a real API call that returns the **same shape**:

| Function | Replace with |
|----------|--------------|
| `_seed_emails` | Gmail API (`users.messages.list` + parse) |
| `_seed_meetings` | Google Calendar `events.list` |
| `_seed_tasks` | Notion `databases.query` |
| `_seed_slack` | Slack `conversations.history` / mentions |
| `_seed_revenue` | Stripe `charges`/`subscriptions`, Razorpay payments |

Everything downstream — the brief, insights, analytics, and assistant — consumes the unified snapshot from `collect_context()`, so no other code changes are needed.

---

## 6. Deploy

Push to GitHub and deploy on [Streamlit Community Cloud](https://streamlit.io/cloud). Add your key under **App → Settings → Secrets**:

```toml
OPENAI_API_KEY = "sk-your-key"
```

That's it — your founder brief is live. ☀️
