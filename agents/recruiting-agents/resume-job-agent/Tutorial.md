# 🎯 Build an AI Resume & Job Match Agent from Scratch

### A Step-by-Step Tutorial for Beginners to Intermediate Developers

> **What you'll build:** A full-stack AI career assistant that parses resumes, scores job matches, checks ATS compatibility, generates cover letters, and preps you for interviews — powered by OpenAI GPT-4o and deployed free on Streamlit Cloud.

---

## 📋 Table of Contents

1. [What Are We Building?](#1-what-are-we-building)
2. [How It Works](#2-how-it-works)
3. [Prerequisites](#3-prerequisites)
4. [Project Setup](#4-project-setup)
5. [Module 1 — parser.py (File Reading)](#5-module-1--parserpy)
6. [Module 2 — database.py (SQLite Storage)](#6-module-2--databasepy)
7. [Module 3 — agent.py (OpenAI GPT-4o Calls)](#7-module-3--agentpy)
8. [Module 4 — exporter.py (PDF Generation)](#8-module-4--exporterpy)
9. [Module 5 — app.py (Streamlit UI)](#9-module-5--apppy)
10. [Running Locally](#10-running-locally)
11. [Deploying to Streamlit Cloud](#11-deploying-to-streamlit-cloud)
12. [Testing the App](#12-testing-the-app)
13. [Common Errors & Fixes](#13-common-errors--fixes)
14. [Extending the App](#14-extending-the-app)

---

## 1. What Are We Building?

Imagine having a personal career coach available 24/7 that:
- Reads your resume in seconds
- Tells you exactly how well you match any job
- Rewrites it to beat ATS filters
- Writes a custom cover letter for every application
- Prepares you with likely interview questions

That's exactly what this app does.

```
📄 Resume Upload
      ↓
🧠 GPT-4o parses your entire background
      ↓
📋 Paste any job description
      ↓
🎯 Get match score, gap analysis, and improvements
      ↓
✉️ Generate tailored cover letter
      ↓
💬 Get interview prep questions
      ↓
📊 Track all applications in a dashboard
```

**Real-world use cases:**
- Job seekers who apply to multiple roles
- Career coaches building tools for clients
- Recruiters who want to pre-screen candidates
- Developers learning AI-powered app architecture

---

## 2. How It Works

```
┌────────────────────────────────────────────────────────────┐
│                    APPLICATION FLOW                         │
│                                                            │
│  USER UPLOADS RESUME (.pdf or .docx)                       │
│         ↓                                                   │
│   parser.py                                                │
│   - pypdf reads PDF pages                                  │
│   - python-docx reads DOCX paragraphs                      │
│   - returns raw text string                                │
│         ↓                                                   │
│   agent.py → OpenAI API                                    │
│   - sends raw text with a parsing prompt                   │
│   - GPT-4o returns structured JSON                         │
│   - skills, experience, education, projects                │
│         ↓                                                   │
│   database.py                                              │
│   - saves resume to SQLite                                 │
│         ↓                                                   │
│  USER PASTES JOB DESCRIPTION                               │
│         ↓                                                   │
│   agent.py → OpenAI API (match_job)                        │
│   - compares resume JSON with job text                     │
│   - returns score, grade, gaps, recs                       │
│         ↓                                                   │
│   agent.py → OpenAI API (check_ats)                        │
│   - checks keyword match                                   │
│   - checks formatting issues                               │
│         ↓                                                   │
│   database.py                                              │
│   - saves analysis to SQLite                               │
│         ↓                                                   │
│   app.py (Streamlit)                                       │
│   - renders score, charts, pill tags                       │
│   - cover letter, interview questions                      │
│   - PDF export via exporter.py                             │
└────────────────────────────────────────────────────────────┘
```

**Five files, each with one clear job:**

| File | Job | Size |
|------|-----|------|
| `modules/parser.py` | Extracts text from PDF/DOCX | ~60 lines |
| `modules/database.py` | SQLite CRUD operations | ~200 lines |
| `modules/agent.py` | All OpenAI API prompts | ~250 lines |
| `modules/exporter.py` | PDF generation | ~150 lines |
| `app.py` | Streamlit UI + routing | ~600 lines |

---

## 3. Prerequisites

Before starting, you need:

### ✅ Required

- [ ] **Python 3.10+** — [python.org/downloads](https://python.org/downloads)
- [ ] **OpenAI API key** — [platform.openai.com/api-keys](https://platform.openai.com/api-keys) (requires billing)
- [ ] **GitHub account** — [github.com](https://github.com)
- [ ] **Streamlit account** — [share.streamlit.io](https://share.streamlit.io) (free)

### 💡 Verify Python version

```bash
python3 --version
# Should show Python 3.10.x or higher
```

### 💰 OpenAI API Costs

This app uses `gpt-4o`. Typical costs:
- Resume parse: ~$0.003
- Job match: ~$0.004
- Cover letter: ~$0.005
- Interview questions: ~$0.006
- Full workflow: ~$0.02 per resume analysis

Very affordable for personal use.

---

## 4. Project Setup

### Step 1 — Create folder structure

```bash
mkdir resume-job-agent
cd resume-job-agent
mkdir modules sample_data exports .streamlit
```

### Step 2 — Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate     # macOS/Linux
# or
venv\Scripts\activate        # Windows
```

### Step 3 — Install dependencies

```bash
pip install streamlit openai python-docx pypdf pdfplumber reportlab plotly pandas python-dotenv
```

### Step 4 — Set up your API key

Create `.env`:
```
OPENAI_API_KEY=sk-...your-key-here...
```

### Step 5 — Initialize git

```bash
git init
echo ".env\ndata/\nvenv/" > .gitignore
git add .
git commit -m "Initial setup"
```

---

## 5. Module 1 — `parser.py`

> **What this file does:** Takes a raw file upload from Streamlit and returns plain text. Handles both PDF and DOCX formats with a graceful fallback.

### Key Concepts

**Why two PDF libraries?**
`pypdf` is fast and handles most PDFs well. But some PDFs (scanned, complex layouts) fail with pypdf. `pdfplumber` is slower but more robust. We try pypdf first, fall back to pdfplumber.

```python
def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except ImportError:
        # Fall back to pdfplumber
        import pdfplumber
        ...
```

**Why `io.BytesIO`?**
Streamlit gives you bytes from an uploaded file. PDF libraries expect a file-like object, not a path. `io.BytesIO` wraps bytes into a file-like object without writing to disk.

**DOCX tables:**
Word tables aren't in `doc.paragraphs`. If your resume has a table layout (very common), you must also iterate `doc.tables`:

```python
for table in doc.tables:
    for row in table.rows:
        row_text = " | ".join(cell.text.strip() for cell in row.cells)
```

---

## 6. Module 2 — `database.py`

> **What this file does:** All SQLite read/write operations. Keeps data between Streamlit sessions since Streamlit re-runs the script on every user interaction.

### Why Supabase?

- Free PostgreSQL database hosted in the cloud
- Data persists permanently — survives Streamlit Cloud restarts
- Simple Python SDK (`supabase-py`) with a clean chainable API
- JSONB columns store AI output without any schema migration

### Schema Design

```sql
resumes                    -- one row per uploaded resume
  id, name, filename, raw_text, parsed_data (JSON), created_at

job_analyses               -- one row per job match run
  id, resume_id, job_title, company_name, job_description,
  match_result (JSON), ats_result (JSON), created_at

cover_letters              -- one row per generated letter
  id, resume_id, job_analysis_id, company_name, job_title,
  content, tone, created_at

interview_questions        -- one row per question set
  id, resume_id, job_analysis_id, questions_data (JSON), created_at
```

**Why JSONB columns?**
Postgres JSONB stores structured data natively. Supabase returns JSONB columns already parsed as Python dicts — no `json.loads()` needed. This makes storing GPT-4o's JSON output clean and queryable.

### Key Pattern: nested select for JOINs

Supabase's Python client uses a chainable API. To fetch a joined column:

```python
_db().table("job_analyses").select("*, resumes(name)").execute()
```

The nested `resumes(name)` tells Supabase to include the related resume's name — equivalent to a SQL LEFT JOIN.

### The `init_db()` Function

With Supabase, `init_db()` is a no-op — tables are created once via `supabase_schema.sql` in the Supabase SQL Editor. The function exists only for backwards compatibility so `app.py` doesn't need changing.

---

## 7. Module 3 — `agent.py`

> **What this file does:** Contains one function per GPT-4o-powered feature. Each function has a carefully designed system prompt and parses the JSON response.

### The Core Pattern

Every AI function in this app follows the same structure:

```python
def some_feature(input_data) -> dict:
    system = """You are an expert in X.
    Return ONLY valid JSON with these exact keys:
    { "key1": ..., "key2": ... }"""
    
    user = f"Here is the data: {input_data}"
    
    raw = _call_openai(system, user, max_tokens=2000)
    return _safe_json(raw)   # strips markdown fences, parses JSON
```

### Why `_safe_json()`?

The model occasionally wraps JSON in markdown code fences:
````
```json
{ "score": 75 }
```
````

`_safe_json()` strips those before parsing:

```python
def _safe_json(text: str) -> dict | list:
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    return json.loads(cleaned)
```

### Prompt Engineering Deep Dive

The system prompts are the most important part. Key techniques used:

**1. Role assignment**
```
"You are an expert HR consultant and talent acquisition specialist."
```
Sets the AI's persona and activates domain-specific knowledge.

**2. Output format specification**
```
"Return ONLY valid JSON (no markdown, no extra text) with these exact keys:"
```
Critical — without this, the model adds explanatory text that breaks JSON parsing.

**3. Schema definition**
```json
{
  "match_score": 78,
  "grade": "B+",
  ...
}
```
Providing the exact schema with example values dramatically improves consistency.

**4. Behavioral rules**
```
"- If answer not in documents, say 'I could not find that'"
"- Always mention which company/role your answer is about"
```
Specific rules prevent hallucination and improve output quality.

### The Six AI Functions

| Function | System Prompt Focus | Output |
|---|---|---|
| `parse_resume()` | Expert resume parser | Structured candidate data |
| `match_job()` | HR consultant | Score, grade, strengths, gaps |
| `check_ats()` | ATS specialist | Keyword scores, formatting issues |
| `generate_cover_letter()` | Professional writer | Formatted letter text |
| `generate_interview_questions()` | Expert interviewer | Categorized Q&A |
| `get_resume_improvements()` | Resume coach | Specific rewrites |

---

## 8. Module 4 — `exporter.py`

> **What this file does:** Generates downloadable PDF files from analysis results and cover letters using ReportLab.

### Why ReportLab?

ReportLab is the industry standard for programmatic PDF generation in Python. It gives precise control over layout, fonts, colors, and tables — important for professional-looking documents.

### Key ReportLab Concepts

**Styles** — define font, size, color, spacing:
```python
from reportlab.lib.styles import ParagraphStyle
header_style = ParagraphStyle("Header",
    fontSize=14, fontName="Helvetica-Bold",
    textColor=colors.HexColor("#1e3a5f"))
```

**Story** — list of elements to render top-to-bottom:
```python
story = []
story.append(Paragraph("Your Name", header_style))
story.append(Spacer(1, 0.2 * inch))
story.append(HRFlowable(width="100%"))  # horizontal rule
```

**Tables** — for structured data like scores:
```python
data = [["Header 1", "Header 2"], ["Value 1", "Value 2"]]
table = Table(data, colWidths=[2*inch, 2*inch])
table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.navy)]))
```

**SimpleDocTemplate** — renders the story to a PDF buffer:
```python
buffer = io.BytesIO()
doc = SimpleDocTemplate(buffer, pagesize=letter)
doc.build(story)
buffer.seek(0)
return buffer.read()  # return bytes for Streamlit download button
```

---

## 9. Module 5 — `app.py`

> **What this file does:** The entire Streamlit UI — sidebar navigation, 8 pages, custom CSS, session state management, and all user interactions.

### Page Architecture

The app uses a single `app.py` with radio button navigation:

```python
page = st.radio("Navigation", [
    "🏠 Dashboard",
    "📄 Upload Resume",
    "🔍 Job Matching",
    ...
])

if page == "🏠 Dashboard":
    # render dashboard
elif page == "📄 Upload Resume":
    # render upload page
```

This is simpler than Streamlit's multipage feature for apps with shared state.

### Session State — The Most Important Concept

Streamlit re-runs your entire script on every user interaction. Session state persists values between re-runs:

```python
# Initialize on first run
if "active_resume_id" not in st.session_state:
    st.session_state.active_resume_id = None

# Set after upload
st.session_state.active_resume_id = resume_id
st.session_state.active_resume_data = parsed_data

# Read on any page
resume = st.session_state.active_resume_data
```

**Key session variables:**
```
active_resume_id        — ID of the currently loaded resume
active_resume_data      — full resume dict (raw text + parsed JSON)
active_job_analysis_id  — ID of the latest job analysis
active_match            — latest match result dict
active_ats              — latest ATS result dict
active_cover_letter     — generated cover letter text
active_interview_qs     — generated questions dict
```

### Custom CSS Technique

Streamlit allows injecting CSS via `st.markdown`:

```python
st.markdown("""
<style>
.metric-card {
    background: white;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    border-left: 4px solid #3b82f6;
}
</style>
""", unsafe_allow_html=True)
```

Then use HTML in markdown calls:
```python
st.markdown(f'<div class="metric-card">...</div>', unsafe_allow_html=True)
```

### Plotly Charts

The analytics page uses Plotly for interactive charts:

```python
import plotly.graph_objects as go

fig = go.Figure(data=go.Scatterpolar(
    r=values,
    theta=categories,
    fill="toself",
    line_color="#3b82f6",
))
st.plotly_chart(fig, use_container_width=True)
```

`use_container_width=True` makes charts responsive to the column width.

---

## 10. Running Locally

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Make sure your .env exists with your key
cat .env
# OPENAI_API_KEY=sk-...

# 3. Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501`

### First Run Walkthrough

1. Go to **📄 Upload Resume**
2. Upload a PDF or DOCX resume
3. Click **🤖 Parse Resume with GPT-4o**
4. Wait ~5 seconds — see parsed skills, experience, education
5. Go to **🔍 Job Matching**
6. Paste the sample job from `sample_data/sample_job_description.txt`
7. Click **🔍 Analyze Match** — see your match score and radar chart
8. Go to **✉️ Cover Letter** — paste the same JD, click Generate
9. Go to **💬 Interview Prep** — paste the JD, generate questions
10. Go to **📊 Analytics** — see your score charts

---

## 11. Deploying to Streamlit Cloud

Streamlit Cloud is free for public repos and gives you a permanent URL.

### Step 1 — Push to GitHub

```bash
git add .
git commit -m "Initial commit — AI Resume Agent"
git push origin main
```

> ⚠️ Never commit `.env` or the `data/` folder. Verify your `.gitignore` is working:
> `git status` should NOT show `.env` or `data/`

### Step 2 — Create app on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **New app**
4. Select your repository and branch
5. Set **Main file path**: `app.py`

### Step 3 — Add secrets

Click **Advanced settings** → **Secrets** and paste:

```toml
OPENAI_API_KEY = "sk-your-key-here"
```

### Step 4 — Deploy

Click **Deploy**. In 2–3 minutes you'll have a URL like:
```
https://your-username-resume-agent-app-xxxx.streamlit.app
```

### ⚠️ Note on SQLite in the Cloud

Streamlit Cloud has an **ephemeral filesystem** — data resets on each deployment. For persistent storage in production, consider replacing SQLite with:
- **Supabase** (free PostgreSQL tier)
- **PlanetScale** (free MySQL tier)
- **Streamlit's built-in `st.experimental_data_editor`**
- **Google Sheets** (via gspread)

For local use and demos, SQLite works perfectly.

---

## 12. Testing the App

### Happy Path Tests

```
Upload & Parse:
✅ Upload a PDF resume → parsed name, skills, and experience appear
✅ Upload a DOCX resume → same result
✅ Parsed skills show as pill tags

Job Match:
✅ Paste job description → match score between 0-100 appears
✅ Missing skills show as red pills
✅ Strengths show as green cards
✅ Radar chart renders

ATS Check:
✅ ATS score appears with grade
✅ Keyword found/missing sections populate
✅ Optimization suggestions have priority labels

Cover Letter:
✅ Generated letter is 3-4 paragraphs
✅ No [placeholder] brackets in output
✅ Download TXT works
✅ Download PDF works

Interview Prep:
✅ Questions generated across 4 categories
✅ Each question has a "why asked" and answer guidance

Dashboard:
✅ KPI cards show correct counts
✅ Score history chart renders after first analysis
```

### Edge Cases

```
⚠️ Empty job description → error message shown (not crash)
⚠️ Corrupt PDF → error message shown, not crash
⚠️ Very short resume → GPT-4o still returns valid JSON
⚠️ No API key → clear error on first GPT-4o call
⚠️ Very long JD (5000+ words) → may hit token limits, truncate JD
```

---

## 13. Common Errors & Fixes

| Error | Cause | Fix |
|---|---|---|
| `openai.AuthenticationError` | API key wrong or missing | Check `.env` or Streamlit secrets |
| `ModuleNotFoundError: No module named 'pypdf'` | Packages not installed | `pip install -r requirements.txt` |
| `No module named 'modules'` | Running from wrong directory | `cd resume-job-agent && streamlit run app.py` |
| `json.JSONDecodeError` | GPT-4o returned non-JSON | OpenAI rate limit or prompt issue; retry |
| `Error reading PDF: EOF marker not found` | Corrupted PDF | Re-save the PDF from source |
| Cover letter has `[Company Name]` | JD not provided before generation | Always fill in job description field |
| PDF export shows garbled text | Non-ASCII chars in resume | Add `encoding='utf-8'` handling in exporter |
| `OperationalError: no such table` | DB not initialized | `init_db()` at top of `app.py` |
| Charts don't render | Plotly not installed | `pip install plotly` |
| Streamlit secret not found | Wrong secret key name | Must be exactly `OPENAI_API_KEY` |

---

## 14. Extending the App

Now that you have a working app, here are some ideas to take it further:

### Easy Extensions

- **LinkedIn import** — scrape job descriptions directly from LinkedIn URLs using `beautifulsoup4`
- **Multi-language support** — add a language selector; GPT-4o handles most languages natively
- **Resume scoring without JD** — generate improvement suggestions standalone (already implemented in `agent.py`)
- **Email notifications** — use `smtplib` to email results after analysis

### Intermediate Extensions

- **Cloud database** — replace SQLite with Supabase for persistent cloud storage
- **Resume builder** — let users create resumes from scratch using GPT-4o's output
- **Salary estimator** — add a GPT-4o call that estimates salary range from the JD
- **Company research** — use GPT-4o with web search to summarize the company before interviews

### Advanced Extensions

- **Vector search** — embed resumes and JDs with sentence-transformers; find best-matching jobs from a database
- **Batch analysis** — upload multiple JDs and rank them by match score simultaneously
- **Fine-tuned prompts** — A/B test different system prompts to improve match accuracy
- **API mode** — expose resume matching as a REST API using FastAPI alongside Streamlit

---

## 🎓 What You Learned

By completing this tutorial, you've learned:

- ✅ **Modular Python architecture** — splitting a complex app into focused modules
- ✅ **Prompt engineering** — designing system prompts that return structured JSON
- ✅ **Streamlit session state** — persisting data across re-renders
- ✅ **SQLite patterns** — storing and querying structured + semi-structured data
- ✅ **File handling** — reading PDF and DOCX without writing to disk
- ✅ **PDF generation** — using ReportLab for professional document export
- ✅ **Plotly charts** — interactive radar, scatter, and histogram charts
- ✅ **Custom Streamlit CSS** — making Streamlit look professional
- ✅ **OpenAI API** — using OpenAI's SDK for structured AI outputs

---

*Built with ❤️ using Python, OpenAI GPT-4o, and Streamlit*

---

## ⭐ Enjoyed this tutorial?

If you learned something from this project, it would mean a lot if you could:

- ⭐ **Star the GitHub repository** — helps others discover this project
- 🐛 **Open an issue** — share bugs, ideas, or questions
- 🤝 **Submit a PR** — improvements and new features welcome
