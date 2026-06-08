<div align="center">

⭐ **[Star the repo](https://github.com/adityasharmadotai-hash/amazing-ai-agents)** &nbsp;·&nbsp;
💼 **[Follow on LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)** &nbsp;·&nbsp;
📺 **[Subscribe on YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)** &nbsp;·&nbsp;
🚀 **[AI Jobs in the U.S. — Apply here](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

</div>

---

# ☀️ Founder Daily Brief Agent

> An AI executive dashboard that pulls Gmail, Calendar, Notion, Slack & revenue into **one daily briefing** — so founders stop checking 7 tools every morning.

---

## 📌 Overview

Every morning a founder opens seven tabs: Gmail for important emails, Calendar for meetings, Notion for tasks, Slack for mentions, Stripe for revenue, and more. The context-switching is exhausting and it's easy to miss the one thing that actually matters today.

**Founder Daily Brief Agent** collapses all of that into a single screen. It collects information from every business tool, uses AI to find the signal in the noise, and presents a clean briefing:

```
Good Morning Aditya 👋

Meetings Today: 4     Important Emails: 4     Pending Follow-Ups: 7
Customer Issues: 2    Open Actions: 8         Revenue Yesterday: $1,349

🎯 Suggested Focus:
Finalise the ABC Corp proposal pricing, follow up with Priya & Marcus,
and resolve Northwind's stale-dashboard issue before it hits their board prep.
```

**The problem it solves:** founders waste the most valuable part of their day — the first hour — gathering context instead of acting on it. This agent does the gathering, prioritising, and summarising for you.

> 💡 **Runs with zero setup.** Rich demo data is seeded on first launch, and every AI feature has a deterministic rule-based fallback — so the dashboard is fully usable even without an OpenAI key. Add a key to upgrade the briefs and answers to GPT-4o quality.

<img width="1903" height="780" alt="image" src="https://github.com/user-attachments/assets/c5246871-997d-47cd-9bb9-a228ce014ebb" />

---

<img width="1858" height="813" alt="image" src="https://github.com/user-attachments/assets/fba1a38f-780d-4da3-943c-d58a38dc718a" />

---

## ✨ Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | ☀️ **Daily Founder Brief** | Greeting, 6 headline metrics, executive summary, highlights, watch-outs, and an AI-suggested focus for the day |
| 2 | 📧 **Gmail / Inbox** | Important-email detection, unread summaries, follow-up flags, priority + category, customer-issue triage |
| 3 | 📅 **Google Calendar** | Today's schedule, meeting load, and one-click **AI meeting-prep briefs** |
| 4 | 📝 **Notion** | Open tasks, blocked items, projects, due dates — add and complete tasks inline |
| 5 | 💬 **Slack** | Mentions, unanswered messages, and important threads grouped by channel |
| 6 | 💰 **Revenue** | Stripe & Razorpay-style feed, MRR estimate, 14-day trend chart, manual entry |
| 7 | 🧠 **AI Insights** | Priorities, risks, opportunities, follow-up recommendations, recommended next actions |
| 8 | 📊 **Analytics** | Inbox health, productivity, task completion, meeting load, follow-up status + charts |
| 9 | 🔍 **Search Assistant** | Ask "what needs my attention today?", "which clients need follow-up?", etc. |
| 10 | 🔑 **Settings** | OpenAI API key, founder profile, connection toggles, demo-data reset |

---

## ⚙️ How It Works

The app reads from each business tool through a **connector layer**, merges everything into one unified snapshot, and hands that snapshot to an **AI brain** that produces the brief, insights, and answers.

```
   ┌─────────┐  ┌──────────┐  ┌────────┐  ┌────────┐  ┌──────────────┐
   │  Gmail  │  │ Calendar │  │ Notion │  │ Slack  │  │ Stripe/Razor │
   └────┬────┘  └────┬─────┘  └───┬────┘  └───┬────┘  └──────┬───────┘
        │            │            │           │              │
        └────────────┴─────┬──────┴───────────┴──────────────┘
                           ▼
                ┌──────────────────────┐
                │   connectors.py      │   normalises every source +
                │   collect_context()  │   computes health/revenue scores
                └──────────┬───────────┘
                           ▼
                ┌──────────────────────┐
                │      brief.py        │   GPT-4o (or rule-based fallback):
                │  brief · insights ·  │   prioritise, summarise, advise
                │  assistant · prep    │
                └──────────┬───────────┘
                           ▼
                ┌──────────────────────┐
                │       app.py         │   10-page Streamlit dashboard
                │  (Streamlit UI)      │
                └──────────────────────┘
```

1. **Collect** — each `seed_*` connector returns normalised records (emails, meetings, tasks, messages, transactions).
2. **Aggregate** — `collect_context()` merges them and derives scores (inbox health, productivity, MRR, meeting load).
3. **Reason** — `brief.py` sends the snapshot to GPT-4o to generate the brief, insights, and answers (with rule-based fallbacks).
4. **Present** — `app.py` renders everything across 10 themed pages.

---

## 🧰 Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| UI / Frontend | [Streamlit](https://streamlit.io) | Pure-Python dashboards, no JS required |
| AI / LLM | [OpenAI GPT-4o](https://platform.openai.com) | Brief generation, insights, Q&A |
| Charts | [Plotly](https://plotly.com/python/) | Interactive revenue & analytics charts |
| Config | [python-dotenv](https://pypi.org/project/python-dotenv/) | Load `OPENAI_API_KEY` from `.env` |
| State | `st.session_state` | In-session storage — no database needed |
| Language | Python 3.9+ | — |

---

## 📁 File Structure

```
founder-daily-brief-agent/
├── app.py                 # 10-page Streamlit dashboard (UI + routing)
├── modules/
│   ├── __init__.py        # package marker
│   ├── ai.py              # OpenAI wrapper + API-key resolution
│   ├── connectors.py      # Gmail/Calendar/Notion/Slack/revenue data + scores
│   ├── brief.py           # AI brief, insights, assistant, meeting prep (+ fallbacks)
│   └── storage.py         # Founder profile & connection settings
├── requirements.txt       # Python dependencies
├── .env.example           # template for your OpenAI key
├── .gitignore
├── .streamlit/
│   └── config.toml        # theme + server config
├── README.md
└── TUTORIAL.md            # step-by-step beginner guide
```

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/adityasharmadotai-hash/amazing-ai-agents.git
cd amazing-ai-agents/agents/business-agents/founder-daily-brief-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run it

```bash
streamlit run app.py
```

Your browser opens at `http://localhost:8501`. The app works immediately with seeded demo data.

### 4. (Optional) Add your OpenAI key

Open the **🔑 Settings** page and paste your key (starts with `sk-`), **or** create a `.env` file:

```bash
echo 'OPENAI_API_KEY=sk-your-key-here' > .env
```

Get a key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys).

---

## ☁️ Deployment (Streamlit Community Cloud)

1. Push your fork to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Select your repo and set the main file path to:
   ```
   agents/business-agents/founder-daily-brief-agent/app.py
   ```
4. Under **Advanced settings → Secrets**, add your key:
   ```toml
   OPENAI_API_KEY = "sk-your-key"
   ```
5. Click **Deploy**. Your founder brief is live. ☀️

---

## 🔌 Connecting Real Tools

The `seed_*` functions in [`modules/connectors.py`](./modules/connectors.py) are the integration points. Replace each one's body with a real API call returning the same record shape — Gmail OAuth, Google Calendar, Notion, Slack, Stripe/Razorpay — and the brief, insights, analytics, and assistant keep working unchanged.

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push and open a Pull Request

Please keep the code style consistent with the existing modules and test that `streamlit run app.py` works before submitting.

---

## 📄 License

Released under the **MIT License** — free to use, modify, and distribute.

---

## 📘 Tutorial

New to this? Follow the full step-by-step guide:
**👉 [TUTORIAL.md](https://github.com/adityasharmadotai-hash/docs-reader-rag-agent/blob/main/TUTORIAL.md)**

---

<div align="center">

*Built with ❤️ by [Aditya Sharma](https://www.adityasharma.ai)*

⭐ **[Star the repo](https://github.com/adityasharmadotai-hash/amazing-ai-agents)** if this helped you!

</div>
