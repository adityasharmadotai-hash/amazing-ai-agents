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

> **What you'll build:** A Streamlit app that scrapes any website, runs 6 rule-based SEO scoring modules, calls GPT-4o five times for AI recommendations, and exports professional PDF and Markdown audit reports.

---

## 📋 Table of Contents

1. [What Are We Building?](#1-what-are-we-building)
2. [How It Works](#2-how-it-works)
3. [Prerequisites](#3-prerequisites)
4. [Project Setup](#4-project-setup)
5. [File 1 — scraper.py](#5-file-1--scraperpy)
6. [File 2 — analyser.py](#6-file-2--analyserpy)
7. [File 3 — ai_advisor.py](#7-file-3--ai_advisorpy)
8. [File 4 — exporter.py](#8-file-4--exporterpy)
9. [File 5 — app.py](#9-file-5--apppy)
10. [Running Locally](#10-running-locally)
11. [Deploying to Streamlit Cloud](#11-deploying-to-streamlit-cloud)
12. [Common Errors & Fixes](#12-common-errors--fixes)
13. [What You Learned](#13-what-you-learned)
14. [What's Next](#14-whats-next)

---

## 1. What Are We Building?

Professional SEO audits cost $500-$2000 and take days. This agent does them in 60 seconds for free.

Paste any URL → the agent crawls it → scores 6 SEO categories → GPT-4o writes your improvement plan:

```
URL: https://example.com
      ↓
📊 Overall SEO Score: 67/100 — Needs Work
      ↓
❌ 3 Critical Issues:
   • No meta description
   • Page NOT using HTTPS
   • No H1 tag found

⚠️ 8 Warnings:
   • Title too long (72 chars)
   • 14/22 images missing alt text
   • No canonical URL defined

🤖 AI Quick Wins:
   1. Add meta description (High impact, Low effort)
   2. Fix HTTPS — ranking factor (High impact, Low effort)
   3. Add H1 with primary keyword (High impact, Low effort)

✍️ Optimised Titles:
   • "Buy Organic Coffee Beans | Free UK Delivery — BeanCo" (52 chars)
   • "Premium Coffee Beans Online | BeanCo — Est. 2010" (49 chars)
```

---

## 2. How It Works

```
┌──────────────────────────────────────────────────────────────────┐
│                    FULL ARCHITECTURE                             │
│                                                                  │
│  USER PASTES URL                                                 │
│           ↓                                                       │
│    scraper.py — requests + BeautifulSoup                        │
│    Fetch page → measure load time → extract:                    │
│    title, meta, headings, images, links, body text, schema      │
│           ↓                                                       │
│    analyser.py — 6 independent scoring functions                │
│    meta_score / heading_score / keyword_score /                 │
│    technical_score / image_score / link_score                   │
│    Each returns: score (0-100) + issues list                    │
│           ↓                                                       │
│    ai_advisor.py — 5 GPT-4o API calls                          │
│    1. seo_improvements() → improvement plan + grade             │
│    2. content_optimisation() → titles, descriptions, CTAs       │
│    3. technical_guidance() → performance, schema, CWV           │
│    4. ux_suggestions() → readability, mobile, trust             │
│    5. keyword_strategy() → targets, long-tail, content ideas    │
│           ↓                                                       │
│    app.py — 7-page Streamlit dashboard                          │
│    Audit → Dashboard → AI → Keywords → Technical → Export → Settings │
│           ↓                                                       │
│    exporter.py — PDF + Markdown                                 │
│    Download complete audit report                               │
└──────────────────────────────────────────────────────────────────┘
```

**Four modules, each with one job:**

| File | Job | Key tech |
|------|-----|----------|
| `scraper.py` | Fetch + parse webpage | requests, BeautifulSoup |
| `analyser.py` | Rule-based SEO scoring | Pure Python + Counter |
| `ai_advisor.py` | AI recommendations | OpenAI GPT-4o |
| `exporter.py` | Report generation | ReportLab, Markdown |

---

## 3. Prerequisites

### ✅ Required

- [ ] Python 3.10+ — [python.org/downloads](https://python.org/downloads)
- [ ] OpenAI API key — [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- [ ] GitHub + Streamlit accounts for deployment

### 💰 Cost per audit

| Step | Cost |
|------|------|
| Web scraping | Free |
| Rule-based analysis | Free |
| 5 × GPT-4o calls | ~$0.025 total |
| **Full audit** | **~$0.025** |

Very affordable — you can run 40 audits for $1.

---

## 4. Project Setup

```bash
mkdir seo-audit-agent && cd seo-audit-agent
mkdir modules .streamlit

python3 -m venv venv
source venv/bin/activate

pip install streamlit openai requests beautifulsoup4 lxml reportlab plotly python-dotenv

cp .env.example .env
# Set OPENAI_API_KEY=sk-your-key
```

---

## 5. File 1 — `scraper.py`

> **What this file does:** Fetches the target webpage using `requests`, measures the load time, then uses BeautifulSoup to extract every piece of data needed for an SEO audit.

### Two functions — fetch then extract

```python
def fetch_page(url: str) -> dict:
    start = time.time()
    resp  = requests.get(url, headers=HEADERS, timeout=20)
    load_time = round(time.time() - start, 3)
    return {"soup": BeautifulSoup(resp.text, "html.parser"),
            "load_time_seconds": load_time, ...}

def extract_raw_data(page: dict) -> dict:
    # Extract everything the analyser needs
    return {"title": ..., "headings": ..., "images": ..., ...}
```

Separating fetch from extraction means you can test extraction without hitting the network.

### Why `lxml` as parser?

```python
soup = BeautifulSoup(resp.text, "lxml")  # 10x faster than "html.parser"
```

`lxml` is a C-based parser — dramatically faster for large pages. Falls back to `html.parser` if not installed.

### Fake browser headers

Real browsers send these headers. Without them, many sites return 403 Forbidden:

```python
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
    "Accept-Language": "en-US,en;q=0.9",
}
```

### What data is extracted

```python
{
    "title": "Page title",
    "description": "meta description content",
    "headings": {"h1": ["Main heading"], "h2": [...], ...},
    "images": [{"src": "...", "alt": "...", "loading": "lazy"}],
    "internal_links": [{"href": "...", "text": "..."}],
    "external_links": [...],
    "body_text": "cleaned text content...",
    "word_count": 1243,
    "has_schema": True,
    "load_time_seconds": 0.83,
    "is_https": True,
    ...
}
```

---

## 6. File 2 — `analyser.py`

> **What this file does:** Six independent scoring functions — each takes the raw data dict and returns a score (0-100) plus a detailed issues list with severity levels.

### The issue system

Every finding is a dict:

```python
def _issue(severity: str, message: str, fix: str = "") -> dict:
    return {"severity": severity, "message": message, "fix": fix}
# severity: "critical" | "warning" | "info" | "pass"
```

In the UI:
- `critical` → ❌ red card
- `warning` → ⚠️ yellow card
- `info` → ℹ️ blue card
- `pass` → ✅ green card

### The scoring pattern

```python
def _score(passed: int, total: int) -> int:
    return round((passed / total) * 100) if total else 0

def analyse_meta(d: dict) -> dict:
    issues, ok, total = [], 0, 9   # total = number of checks

    # Title check
    tl = len(d.get("title", ""))
    if not d.get("title"):
        issues.append(_issue("critical", "No <title> tag", "Add a 50-60 char title."))
    elif 50 <= tl <= 60:
        ok += 1  # passed this check
        issues.append(_issue("pass", f"Title OK — {tl} chars"))
    else:
        issues.append(_issue("warning", f"Title length {tl} chars", "Aim for 50-60."))

    return {"score": _score(ok, total), "issues": issues, ...}
```

### The 6 categories and what they check

**Meta (25% weight):**
- Title: exists, 50-60 chars
- Description: exists, 150-160 chars
- Canonical URL: present
- Viewport: present (mobile)
- Robots: not noindex/nofollow
- Open Graph: title + description + image
- Twitter card: present

**Headings (15% weight):**
- H1: exactly one, under 70 chars
- H2: at least one present
- Total headings > 0
- No empty heading tags

**Keywords (20% weight):**
- Top keywords found via frequency (stops words removed)
- Keywords present in title, description, H1
- Keyword density (not too high = stuffing, not too low)
- Word count target: 300+ / 500+ / 1500+

**Technical (20% weight):**
- HTTPS enabled
- HTTP status 200
- No long redirect chains
- Load time < 3 seconds
- HTML size < 500 KB
- Schema.org markup present
- Favicon present
- HTML lang attribute
- Security headers (CSP, X-Frame-Options)

**Images (10% weight):**
- All images have alt text
- 50%+ use lazy loading
- All have width/height attributes
- Total image count < 30

**Links (10% weight):**
- All links have anchor text
- No generic text ("click here", "read more")
- 3-100 internal links
- External links present

### The overall score formula

```python
WEIGHTS = {"meta":0.25,"headings":0.15,"keywords":0.20,
           "technical":0.20,"images":0.10,"links":0.10}

def calculate_overall(results: dict) -> int:
    return round(sum(results[c]["score"] * w for c, w in WEIGHTS.items()))
```

Meta and keywords get the highest weight because they directly control what appears in search results.

### The keyword extraction system

```python
from collections import Counter

STOP_WORDS = set(["a","the","is","are","and","or","but",...])

def analyse_keywords(d):
    text  = d.get("body_text","")
    clean = re.sub(r"[^a-zA-Z\s]", " ", text.lower())
    words = [w for w in clean.split() if len(w) > 3 and w not in STOP_WORDS]
    freq  = Counter(words)
    top   = freq.most_common(20)   # [("python", 45), ("code", 23), ...]
```

This finds the actual keywords on the page — not what the owner thinks are keywords, but what the page is *actually* about based on frequency.

---

## 7. File 3 — `ai_advisor.py`

> **What this file does:** Five focused GPT-4o calls — each with a specific system prompt, compact data summary, and a JSON schema the model must follow.

### Why five calls instead of one?

One massive call would exceed token limits and produce unfocused output. Five focused calls:
- Each has a specialist system prompt
- Each gets only the data it needs (compact summary)
- Each returns a clean JSON structure
- If one fails, the others still work

### The pattern for every call

```python
def _call(system: str, user: str, tokens: int = 1500) -> str:
    r = _client().chat.completions.create(
        model="gpt-4o",
        max_tokens=tokens,
        messages=[{"role":"system","content":system},
                  {"role":"user","content":user}]
    )
    return r.choices[0].message.content.strip()

def _json(text: str):
    # Strip markdown fences if GPT wraps in ```json
    return json.loads(re.sub(r"```(?:json)?|```","",text).strip())
```

### The system prompts are specific roles

```python
"You are a world-class SEO expert. Return ONLY valid JSON."
"You are an expert SEO copywriter. Return ONLY valid JSON."
"You are a technical SEO engineer. Return ONLY valid JSON."
"You are a UX & CRO specialist. Return ONLY valid JSON."
"You are an SEO keyword strategist. Return ONLY valid JSON."
```

**Why "Return ONLY valid JSON"?** Without this, GPT-4o sometimes adds preamble ("Sure! Here's the analysis:") which breaks `json.loads()`. The instruction forces clean output.

### The JSON schema in the prompt

```python
user = f"""Return ONLY this JSON:
{{
  "quick_wins": [{{"action":"...","impact":"High/Medium/Low","effort":"Low","detail":"..."}}],
  "short_term": [...],
  "long_term": [...]
}}
quick_wins: 4 items fixable immediately."""
```

Showing the exact structure with example values is few-shot prompting — GPT-4o uses the structure as a template rather than deciding its own format.

### Error handling — graceful degradation

```python
try:
    return _json(_call(system, user, 2000))
except Exception as e:
    return {"error": str(e), "quick_wins": [], "short_term": [], "long_term": []}
```

If any AI call fails, the app still shows the rule-based audit — it doesn't crash. The UI checks `if ai_data.get("error")` and shows an info message instead.

---

## 8. File 4 — `exporter.py`

> **What this file does:** Converts the audit results and AI suggestions into downloadable PDF and Markdown files.

### Markdown export — simple f-strings

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
                lines.append(f"- ❌ {iss['message']}")
                if iss["fix"]:
                    lines.append(f"  - *Fix:* {iss['fix']}")
    return "\n".join(lines)
```

### PDF export — ReportLab "story" pattern

ReportLab uses a `story` list of flowable elements rendered top-to-bottom:

```python
story = []
story.append(Paragraph("SEO Audit Report", title_style))
story.append(HRFlowable(width="100%", color=INDIGO))
story.append(Paragraph(summary, body_style))

# Table with category scores
table = Table(data, colWidths=[3*inch, 1.2*inch, 1.5*inch])
table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), INDIGO),  # header row
    ("TEXTCOLOR",  (0,0), (-1,0), white),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [LIGHT, white]),
]))
story.append(table)

doc.build(story)   # renders to PDF
```

The `doc.build()` call processes all flowables and produces a multi-page PDF with automatic page breaks.

---

## 9. File 5 — `app.py`

> **What this file does:** 7-page Streamlit dashboard connecting all modules. Runs the audit, displays results with charts and interactive cards, and handles export.

### The 7 pages

| Page | What It Shows |
|------|--------------|
| 🔍 Audit | URL input, run button, audit options |
| 📊 Dashboard | Score gauge, radar chart, issue breakdown, metrics |
| 🤖 AI Suggestions | Quick wins, short/long-term plan, content optimisation, UX |
| 📈 Keywords | Keyword frequency bar chart, AI keyword strategy |
| ⚙️ Technical | Technical scores, image/link stats, AI technical guidance |
| 📤 Export | PDF + Markdown download buttons |
| 🔑 Settings | API key entry (session-only) |

### The audit flow

```python
if run_audit and url_input:
    with st.status("Running...") as status:
        # Step 1: Scrape
        page_data = fetch_page(url_input)
        raw = extract_raw_data(page_data)

        # Step 2: Rule-based analysis (instant)
        audit = {
            "meta":      analyse_meta(raw),
            "headings":  analyse_headings(raw),
            "keywords":  analyse_keywords(raw),
            "technical": analyse_technical(raw),
            "images":    analyse_images(raw),
            "links":     analyse_links(raw),
        }
        audit["overall_score"] = calculate_overall(audit)

        # Step 3: AI analysis (5 calls, ~15-30s)
        if run_ai:
            ai_results["improvements"] = seo_improvements(raw, audit)
            ai_results["content"]      = content_optimisation(raw, audit)
            ai_results["technical"]    = technical_guidance(raw, audit)
            ai_results["ux"]           = ux_suggestions(raw, audit)
            ai_results["keywords"]     = keyword_strategy(raw, audit)

        # Save to session state
        st.session_state.audit   = audit
        st.session_state.raw_data = raw
        st.session_state.ai       = ai_results
```

### The radar chart

```python
fig = go.Figure(go.Scatterpolar(
    r=scores_list + [scores_list[0]],   # close the polygon
    theta=cats_order + [cats_order[0]],
    fill="toself",
    fillcolor="rgba(79,70,229,0.15)",
    line=dict(color="#4f46e5", width=2),
))
fig.update_layout(polar=dict(radialaxis=dict(range=[0,100])))
```

Each category becomes a point on the radar — concave areas show where improvement is needed.

### Issue cards via HTML

Instead of plain Streamlit text, issues use custom HTML cards:

```python
css_map = {"critical":"issue-critical","warning":"issue-warning",...}
st.markdown(f"""
<div class="{css_map[severity]}">
    <div class="issue-title">{icon} {message}</div>
    <div class="issue-fix">→ {fix}</div>
</div>
""", unsafe_allow_html=True)
```

The CSS is defined in the global `st.markdown("""<style>...</style>""")` block at the top of the file.

---

## 10. Running Locally

```bash
source venv/bin/activate
streamlit run app.py
# Opens at http://localhost:8501
```

### First Run Walkthrough

1. **🔑 Settings** → Enter your OpenAI API key → Save
2. **🔍 Audit** → Enter a URL (try `https://wikipedia.org` or your own site)
3. Make sure "Run AI Analysis" is checked
4. Click **🔍 Audit** button
5. Watch the status box: scraping → analysing → 5 AI calls
6. Auto-navigates to **📊 Dashboard** — see your score and radar chart
7. Click each issue to see the full details and fix
8. Go to **🤖 AI Suggestions** → review quick wins and content options
9. Go to **📈 Keywords** → see what keywords the page is actually about
10. Go to **⚙️ Technical** → see performance and schema recommendations
11. Go to **📤 Export** → download your PDF report

---

## 11. Deploying to Streamlit Cloud

```bash
git add . && git commit -m "AI SEO Audit Agent" && git push
```

1. [share.streamlit.io](https://share.streamlit.io) → New app
2. Select repo, main file: `app.py`
3. **Advanced settings → Secrets:**

```toml
OPENAI_API_KEY = "sk-your-openai-key"
```

4. Click **Deploy** ✅ — live in ~2 minutes

> Users can also add their own key via **🔑 Settings** — perfect for public demos.

---

## 12. Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Could not connect` | Bad URL or site blocks bots | Check the URL is publicly accessible |
| `SSL certificate error` | Invalid cert | Try `http://` instead of `https://` |
| `Request timed out` | Site too slow | Try again or increase TIMEOUT in scraper.py |
| `Invalid API key` | Wrong key | Go to 🔑 Settings → re-enter key |
| `lxml not found` | Missing parser | `pip install lxml` |
| AI sections blank | AI not enabled | Check "Run AI Analysis" checkbox |
| `Invalid format: TOML` | Wrong secrets format | Use `KEY = "value"` with quotes |
| PDF generation failed | ReportLab issue | Check special characters in content |
| Score seems wrong | Different page served | Some sites serve different content to bots |

---

## 13. What You Learned

- ✅ **Web scraping with requests + BeautifulSoup** — headers, load time measurement, HTML parsing
- ✅ **lxml parser** — faster HTML parsing for production
- ✅ **Rule-based scoring systems** — weighted multi-category scoring with issue severity levels
- ✅ **Keyword frequency analysis** — Counter, stop words, density calculation
- ✅ **Focused GPT-4o calls** — specialist system prompts, JSON schema enforcement
- ✅ **Graceful AI degradation** — app works without AI, each call independent
- ✅ **ReportLab PDF generation** — story pattern, TableStyle, multi-page documents
- ✅ **Plotly radar charts** — Scatterpolar with fill for multi-category visualization
- ✅ **Custom HTML cards in Streamlit** — `unsafe_allow_html=True` with CSS classes
- ✅ **Session state for multi-page apps** — persisting audit results across page navigations
- ✅ **User-provided API keys** — session-only storage, server key fallback pattern

---

## 14. What's Next

### Easy
- **Multiple URL audit** — audit all pages on a site (crawl internal links)
- **Competitor comparison** — audit two URLs side by side
- **Historical tracking** — save audits to Supabase and track score over time

### Intermediate
- **Google PageSpeed API** — get real Core Web Vitals data (LCP, FID, CLS)
- **Google Search Console integration** — pull actual keyword ranking data
- **Broken link checker** — test all internal links for 404 errors

### Advanced
- **Full site crawl** — follow all internal links, audit every page
- **SERP snippet preview** — show how the title/description looks in Google
- **Automated monitoring** — weekly scheduled audits with email alerts on score drops

---

## ⭐ Enjoyed this tutorial?

- ⭐ **[Star the repository](https://github.com/adityasharmadotai-hash)** — helps others discover this
- 🌐 **[Visit adityasharma.ai](https://www.adityasharma.ai)** — AI training for professionals
- 💼 **[Follow on LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)** — daily AI updates
- 📺 **[Subscribe on YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)** — AI agent tutorials
- 🚀 **[AI Jobs in the USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

---

*Built with ❤️ by [Aditya Sharma](https://www.adityasharma.ai) · OpenAI GPT-4o + BeautifulSoup + Streamlit*
