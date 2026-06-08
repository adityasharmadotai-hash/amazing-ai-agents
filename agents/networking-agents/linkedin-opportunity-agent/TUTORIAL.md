# Tutorial — LinkedIn Opportunity Agent

A 5-minute walkthrough from zero to your first scored opportunities and outreach
draft.

## 1. Install & run

```bash
cd agents/networking-agents/linkedin-opportunity-agent
pip install -r requirements.txt
streamlit run app.py
```

Your browser opens the **Home** page, already populated with demo opportunities.
Everything works immediately — even before you add an API key.

## 2. (Optional) Turn on AI analysis

The app has two engines:

- **Keyword engine (default):** deterministic signal matching. Free, instant,
  no key required. Great for trying things out.
- **OpenAI engine:** nuanced analysis and outreach. Add a key to enable it.

To enable AI, go to **⚙️ Settings → AI / OpenAI API** and paste your
`sk-...` key (or set `OPENAI_API_KEY` in your environment / Streamlit
secrets). Pick a model:

- `gpt-4o` — highest quality
- `gpt-4.1-mini` — balanced
- `gpt-4o-mini` — fastest / cheapest for bulk scanning (default)

The sidebar shows a green ✅ when AI is active.

## 3. Tell the agent what you care about

On **Settings → What to monitor**, set your **keywords** (e.g. `AI`, `funding`,
`automation`) and **target industries** (e.g. `Fintech`, `SaaS`). Posts matching
these score higher. Click **Save monitoring preferences**.

Optionally add **monitored profiles** and **company pages** you want to watch.

## 4. Scan for opportunities

Back on **🏠 Home**, click **🔍 Scan LinkedIn now**. The agent:

1. Fetches new posts from the active source,
2. Analyses each one (OpenAI runs them concurrently via async),
3. Detects the opportunity type, writes a summary, explains why it matters,
   recommends an action, and assigns a **0-100 score**.

The **Today's Opportunities** feed shows the highest-scoring results first.

> **Tip:** the demo source eventually runs out of fresh sample posts. To analyse
> real content, paste a LinkedIn post into **Settings → Add a post manually**,
> then scan again.

## 5. Explore & filter

Open **🎯 Opportunities** to search and filter by type, score, industry, date,
company, or person. Switch to the **Table** tab to sort and **export a CSV**.
Use the **⭐ Save / 📨 Contacted / 🗄 Archive** buttons to triage.

## 6. Draft outreach

Go to **✍️ Outreach**, pick an opportunity, enter your name/role, and choose a
message type:

- Connection request (≤ 280 chars)
- Personalised first message
- Follow-up
- Networking introduction

Click **✨ Generate** — or **⚡ Generate full sequence** to draft a
connection → message → follow-up chain at once. Edit, then **💾 Save draft**.
Every saved message is kept in history per opportunity.

## 7. Track analytics & set up digests

**📊 Analytics** shows KPIs, opportunity-type and lead-score distributions, top
industries and companies, plus **hiring** and **funding** trend lines.

At the bottom, preview a **Daily** or **Weekly** email digest. To actually send
it, configure SMTP on **Settings → Email digests** (Gmail users: use an App
Password). The preview works without any setup.

## 8. Reset / manage data

**Settings → Data** lets you clear all opportunities and re-seed demo data. The
SQLite database lives under `data/` locally; on Streamlit Cloud it resets when
the container restarts and re-seeds automatically.

---

## Wiring in a real data source (advanced)

LinkedIn has no public posts API and scraping with credentials breaks their ToS.
To feed compliant, real data, register a custom source anywhere at startup:

```python
from modules import monitor

def my_source(keywords, industries, limit):
    # query your authorised provider, return a list of post dicts:
    return [{
        "external_id": "unique-id",
        "author_name": "Jane Doe",
        "author_headline": "VP Eng at Acme",
        "company": "Acme",
        "url": "https://www.linkedin.com/...",
        "text": "We're hiring AI engineers...",
        "industry": "SaaS",
        "posted_at": "2026-06-08T10:00:00Z",
    }]

monitor.set_source(my_source)
```

Detection, scoring, outreach, and analytics all run unchanged on your data.

---

## Troubleshooting

- **"AI off" warning:** no API key found. Add one on Settings (the app still
  works on the keyword engine).
- **No new posts on scan:** the demo source is exhausted — add a post manually,
  or wire in a real source.
- **Digest won't send:** SMTP isn't configured, or your provider needs an App
  Password. The in-app preview always works.
