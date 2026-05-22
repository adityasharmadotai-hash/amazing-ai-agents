# 🔍 AI SEO Audit Agent

> Enter any website URL → get a complete 6-category SEO audit with AI-powered scores, issue detection, GPT-4o recommendations, keyword strategy, and PDF/Markdown export — in under 60 seconds.

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

SEO audits that used to take hours and cost hundreds of dollars are now instant and free. Paste any URL — the agent scrapes the page, runs 6 rule-based scoring modules, then calls GPT-4o five times to generate a complete improvement plan, optimised meta tags, technical fixes, UX suggestions, and a keyword strategy.

---

## Features

| Feature | Description |
|---------|-------------|
| 🔍 **6-Category Audit** | Meta tags, headings, keywords, technical SEO, images, links |
| 📊 **SEO Score 0-100** | Weighted overall score with radar chart per category |
| ❌ **Issue Detection** | Critical, warning, info, and pass findings with fix instructions |
| 🤖 **AI Improvement Plan** | GPT-4o: quick wins, short-term, long-term actions with impact ratings |
| ✍️ **Content Optimisation** | 3 improved title options, 3 meta descriptions, CTA ideas |
| ⚙️ **Technical Guidance** | Core Web Vitals tips, schema recommendations, robots/sitemap |
| 🎨 **UX Suggestions** | Readability, navigation, mobile UX, trust signals |
| 📈 **Keyword Strategy** | Top keywords found, AI target suggestions, long-tail opportunities |
| 💡 **Content Ideas** | AI-generated blog/page ideas with target keywords |
| 📥 **PDF Export** | Professional ReportLab PDF with tables, scores, and AI recommendations |
| 📝 **Markdown Export** | Clean Markdown for Notion, Obsidian, GitHub |
| 🔑 **User API Key** | Anyone can test on Streamlit Cloud with their own OpenAI key |

---

## How It Works

```
Paste Website URL
      ↓
scraper.py — requests + BeautifulSoup
Fetch page, measure load time, extract all HTML data
      ↓
analyser.py — 6 rule-based modules
Meta / Headings / Keywords / Technical / Images / Links
Each scored 0-100 with detailed issues list
      ↓
ai_advisor.py — GPT-4o (5 API calls)
1. SEO improvement plan (quick wins / short / long term)
2. Content optimisation (title, description, CTA)
3. Technical guidance (performance, schema, CWV)
4. UX suggestions (readability, mobile, trust)
5. Keyword strategy (targets, long-tail, content ideas)
      ↓
app.py — 7-page Streamlit dashboard
Scores, radar chart, issue cards, AI cards, charts
      ↓
exporter.py — PDF + Markdown
Download full audit report
```

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Core language |
| Streamlit | 7-page web dashboard |
| OpenAI GPT-4o | 5 AI analysis calls per audit |
| requests | HTTP page fetching with load time measurement |
| BeautifulSoup4 | HTML parsing and data extraction |
| lxml | Fast HTML parser backend |
| ReportLab | Professional PDF report generation |
| Plotly | Radar chart, bar charts, analytics |

---

## Project Structure

```
seo-audit-agent/
├── app.py                  # Main Streamlit app — 7 pages
├── modules/
│   ├── __init__.py
│   ├── scraper.py          # Web fetch + HTML parsing
│   ├── analyser.py         # 6-category rule-based scoring
│   ├── ai_advisor.py       # GPT-4o recommendations (5 calls)
│   └── exporter.py         # PDF (ReportLab) + Markdown export
├── .streamlit/
│   └── config.toml         # Theme + server settings
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── Tutorial.md
```

---

## Getting Started

### 1. Clone & install

```bash
git clone https://github.com/adityasharmadotai-hash/amazing-ai-agents.git
cd amazing-ai-agents/agents/seo-agents/seo-audit-agent
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set credentials

```bash
cp .env.example .env
# Edit .env — add your OPENAI_API_KEY
```

### 3. Run

```bash
streamlit run app.py
# Opens at http://localhost:8501
```

---

## Deploy to Streamlit Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Set main file: `app.py`
4. Add secrets (TOML format with quotes):

```toml
OPENAI_API_KEY = "sk-your-openai-key"
```

5. Deploy ✅

> **Public access:** Users visiting your app can add their own OpenAI key via **🔑 Settings** — no need to share yours.

---

## Common Errors & Fixes

| Error | Fix |
|-------|-----|
| `Could not connect` | Check the URL — ensure the site is publicly accessible |
| `SSL certificate error` | Site has an invalid certificate — try the HTTP version |
| `Request timed out` | Site is too slow or blocking scrapers — try again |
| `Invalid API key` | Go to 🔑 Settings and re-enter your OpenAI key |
| `Invalid format: TOML` | Use `KEY = "value"` with quotes in Streamlit secrets |
| AI sections empty | Enable "Run AI Analysis" in audit options |
| `lxml not found` | Run `pip install lxml` |

---

## ⭐ If you found this useful

- ⭐ **[Star the repository](https://github.com/adityasharmadotai-hash)** — helps others discover this
- 🌐 **[Visit adityasharma.ai](https://www.adityasharma.ai)** — AI training for professionals
- 💼 **[Follow on LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)** — daily AI updates
- 📺 **[Subscribe on YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)** — AI agent tutorials
- 🚀 **[AI Jobs in the USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

---

*Built with ❤️ by [Aditya Sharma](https://www.adityasharma.ai) · OpenAI GPT-4o + BeautifulSoup + Streamlit*
