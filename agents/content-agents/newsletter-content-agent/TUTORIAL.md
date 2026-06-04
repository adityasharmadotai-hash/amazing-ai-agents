# 🪶 Quill — Tutorial & Walkthrough

This tutorial walks you through Quill end to end: from launching the app in Demo Mode to producing and exporting a complete AI-generated newsletter. No API key is required to follow along — but we'll note where one unlocks live generation.

---

## 0. Launch

```bash
pip install -r requirements.txt
streamlit run app.py
```

On first launch Quill seeds demo data: 7 content sources, a handful of articles, two example newsletters, and a weekly schedule. The sidebar badge shows your mode:

- **🟢 OpenAI connected** — live AI generation
- **🟡 Demo mode** — deterministic fallbacks + seed data (still fully functional)

The sidebar has 9 pages. We'll go through them in the natural order you'd use them.

---

## 1. Dashboard

Your home base. Stat cards summarize sources, collected content, newsletters created, and drafts pending. Below that you'll see trending topics, a newsletters-over-time chart, and engagement-by-style — all driven by what's in your database.

> First time? These already have demo numbers so the page never looks empty.

---

## 2. Content Sources

This is where you tell Quill *where* to read from.

1. Pick a **source type** (RSS Feed, News Website, Blog, Reddit, Twitter/X, LinkedIn, YouTube, Company Website).
2. Give it a **name** and the **URL / handle / subreddit**.
3. Click **Add source**.

Each type uses a tailored collector:
- **RSS Feed** → parsed directly with feedparser.
- **News Website / Blog / Company Website** → scraped; Quill auto-discovers an RSS link if one exists, otherwise extracts article links.
- **Reddit** → public JSON "hot" listing for the subreddit.
- **YouTube** → channel/playlist converted to its RSS feed.
- **Twitter/X & LinkedIn** → tries an RSS bridge; if unavailable, inserts a clearly labelled placeholder so the pipeline never breaks.

Delete any source with the ✕ next to it.

---

## 3. Research & Collect

The heart of the agent.

1. Enter a **topic** (e.g. "AI agents", "fundraising", "developer hiring").
2. Optionally set an **industry** and limit which **source types** to pull from.
3. Click **Collect & Research**.

Quill fans out across your sources concurrently, de-duplicates everything (by content hash *and* near-identical titles), then runs the research engine to produce:

- a **summary** of the landscape,
- ranked **key insights**,
- extracted **statistics**,
- topical **clusters**,
- a ranked list of the strongest source items.

With an API key this is LLM-powered; without one, a transparent heuristic does the ranking and stat extraction. Either way you get usable research.

---

## 4. Generate Newsletter

Turn research into a finished issue.

1. Choose a **style** — Founder, AI, Startup, Marketing, Recruiting, Technology, or Finance.
2. Choose a **writing mode** — Professional, Educational, Conversational, Technical, or Thought Leadership.
3. Confirm the topic and click **Generate**.

Quill writes a full structured newsletter:

```
Title
Subject line
Introduction
Key insights        (heading + body, several)
Industry updates    (headline + summary + link)
Actionable takeaways
Closing
Call-to-action
```

It also computes an **engagement prediction** (0–99) using an explainable heuristic — subject-line length and specificity, presence of a CTA, number of insights and takeaways, and intro length. Hover the score to understand *why* it's what it is.

The generated issue is saved automatically as a **draft**.

---

## 5. Drafts & Editor

Every newsletter you generate lands here.

- Browse drafts and sent issues.
- Open one to **preview** the rendered issue.
- **Edit** any section inline and save.
- Delete issues you don't want.

This is also where you go after automation runs, to review what Quill produced overnight.

---

## 6. AI Studio

A toolbox of focused AI assists for any selected newsletter:

- **Subject-line variations** — A/B-test-ready alternatives.
- **CTA suggestions** — different calls-to-action to match your goal.
- **Newsletter hooks** — scroll-stopping opening lines.
- **Content recommendations** — gap analysis: what's missing from your current research.
- **Future ideas** — topics for upcoming issues.

Each returns a clean list. Without an API key these fall back to sensible deterministic suggestions.

---

## 7. Automation

Set Quill to run on its own.

1. Pick a **frequency** — Daily, Weekly, or Monthly.
2. Set the **topic**, **style**, and **mode** the automated run should use.
3. Save the schedule.

Quill uses **pull-based** scheduling: when the app loads (or when you click **Run due now**), it checks for any schedule whose next-run time has passed, executes the full collect → research → generate → save-draft pipeline, and advances the schedule. No separate background process to babysit.

---

## 8. Deliver & Export

Get your newsletter out into the world.

**Export formats:**
- **Markdown** — for docs and Git.
- **HTML** — email-ready with inline CSS in Quill's violet theme.
- **PDF** — via reportlab.
- **DOCX** — via python-docx.

**Email providers:**
- **Gmail** — sends over SMTP with an app password; without credentials, hands you a downloadable `.eml` draft.
- **Mailchimp / ConvertKit / Beehiiv** — creates a campaign/broadcast/post draft via their API; without credentials, returns the exact JSON payload it *would* POST, so you can inspect or copy it.

Pick a draft, pick a destination, and ship.

---

## 9. Settings

- Toggle and enter **email provider credentials** (Gmail, Mailchimp, ConvertKit, Beehiiv) live.
- See your **API connection status**.
- Manage data.

Credentials entered here are stored in the local SQLite settings table and used by the Deliver page.

---

## Going live with AI

To switch from Demo Mode to full AI generation:

```bash
cp .env.example .env
# set OPENAI_API_KEY=sk-...
streamlit run app.py
```

The sidebar badge flips to **🟢 OpenAI connected** and every generation step now calls the model. Everything you learned above works identically — just smarter.

---

## Tips

- **Start in Research & Collect** with a tight topic — narrow topics produce sharper insights and higher engagement scores.
- **Match style to mode** — e.g. Finance + Professional, or AI + Thought Leadership.
- **Use AI Studio after generating**, not before — it works against your actual draft and research.
- **Check the engagement score** before sending; if it's low, the hover explanation tells you what to fix (often: add a CTA or a sharper subject line).

Happy shipping. 🪶
