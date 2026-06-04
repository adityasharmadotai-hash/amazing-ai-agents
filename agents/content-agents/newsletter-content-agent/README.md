# 🪶 Quill — Autonomous Newsletter Content Agent

Quill researches, curates, summarizes, and writes professional newsletters from across the web — RSS feeds, news sites, blogs, Reddit, YouTube, and social — then generates a complete, ready-to-send issue in the style and voice you choose. Built with Python, Streamlit, OpenAI, and SQLite.

> **Works with or without an API key.** Quill ships with seeded demo data and deterministic fallbacks, so the entire dashboard is fully explorable in **Demo Mode** the moment you launch it. Add an `OPENAI_API_KEY` to unlock live AI generation.

---

## ✨ Features

**Multi-source content collection** — Pull from RSS feeds, news websites, blogs, Reddit, Twitter/X, LinkedIn, YouTube channels, and company sites. Collection runs concurrently via a thread pool, and every item is de-duplicated by content hash and near-duplicate title matching.

**AI research engine** — For any topic, Quill surfaces trending content, removes duplicates, extracts key insights and hard statistics, clusters related stories, and produces a research summary.

**Full newsletter generation** — Produces a complete structured issue: title, subject line, introduction, key-insights section, industry updates, actionable takeaways, closing, and call-to-action.

**7 newsletter styles** — Founder, AI, Startup, Marketing, Recruiting, Technology, and Finance, each with its own audience, focus, and tone.

**5 writing modes** — Professional, Educational, Conversational, Technical, and Thought Leadership.

**Automation** — Schedule Daily, Weekly, or Monthly runs. Quill collects content, generates the issue, and saves a draft automatically (pull-based — runs on app load or on demand, no separate worker process needed).

**Email integration** — Gmail (SMTP), Mailchimp, ConvertKit, and Beehiiv. When credentials are absent, Quill returns the exact API payload / `.eml` draft so nothing breaks and you can inspect what *would* be sent.

**Analytics dashboard** — Sources used, trending topics, newsletters over time, engagement-by-style, and a transparent engagement-prediction score.

**Search & filters** — Filter content by topic, industry, date, source type, and free-text search.

**Export** — HTML (email-ready inline CSS), Markdown, PDF, and DOCX.

**AI assist studio** — Subject-line variations, CTA suggestions, newsletter hooks, content-gap recommendations, and future-issue ideas.

---

## 🏗️ Architecture

```
newsletter_agent/
├── app.py                      # Streamlit entry point — 9-page dashboard
├── config.py                   # All constants: model, styles, modes, sources, formats
├── requirements.txt
├── .env.example
└── modules/
    ├── database.py             # SQLite DAO (sources, content, newsletters, schedules, analytics, settings)
    ├── llm.py                  # OpenAI wrapper + JSON helpers, graceful no-key handling
    ├── content_sources.py      # Async collectors (RSS, web, Reddit, YouTube, social) + dedup
    ├── ai_research.py          # Trending scoring, insights, statistics, clustering
    ├── newsletter_generator.py # Structured issue generation + engagement estimate
    ├── ai_features.py          # Subject variations, CTAs, hooks, recommendations, ideas
    ├── exporters.py            # Markdown / HTML / PDF / DOCX
    ├── email_integration.py    # Gmail / Mailchimp / ConvertKit / Beehiiv adapters
    ├── scheduler.py            # Pull-based Daily/Weekly/Monthly automation
    ├── analytics.py            # Dashboard metrics (pure SQLite reads)
    ├── styles.py               # Dark "editorial" theme CSS
    └── seed_data.py            # Idempotent demo seeder
```

**Design principles**

- **Modular** — each concern lives in one module; `config.py` keeps the app declarative and easy to extend (add a style or source by editing a dict).
- **Graceful degradation** — no API key, no missing-library crash. Every AI call has a deterministic heuristic fallback; PDF/DOCX exporters report cleanly if their library is absent.
- **Concurrency** — content collection fans out across a `ThreadPoolExecutor`; the SQLite layer uses connection-per-call with a threading lock.
- **Transparency** — engagement scoring is an explainable heuristic, and email adapters expose the raw payload they would send.

---

## 🚀 Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) add your OpenAI key for live AI generation
cp .env.example .env
# edit .env and set OPENAI_API_KEY=sk-...

# 3. Launch
streamlit run app.py
```

Open the URL Streamlit prints (default `http://localhost:8501`). The app seeds demo sources, content, and newsletters on first run so you can explore everything immediately.

---

## ⚙️ Configuration

All settings are environment variables (see `.env.example`):

| Variable | Purpose | Default |
|---|---|---|
| `OPENAI_API_KEY` | Enables live AI generation | _none → Demo Mode_ |
| `OPENAI_MODEL` | Primary model | `gpt-4o` |
| `OPENAI_MODEL_FAST` | Lightweight tasks | `gpt-4o-mini` |
| `NEWSLETTER_DB` | SQLite path | `newsletter_agent.db` |
| `GMAIL_ADDRESS` / `GMAIL_APP_PASSWORD` | Gmail SMTP sending | _optional_ |
| `MAILCHIMP_API_KEY` / `MAILCHIMP_LIST_ID` | Mailchimp campaigns | _optional_ |
| `CONVERTKIT_API_SECRET` | ConvertKit broadcasts | _optional_ |
| `BEEHIIV_API_KEY` / `BEEHIIV_PUBLICATION_ID` | Beehiiv posts | _optional_ |

Email credentials can also be entered live in the **Settings** page.

---

## 🧱 Tech stack

Python · Streamlit · OpenAI · SQLite · feedparser · BeautifulSoup · reportlab · python-docx · async (ThreadPoolExecutor)

---

## 📄 License

Open source — released as part of the `amazing-ai-agents` collection. Use it, fork it, ship your own newsletter.
