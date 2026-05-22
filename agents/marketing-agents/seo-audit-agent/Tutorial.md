# 🔍 Build an AI SEO Audit Agent from Scratch

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

> **What you'll build:** A 9-page Streamlit app that scrapes any website, scores it across 6 SEO categories, shows a live Google SERP preview, provides step-by-step fix guides with copy-paste code, calls GPT-4o for AI recommendations, and exports professional PDF and Markdown reports.

---

## 📋 Table of Contents

1. [What Are We Building?](#1-what-are-we-building)
2. [How It Works](#2-how-it-works)
3. [Prerequisites](#3-prerequisites)
4. [Project Setup](#4-project-setup)
5. [File 1 — scraper.py](#5-file-1--scraperpy)
6. [File 2 — analyser.py](#6-file-2--analyserpy)
7. [File 3 — fixes.py](#7-file-3--fixespy)
8. [File 4 — ai_advisor.py](#8-file-4--ai_advisorpy)
9. [File 5 — exporter.py](#9-file-5--exporterpy)
10. [File 6 — app.py](#10-file-6--apppy)
11. [Running Locally](#11-running-locally)
12. [Deploying to Streamlit Cloud](#12-deploying-to-streamlit-cloud)
13. [Common Errors & Fixes](#13-common-errors--fixes)
14. [What You Learned](#14-what-you-learned)
15. [What's Next](#15-whats-next)

---

## 1. What Are We Building?

Professional SEO audits cost $500–$2,000 and take days. This agent does them in 60 seconds for free — and tells users *exactly* how to fix every problem with copy-paste code.

```
URL: https://example.com
      ↓
📊 Overall SEO Score: 58/100 — Needs Work   Grade: C

❌ 4 Critical Issues Found:
   • No meta description
   • Page NOT using HTTPS
   • No H1 tag found
   • 18/24 images missing alt text

📖 Fix Guide — "Add a Meta Description":
   Difficulty: Easy · Time: 10 min · Impact: High
   Step 1: Open your HTML or CMS settings
   Step 2: Find the meta description field
   Step 3: Write 150-160 characters with your primary keyword...
   <meta name="description" content="Your description here...">
   ✅ Do: Include primary keyword
   ❌ Don't: Copy your title tag

🤖 AI Quick Win #1:
   Add HTTPS — ranking factor (High impact, Low effort)
   → Get a free SSL certificate via Cloudflare or Let's Encrypt

👁️ Google Preview:
   [Live SERP card showing how your page looks in search results]
```

---

## 2. How It Works

```
┌──────────────────────────────────────────────────────────────────┐
│                    FULL ARCHITECTURE                             │
│                                                                  │
│  USER PASTES URL (or clicks sample: openai.com, stripe.com)     │
│           ↓                                                       │
│    scraper.py — requests + BeautifulSoup                        │
│    Fetch page → measure load time → extract all HTML data       │
│           ↓                                                       │
│    analyser.py — 6 independent scoring functions                │
│    Each returns: score (0-100) + issues list                    │
│           ↓                                                       │
│    fixes.py — Fix guide lookup (18 guides)                      │
│    Each issue → matched to step-by-step fix + code example      │
│           ↓                                                       │
│    ai_advisor.py — GPT-4o (5 calls, optional)                   │
│    Improvement plan / content / technical / UX / keywords       │
│           ↓                                                       │
│    app.py — 9-page Streamlit dashboard                          │
│    Audit · Dashboard · AI · Keywords · Technical                │
│    SERP Preview · Fix Guides · Export · Settings                │
│           ↓                                                       │
│    exporter.py — PDF + Markdown                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Five modules, each with one job:**

| File | Job | Key tech |
|------|-----|----------|
| `scraper.py` | Fetch + parse webpage | requests, BeautifulSoup |
| `analyser.py` | Rule-based scoring (6 categories) | Pure Python + Counter |
| `fixes.py` | Fix guide library (18 guides) | Plain dict lookup |
| `ai_advisor.py` | AI recommendations | OpenAI GPT-4o |
| `exporter.py` | PDF + Markdown reports | ReportLab |

---

## 3. Prerequisites

### ✅ Required

- [ ] Python 3.10+
- [ ] OpenAI API key — [platform.openai.com/api-keys](https://platform.openai.com/api-keys) *(optional — most features work without it)*
- [ ] GitHub + Streamlit accounts for deployment

### 💰 Cost per full audit

| What | Cost |
|------|------|
| Scraping + rule-based analysis | Free |
| Fix guides (18 guides) | Free |
| SERP & social preview | Free |
| 5 × GPT-4o AI calls | ~$0.022 |
| **Total (with AI)** | **~$0.022** |

---

## 4. Project Setup

```bash
mkdir seo-audit-agent && cd seo-audit-agent
mkdir modules .streamlit

python3 -m venv venv && source venv/bin/activate

pip install streamlit openai requests beautifulsoup4 lxml reportlab plotly python-dotenv

cp .env.example .env
# Set OPENAI_API_KEY=sk-your-key (or leave blank — audit still works)
```

---

## 5. File 1 — `scraper.py`

> **What this file does:** Fetches the target page, measures load time, and extracts every piece of data the analyser needs — meta tags, headings, images, links, body text, structured data.

### Two functions — fetch then extract

```python
def fetch_page(url: str) -> dict:
    start = time.time()
    resp  = requests.get(url, headers=HEADERS, timeout=20)
    load_time = round(time.time() - start, 3)
    soup = BeautifulSoup(resp.text, "lxml")   # lxml = 10x faster than html.parser
    return {"soup": soup, "load_time_seconds": load_time, ...}

def extract_raw_data(page: dict) -> dict:
    # Extracts: title, description, headings, images, links,
    # body text, schema tags, favicon, HTML lang, response headers...
    return {...}
```

### Why fake browser headers?

```python
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
    "Accept-Language": "en-US,en;q=0.9",
}
```

Without these, many sites return `403 Forbidden` because they block bot traffic. Using realistic headers makes your requests look like a Chrome browser visit.

### What gets extracted

```python
{
    "title": "Page Title",              # from <title>
    "description": "...",              # from <meta name=description>
    "headings": {"h1":["..."],"h2":[]},# all heading tags
    "images": [{"src":"...","alt":"...","loading":"lazy"}],
    "internal_links": [...],
    "external_links": [...],
    "body_text": "full text...",       # all visible text, scripts stripped
    "word_count": 1243,
    "has_schema": True,                # JSON-LD present?
    "load_time_seconds": 0.83,
    "is_https": True,
    "og_tags": {"og:title":"...", ...},
    "twitter_tags": {...},
    ...
}
```

---

## 6. File 2 — `analyser.py`

> **What this file does:** Six independent scoring functions. Each takes the raw data dict and returns a `score` (0-100) plus a list of `issues` with severity labels.

### The issue object

```python
def _issue(severity: str, message: str, fix: str = "") -> dict:
    return {"severity": severity, "message": message, "fix": fix}
# severity: "critical" | "warning" | "info" | "pass"
```

### The scoring pattern — consistent across all 6 modules

```python
def analyse_meta(d: dict) -> dict:
    issues, ok, total = [], 0, 9   # total = how many checks we run

    # Each check either increments ok (passed) or adds an issue
    tl = len(d.get("title",""))
    if not d.get("title"):
        issues.append(_issue("critical","No <title> tag","Add a 50-60 char title."))
    elif 50 <= tl <= 60:
        ok += 1
        issues.append(_issue("pass",f"Title OK — {tl} chars"))
    else:
        issues.append(_issue("warning",f"Title length {tl} chars","Aim for 50-60."))

    # ... repeat for description, canonical, viewport, robots, OG, Twitter...

    return {"score": round(ok/total*100), "issues": issues, ...}
```

### The 6 categories and their weight in the final score

```python
WEIGHTS = {
    "meta":      0.25,   # 25% — directly controls search snippets
    "keywords":  0.20,   # 20% — relevance signals
    "technical": 0.20,   # 20% — crawlability and speed
    "headings":  0.15,   # 15% — content structure
    "images":    0.10,   # 10% — accessibility + page speed
    "links":     0.10,   # 10% — internal architecture
}

def calculate_overall(results: dict) -> int:
    return round(sum(results[c]["score"] * w for c, w in WEIGHTS.items()))
```

### Keyword frequency analysis

The keyword module finds the *actual* keywords on the page — not metadata, but what the content is truly about:

```python
from collections import Counter

STOP_WORDS = set(["a","the","is","are","and","or",...])  # 150+ words

def analyse_keywords(d):
    text  = d.get("body_text","")
    clean = re.sub(r"[^a-zA-Z\s]", " ", text.lower())
    words = [w for w in clean.split() if len(w) > 3 and w not in STOP_WORDS]
    freq  = Counter(words)
    top   = freq.most_common(20)   # [("python", 45), ("code", 23), ...]
```

This surfaces keyword opportunities the owner may not have noticed — and flags keyword stuffing when density > 5%.

---

## 7. File 3 — `fixes.py`

> **What this file does:** A library of 18 detailed fix guides, one for each major SEO issue type. Each guide has step-by-step instructions, copy-paste code examples, difficulty rating, time estimate, and do/don't lists. A lookup function matches issue messages to the right guide.

### Why a separate file for fixes?

Three reasons:
1. **Separation of concerns** — analyser.py detects issues, fixes.py explains how to solve them
2. **Reusability** — fixes can be shown inline in the Dashboard AND browsed in a dedicated Fix Guides page
3. **No AI cost** — these are pre-written expert guides, not generated on demand

### The guide structure

```python
FIX_GUIDES = {
    "No meta description": {
        "title": "Add a Meta Description",
        "difficulty": "Easy",
        "time": "10 minutes",
        "impact": "High",
        "summary": "The meta description appears as the gray text under your title in Google. It doesn't affect rankings directly, but a compelling description improves click-through rate — which does.",
        "steps": [
            "Open your page's HTML or CMS settings",
            "Find the meta description field",
            "Write 150-160 characters including your primary keyword",
            "Add a call-to-action (Learn more, Get started, Shop now)",
            "Make it unique for every page on your site",
        ],
        "code": """<meta name="description" content="Your 150-160 char description here. Include keyword and CTA.">""",
        "do": ["Include primary keyword", "Add a clear CTA", "Make every page's description unique"],
        "dont": ["Don't copy the title tag", "Don't stuff keywords", "Don't exceed 160 chars"],
    },
    # ... 17 more guides
}
```

### The lookup function

```python
def get_fix_guide(issue_message: str) -> dict | None:
    """Match an issue message to its fix guide."""
    msg_lower = issue_message.lower()

    # Try exact key match first
    for key, guide in FIX_GUIDES.items():
        if key.lower() in msg_lower:
            return guide

    # Fall back to keyword matching
    keyword_map = {
        "title":    ["title too short", "title too long", "no <title>"],
        "description": ["meta description", "no meta description"],
        "https":    ["https", "ssl", "not using https"],
        "alt text": ["alt text", "missing alt"],
        # ... more mappings
    }
    for guide_key, keywords in keyword_map.items():
        if any(kw in msg_lower for kw in keywords):
            # Return the matching guide
            ...
```

This two-step lookup (exact → keyword) means even issues with slightly different wording still find the right guide.

### The 18 fix guides cover

Meta tags: title tag (3 variations), meta description (3 variations), canonical URL, viewport, noindex removal, Open Graph tags.

Headings: H1 missing, multiple H1s, H2 missing.

Images: alt text, width/height dimensions, lazy loading.

Technical: HTTPS migration, page speed, structured data (Schema.org), HTML lang attribute.

Links: empty anchor text, too few internal links.

Keywords: keyword not in title, low word count.

---

## 8. File 4 — `ai_advisor.py`

> **What this file does:** Five focused GPT-4o calls — each specialist, compact, and returning structured JSON.

### Why 5 calls instead of 1?

One massive call would exceed context limits and produce unfocused output. Five specialist calls:
- Each has a targeted system prompt ("You are a world-class SEO expert")
- Each gets only the data it needs (compact summary, not full HTML)
- If one fails, all others still work
- Total cost: ~$0.022 — affordable even at scale

### The "Return ONLY valid JSON" pattern

```python
user = f"""Return ONLY this JSON — no preamble, no fences:
{{
  "quick_wins": [{{"action":"...","impact":"High","effort":"Low","detail":"..."}}],
  "short_term": [...],
  "long_term":  [...]
}}"""
```

Without "Return ONLY valid JSON", GPT-4o sometimes prepends "Sure! Here's the analysis:" which breaks `json.loads()`. The instruction forces clean, parseable output.

### Graceful degradation

```python
try:
    return _json(_call(system, user, tokens=2000))
except Exception as e:
    return {"error": str(e), "quick_wins": [], "short_term": [], "long_term": []}
```

If any AI call fails (rate limit, bad key, timeout), the app shows the rule-based audit and fix guides — which are fully functional without any AI. The UI checks `if ai_data.get("error")` and displays a soft info message instead of crashing.

---

## 9. File 5 — `exporter.py`

> **What this file does:** Converts the complete audit into downloadable PDF (ReportLab) and Markdown (f-strings) reports.

### Markdown — simple and reliable

```python
def export_markdown(raw, audit, ai) -> str:
    lines = [
        f"# SEO Audit Report — {raw['url']}",
        f"**Score:** {audit['overall_score']}/100",
        "",
        "## Critical Issues",
    ]
    for cat_data in audit.values():
        for iss in cat_data.get("issues", []):
            if iss["severity"] == "critical":
                lines.append(f"- ❌ **{iss['message']}**")
                if iss.get("fix"):
                    lines.append(f"  - 🔧 Fix: {iss['fix']}")
    # ... AI sections, quick wins, title options, etc.
    return "\n".join(lines)
```

### PDF — ReportLab story pattern

```python
story = []
# Add elements in reading order:
story.append(Paragraph("SEO Audit Report", title_style))
story.append(HRFlowable(width="100%", color=INDIGO))
story.append(Paragraph(summary, body_style))
story.append(Table(score_data, colWidths=[3*inch, 1.2*inch, 1.5*inch]))
story.append(PageBreak())
story.append(Paragraph("Quick Wins", h2_style))
for qw in quick_wins:
    story.append(Paragraph(f"• {qw['action']}", bullet_style))

doc.build(story)  # renders to multi-page PDF with automatic page breaks
```

---

## 10. File 6 — `app.py`

> **What this file does:** 9-page Streamlit dashboard connecting all modules. The Audit page has sample URL pills and a step progress bar. The Dashboard shows a score ring + benchmark comparison. Fix Guides shows your issues first then a browseable library.

### The 9 pages

| Page | Key feature |
|------|-------------|
| 🔍 Audit | Sample URL pills, 12-step progress bar, audit history |
| 📊 Dashboard | SVG score ring, radar, benchmark bar, issue filter |
| 🤖 AI Suggestions | Grade card, top 3 priorities, tabbed action plan |
| 📈 Keywords | Opacity-scaled bar chart, AI keyword targets |
| ⚙️ Technical | Coloured speed gauge, per-metric status cards |
| 👁️ SERP Preview | Live Google preview, social card, OG checklist |
| 🔧 Fix Guides | YOUR issues first (expanded), then all 18 browseable |
| 📤 Export | PDF + Markdown with summary banner |
| 🔑 Settings | API key, what works free, cost breakdown table |

### Sample URL pills pattern

```python
samples = ["https://openai.com","https://stripe.com","https://notion.so","https://linear.app"]
cols = st.columns(len(samples))
for col, url in zip(cols, samples):
    with col:
        if st.button(url.replace("https://",""), key=f"sample_{url}"):
            st.session_state["_sample_url"] = url
            st.rerun()
# On next run, pick up the stored URL:
if st.session_state.get("_sample_url"):
    url_input = st.session_state.pop("_sample_url")
    run_audit = True
```

### Step progress bar pattern

```python
STEPS = [
    ("📡","Fetching website..."),
    ("🔍","Extracting HTML data..."),
    ("📊","Scoring meta tags..."),
    # ... 9 more steps including AI calls
]
progress_bar = st.progress(0)
status_text  = st.empty()

def update(i):
    icon, msg = STEPS[i]
    progress_bar.progress((i+1)/len(STEPS))
    status_text.markdown(f"**{icon} Step {i+1}/{len(STEPS)}:** {msg}")
```

This gives users real-time feedback during the 20-45 second audit — dramatically better than a spinning wheel.

### SVG score ring

Instead of a plain number, the score uses an SVG circle that fills proportionally:

```python
circumf = 2 * 3.14159 * r         # full circle circumference
dash_arr = f"{circumf * pct:.1f} {circumf}"  # filled portion

st.markdown(f"""
<svg width="120" height="120">
  <circle cx="60" cy="60" r="52" fill="none" stroke="#f1f5f9" stroke-width="10"/>
  <circle cx="60" cy="60" r="52" fill="none" stroke="{color}"
      stroke-width="10" stroke-dasharray="{dash_arr}"
      transform="rotate(-90 60 60)"/>    <!-- start from top -->
  <text x="60" y="66" text-anchor="middle" font-size="28" fill="{color}">{score}</text>
</svg>
""", unsafe_allow_html=True)
```

### SERP Preview — the Google result card

```python
# Truncate title and description like Google does
truncated_title = display_title[:57] + "..." if len(display_title) > 60 else display_title
truncated_desc  = display_desc[:157]  + "..." if len(display_desc)  > 157 else display_desc

st.markdown(f"""
<div style="font-family:Arial;border:1px solid #e2e8f0;border-radius:12px;padding:20px;">
    <div style="color:#006621;font-size:14px;">{domain}</div>
    <div style="color:#1a0dab;font-size:20px;">{truncated_title}</div>
    <div style="color:#4d5156;font-size:14px;">{truncated_desc}</div>
</div>
""", unsafe_allow_html=True)
```

### Fix Guides — YOUR issues first

```python
# Collect issues that have a matching fix guide
your_issues = []
for cat_name, cat_data in audit.items():
    for iss in cat_data.get("issues",[]):
        if iss.get("severity") in ("critical","warning"):
            guide = get_fix_guide(iss["message"])
            if guide:
                your_issues.append({"severity": iss["severity"], "guide": guide, ...})

# Sort critical first, then warning
your_issues.sort(key=lambda x: 0 if x["severity"]=="critical" else 1)

for item in your_issues:
    with st.expander(f"❌ {item['message']}", expanded=(item["severity"]=="critical")):
        _render_fix_guide(item["guide"])  # shows steps + code + do/dont
```

Critical issues start expanded — users immediately see what needs fixing most urgently.

---

## 11. Running Locally

```bash
source venv/bin/activate
streamlit run app.py
```

### First Run Walkthrough

1. Go to **🔑 Settings** → enter your OpenAI key (or skip for free features)
2. **🔍 Audit** → click one of the sample URL pills (e.g. `stripe.com`)
3. Make sure "AI Analysis" is checked → click **🔍 Audit Now**
4. Watch the 12-step progress bar — scraping through AI calls
5. Auto-navigates to **📊 Dashboard** — see score ring, radar, benchmark
6. Filter issues by severity → click any issue to open its expander
7. Click **📖 How to Fix This →** to see the step-by-step guide inline
8. Go to **🔧 Fix Guides** → see all your issues organised by priority
9. Go to **👁️ SERP Preview** → toggle Current vs AI Optimised
10. Go to **📈 Keywords** → see the frequency chart + AI targets
11. Go to **📤 Export** → download PDF or Markdown

---

## 12. Deploying to Streamlit Cloud

```bash
git add . && git commit -m "AI SEO Audit Agent" && git push
```

1. [share.streamlit.io](https://share.streamlit.io) → New app
2. Select repo, main file: `app.py`
3. **Advanced → Secrets:**

```toml
OPENAI_API_KEY = "sk-your-openai-key"
```

4. Deploy ✅

**No API key required for deployment.** The full 6-category audit, all fix guides, SERP preview, and Markdown export work without any key. Users add their own key via Settings for AI features.

---

## 13. Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Could not connect` | URL not accessible | Check URL is public and correct |
| `SSL certificate error` | Invalid cert on target site | Try `http://` version |
| `Request timed out` | Site slow or blocking bots | Try again or increase TIMEOUT |
| `Invalid API key` | Wrong key | Go to 🔑 Settings → re-enter |
| `lxml not found` | Parser missing | `pip install lxml` |
| AI sections blank | AI not enabled | Check "AI Analysis" checkbox |
| `Invalid format: TOML` | Wrong secrets format | Use `KEY = "value"` with quotes |
| Score seems wrong | Different page served to bots | Some CDNs serve different content |
| Fix guide not showing | Issue has no guide yet | Only critical/warning with matched guides show |

---

## 14. What You Learned

- ✅ **Web scraping** — requests headers, load time measurement, lxml parser
- ✅ **HTML parsing** — BeautifulSoup, meta tags, headings, images, links, OG tags
- ✅ **Rule-based scoring** — weighted multi-category system with severity levels
- ✅ **Keyword frequency** — Counter, stop words, density calculation
- ✅ **Fix guide library** — lookup pattern, two-step matching (exact → keyword)
- ✅ **Focused GPT-4o calls** — specialist prompts, JSON schema enforcement
- ✅ **Graceful AI degradation** — full functionality without API key
- ✅ **SVG in Streamlit** — `st.markdown(unsafe_allow_html=True)` for custom graphics
- ✅ **SERP simulation** — pixel-accurate Google result card in pure HTML/CSS
- ✅ **Session state patterns** — sample URL pills, audit history, progress tracking
- ✅ **ReportLab PDFs** — story pattern, tables, styles, multi-page
- ✅ **Plotly radar charts** — Scatterpolar with fill and hover

---

## 15. What's Next

### Easy
- **More fix guides** — add guides for redirect chains, security headers, robots.txt
- **Historical score tracking** — save each audit to Supabase and chart score over time
- **Competitor comparison** — audit two URLs side by side

### Intermediate
- **Google PageSpeed API** — get real Core Web Vitals data (LCP, FID, CLS)
- **Broken link checker** — test all internal links for 404 errors
- **Full site crawl** — follow all internal links, audit every page

### Advanced
- **Google Search Console API** — pull actual keyword ranking and click data
- **Automated monitoring** — weekly scheduled audits with email alerts on score drops
- **White-label PDF** — custom branding for client delivery

---

## ⭐ Enjoyed this tutorial?

- ⭐ **[Star the repository](https://github.com/adityasharmadotai-hash)** — helps others discover this
- 🌐 **[Visit adityasharma.ai](https://www.adityasharma.ai)** — AI training for professionals
- 💼 **[Follow on LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)** — daily AI updates
- 📺 **[Subscribe on YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)** — AI agent tutorials
- 🚀 **[AI Jobs in the USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

---

*Built with ❤️ by [Aditya Sharma](https://www.adityasharma.ai) · OpenAI GPT-4o + BeautifulSoup + Streamlit*
