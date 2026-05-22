# 🔍 AI SEO Audit Agent

> Enter any website URL → get a complete SEO audit with AI-powered scores, step-by-step fix guides, SERP preview, keyword strategy, and PDF/Markdown export — in under 60 seconds.

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

SEO audits that used to take hours and cost hundreds of dollars are now instant and free. Paste any URL — the agent scrapes the page, runs 6 rule-based scoring modules, calls GPT-4o five times for AI recommendations, and provides step-by-step fix guides with copy-paste code for every issue found.

---

## Features

| Feature | Description |
|---------|-------------|
| 🔍 **6-Category Audit** | Meta tags, headings, keywords, technical SEO, images, links |
| 📊 **SEO Score 0-100** | Weighted score with animated ring gauge + radar chart |
| ❌ **Issue Detection** | Critical / warning / info / pass with severity breakdown |
| 🔧 **Fix Guides** | Step-by-step instructions + copy-paste code for every issue |
| 🤖 **AI Improvement Plan** | GPT-4o: quick wins, short-term and long-term action plan |
| ✍️ **Content Optimisation** | 3 improved title options, 3 meta descriptions, CTA ideas |
| ⚙️ **Technical Guidance** | Core Web Vitals, schema recommendations, performance fixes |
| 🎨 **UX Suggestions** | Readability, mobile UX, trust signals, navigation tips |
| 📈 **Keyword Strategy** | Top keywords, density, AI targets, long-tail, content ideas |
| 👁️ **SERP Preview** | Live Google result preview + Facebook/Twitter social card preview |
| 📊 **Benchmark Comparison** | Your score vs industry average, good, and excellent |
| 💡 **Sample URLs** | One-click test with openai.com, stripe.com, notion.so, linear.app |
| 📥 **PDF Export** | Professional ReportLab PDF with all findings and AI recommendations |
| 📝 **Markdown Export** | Clean Markdown for Notion, Obsidian, GitHub, Confluence |
| 🔑 **User API Key** | Anyone can test on Streamlit Cloud with their own OpenAI key |
| 🕐 **Audit History** | Recent audits saved in session with score and domain |

---

## How It Works

```
Paste Website URL (or click a sample)
      ↓
scraper.py — requests + BeautifulSoup
Fetch page, measure load time, extract all HTML data
      ↓
analyser.py — 6 rule-based modules
Meta / Headings / Keywords / Technical / Images / Links
Each scored 0-100 with issues list (critical/warning/info/pass)
      ↓
fixes.py — Fix guide library (18 guides)
Match each issue → step-by-step fix + code example
      ↓
ai_advisor.py — GPT-4o (5 API calls, optional)
1. SEO improvement plan (quick wins / short / long term)
2. Content optimisation (title, description, CTA)
3. Technical guidance (performance, schema, CWV)
4. UX suggestions (readability, mobile, trust)
5. Keyword strategy (targets, long-tail, content ideas)
      ↓
app.py — 9-page Streamlit dashboard
Audit · Dashboard · AI · Keywords · Technical · SERP · Fix Guides · Export · Settings
      ↓
exporter.py — PDF + Markdown
Download full audit report
```

---

## 9 Pages at a Glance

| Page | What You Get |
|------|-------------|
| 🔍 **Audit** | URL input, sample URLs, step progress bar, recent history |
| 📊 **Dashboard** | Score ring, radar chart, issue counts, benchmark comparison |
| 🤖 **AI Suggestions** | Grade, priorities, action plan, content optimisation, UX |
| 📈 **Keywords** | Frequency bar chart, AI keyword strategy, content ideas |
| ⚙️ **Technical** | Speed gauge, technical issues, image/link stats |
| 👁️ **SERP Preview** | Google result preview, social card preview, OG checklist |
| 🔧 **Fix Guides** | Step-by-step fixes for YOUR issues + browse all 18 guides |
| 📤 **Export** | PDF + Markdown download with full report |
| 🔑 **Settings** | API key, what works without a key, cost breakdown |

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Core language |
| Streamlit | 9-page web dashboard |
| OpenAI GPT-4o | 5 AI analysis calls per audit (optional) |
| requests | HTTP page fetching with load time measurement |
| BeautifulSoup4 | HTML parsing and data extraction |
| lxml | Fast HTML parser backend |
| ReportLab | Professional PDF report generation |
| Plotly | Radar chart, bar charts, benchmark comparison |

---

## Project Structure

```
seo-audit-agent/
├── app.py                  # Main Streamlit app — 9 pages
├── modules/
│   ├── __init__.py
│   ├── scraper.py          # Web fetch + HTML parsing
│   ├── analyser.py         # 6-category rule-based scoring
│   ├── ai_advisor.py       # GPT-4o recommendations (5 calls)
│   ├── fixes.py            # ← NEW: 18 step-by-step fix guides with code
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
# Note: the audit works WITHOUT a key — AI sections are disabled
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

> **Public access:** Users can enter their own OpenAI key via **🔑 Settings**. The full 6-category audit + fix guides + SERP preview work without any key — only AI sections require one.

---

## What Works Without an API Key?

| Feature | No Key | With Key |
|---------|--------|----------|
| 6-Category SEO Audit | ✅ | ✅ |
| SEO Score & Charts | ✅ | ✅ |
| Issue Detection | ✅ | ✅ |
| 🔧 Fix Guides (all 18) | ✅ | ✅ |
| 👁️ SERP & Social Preview | ✅ | ✅ |
| Markdown Export | ✅ | ✅ |
| 🤖 AI Improvement Plan | ❌ | ✅ |
| AI Content Optimisation | ❌ | ✅ |
| AI Keyword Strategy | ❌ | ✅ |
| PDF with AI content | ❌ | ✅ |

---

## Common Errors & Fixes

| Error | Fix |
|-------|-----|
| `Could not connect` | Check URL is publicly accessible |
| `SSL certificate error` | Try `http://` version of the URL |
| `Request timed out` | Site too slow or blocking bots — try again |
| `Invalid API key` | Go to 🔑 Settings → re-enter key |
| `Invalid format: TOML` | Use `KEY = "value"` with quotes in secrets |
| AI sections empty | Enable "AI Analysis" in audit options |
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
