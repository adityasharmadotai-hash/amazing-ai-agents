# 🎯 Build an AI Resume & Job Match Agent from Scratch

### A Step-by-Step Tutorial for Beginners to Intermediate Developers

> ⭐ **Star the repo:** [github.com/adityasharmadotai-hash](https://github.com/adityasharmadotai-hash)
> 💼 **Follow on LinkedIn:** [linkedin.com/in/aditya-hicounselor](https://www.linkedin.com/in/aditya-hicounselor/)
> 📺 **Subscribe on YouTube:** [YouTube Channel](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)
> 🚀 **AI Jobs in the USA:** [Apply Now](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)

---

> **What you'll build:** A full-stack AI career assistant that parses resumes, scores job matches, checks ATS compatibility, generates cover letters, and preps you for interviews — powered by OpenAI GPT-4o, Supabase, and deployed free on Streamlit Cloud.

---

## 📋 Table of Contents

1. [What Are We Building?](#1-what-are-we-building)
2. [How It Works](#2-how-it-works)
3. [Prerequisites](#3-prerequisites)
4. [Project Setup](#4-project-setup)
5. [File 1 — parser.py](#5-file-1--parserpy)
6. [File 2 — database.py](#6-file-2--databasepy)
7. [File 3 — agent.py](#7-file-3--agentpy)
8. [File 4 — exporter.py](#8-file-4--exporterpy)
9. [File 5 — app.py](#9-file-5--apppy)
10. [Supabase Setup](#10-supabase-setup)
11. [Running Locally](#11-running-locally)
12. [Deploying to Streamlit Cloud](#12-deploying-to-streamlit-cloud)
13. [Common Errors & Fixes](#13-common-errors--fixes)
14. [What You Learned](#14-what-you-learned)
15. [What's Next](#15-whats-next)

---

## 1. What Are We Building?

Imagine having a personal career coach available 24/7 that:

- Reads your entire resume in seconds
- Tells you **exactly** how well you match any job posting
- Shows which skills are missing and how to fix them
- Runs your resume through an **ATS scanner** before you apply
- Writes a **custom cover letter** for every application
- Prepares you with **likely interview questions** for the specific role

That's exactly what this app does.

```
📄 Upload Resume
      ↓
🧠 GPT-4o parses your entire background
      ↓
📋 Paste any job description
      ↓
🎯 Match score, gap analysis, ATS score
      ↓
✉️ AI-written tailored cover letter
      ↓
💬 Interview questions with answer guidance
      ↓
📊 Dashboard tracking all your applications
```

**Real-world use cases:**
- Job seekers applying to multiple roles at once
- Career coaches building tools for their clients
- Recruiters pre-screening candidates efficiently
- Developers learning full-stack AI app architecture

---

## 2. How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION FLOW                           │
│                                                                 │
│  USER UPLOADS RESUME (.pdf or .docx)                           │
│           ↓                                                      │
│    parser.py                                                    │
│    pypdf reads PDF pages / python-docx reads DOCX              │
│    returns raw text string                                      │
│           ↓                                                      │
│    agent.py → OpenAI GPT-4o                                    │
│    sends raw text + structured parsing prompt                   │
│    GPT-4o returns JSON: skills, experience, education          │
│           ↓                                                      │
│    database.py → Supabase (PostgreSQL)                         │
│    saves resume permanently to cloud DB                        │
│                                                                 │
│  USER PASTES JOB DESCRIPTION                                   │
│           ↓                                                      │
│    agent.py → GPT-4o (match_job)                               │
│    compares resume JSON vs job text                             │
│    returns score 0-100, grade, gaps, recommendations           │
│           ↓                                                      │
│    agent.py → GPT-4o (check_ats)                               │
│    checks keyword density, formatting, section quality          │
│           ↓                                                      │
│    database.py → Supabase — saves analysis                     │
│           ↓                                                      │
│    app.py (Streamlit)                                           │
│    renders score badge, radar chart, skill pills               │
│    cover letter editor, interview Q&A cards                    │
│    PDF export via exporter.py                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Five files, each with one clear job:**

| File | Job | Lines |
|------|-----|-------|
| `modules/parser.py` | Extracts text from PDF/DOCX | ~60 |
| `modules/database.py` | Supabase CRUD — all tables | ~250 |
| `modules/agent.py` | All 6 GPT-4o API calls | ~280 |
| `modules/exporter.py` | PDF generation via ReportLab | ~150 |
| `app.py` | Streamlit UI — 8 pages | ~700 |

---

## 3. Prerequisites

Before starting, make sure you have:

### ✅ Required

- [ ] **Python 3.10+** — [python.org/downloads](https://python.org/downloads)
- [ ] **OpenAI API key** — [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- [ ] **Supabase account (free)** — [supabase.com](https://supabase.com)
- [ ] **GitHub account** — [github.com](https://github.com)
- [ ] **Streamlit account (free)** — [share.streamlit.io](https://share.streamlit.io)

### 💡 Verify Python version

```bash
python3 --version
# Should show Python 3.10.x or higher
```

### 💰 API Cost Estimate

This app uses `gpt-4o`. Typical costs per full workflow:
- Resume parse: ~$0.003
- Job match analysis: ~$0.004
- ATS check: ~$0.003
- Cover letter: ~$0.005
- Interview questions: ~$0.006
- **Total per analysis: ~$0.02**

Very affordable for personal use.

---

## 4. Project Setup

### Step 1 — Create project folder

```bash
mkdir resume-job-agent
cd resume-job-agent
mkdir modules sample_data .streamlit
```

### Step 2 — Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows
```

### Step 3 — Install all dependencies

```bash
pip install streamlit openai supabase python-docx pypdf pdfplumber reportlab plotly pandas python-dotenv
```

### Step 4 — Create your credentials file

```bash
cp .env.example .env
# Edit .env and fill in your keys
```

Your `.env` file:
```
OPENAI_API_KEY=sk-your-openai-key-here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key-here
```

### Step 5 — Initialise git

```bash
git init
git add .
git commit -m "Initial setup"
```

---

## 5. File 1 — `parser.py`

> **What this file does:** Takes a raw file upload from Streamlit and returns plain text. Handles PDF and DOCX with a graceful fallback between two PDF libraries.

### The Full Code

```python
import io
import os

def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except ImportError:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages).strip()
    except Exception as e:
        return f"[Error reading PDF: {e}]"

def extract_text_from_docx(file_bytes: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    lines = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(c.text.strip() for c in row.cells if c.text.strip())
            if row_text:
                lines.append(row_text)
    return "\n".join(lines)

def extract_resume_text(uploaded_file) -> str:
    file_bytes = uploaded_file.read()
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif name.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    return "[Unsupported format]"
```

### Key Concepts Explained

**Why `io.BytesIO`?**
Streamlit gives you bytes from an uploaded file. PDF/DOCX libraries expect a file-like object. `io.BytesIO` wraps bytes into a file-like object without writing anything to disk — critical on Streamlit Cloud which has an ephemeral filesystem.

**Why two PDF libraries?**
`pypdf` is fast and handles most PDFs well. But some PDFs (scanned, complex layouts) fail with pypdf. `pdfplumber` is slower but more robust. We try pypdf first, fall back to pdfplumber automatically.

**Why parse tables separately in DOCX?**
Word tables aren't in `doc.paragraphs`. Many resumes use table layouts for the skills section or contact info. Without this, those sections would be silently lost.

---

## 6. File 2 — `database.py`

> **What this file does:** All Supabase read/write operations. Every function has the same signature as the old SQLite version — so `app.py` needed zero changes when we switched databases.

### Why Supabase Instead of SQLite?

Streamlit Community Cloud has an **ephemeral filesystem** — any local SQLite file gets wiped when the app restarts or goes to sleep. Supabase is a free hosted PostgreSQL database that persists forever.

| | SQLite | Supabase |
|--|--------|---------|
| Setup | Zero config | 5 minutes |
| Persistence on Streamlit Cloud | ❌ Resets on sleep | ✅ Permanent |
| JSONB columns | ❌ Stores as text | ✅ Native |
| Free tier | Unlimited local | 500MB, 2 projects |

### The Client Pattern

```python
import streamlit as st
from supabase import create_client

@st.cache_resource
def _get_client_cached(url: str, key: str):
    return create_client(url, key)

def _db():
    url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY")
    if not url or not key:
        return None
    return _get_client_cached(url, key)
```

`@st.cache_resource` — creates the Supabase client **once** and reuses it across all reruns. Without this, Streamlit would create a new connection on every user interaction.

`_db()` returns `None` if credentials are missing — every caller checks for `None` and returns a safe empty value instead of crashing.

### The Query Pattern

Every Supabase query follows the same chainable API:

```python
# INSERT
db.table("resumes").insert({"name": name, "parsed_data": data}).execute()

# SELECT with filter
db.table("resumes").select("*").eq("id", resume_id).execute()

# SELECT with JOIN (nested select)
db.table("job_analyses").select("*, resumes(name)").order("created_at", desc=True).execute()

# DELETE
db.table("resumes").delete().eq("id", resume_id).execute()
```

**JSONB columns** — Supabase's PostgreSQL stores GPT-4o's JSON output natively. You pass a Python dict in, you get a Python dict back. No `json.dumps()` / `json.loads()` needed.

### Schema Design

```sql
resumes              ← one row per uploaded resume
job_analyses         ← one row per job match run (FK → resumes)
cover_letters        ← one row per generated letter (FK → resumes)
interview_questions  ← one row per question set (FK → resumes)
```

`ON DELETE CASCADE` on all foreign keys — deleting a resume automatically cleans up all its related analyses, letters, and questions.

---

## 7. File 3 — `agent.py`

> **What this file does:** Contains one function per AI-powered feature. Each function has a carefully engineered system prompt and parses the JSON response safely.

### The Core Pattern

Every AI function follows the same structure:

```python
def some_feature(input_data) -> dict:
    system = """You are an expert in X.
    Return ONLY valid JSON with these exact keys:
    { "key1": ..., "key2": ... }"""

    user = f"Here is the data:\n{input_data}"

    raw = _call_openai(system, user, max_tokens=2000)
    return _safe_json(raw)
```

### The OpenAI Call

```python
def _call_openai(system: str, user: str, max_tokens: int = 2000) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
    )
    return response.choices[0].message.content
```

The `system` message sets GPT-4o's persona and output rules. The `user` message contains the actual data to process.

### The `_safe_json()` Function

GPT-4o sometimes wraps JSON in markdown fences:
````
```json
{ "match_score": 75 }
```
````

`_safe_json()` strips those before parsing:

```python
def _safe_json(text: str) -> dict:
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    return json.loads(cleaned)
```

### Prompt Engineering — The Most Important Skill

The system prompts are the heart of this app. Key techniques used:

**1. Role assignment**
```
"You are an expert HR consultant and talent acquisition specialist."
```
Activates GPT-4o's domain knowledge for that role.

**2. Strict output format**
```
"Return ONLY valid JSON (no markdown, no extra text) with these exact keys:"
```
Without this, the model adds explanatory prose that breaks JSON parsing.

**3. Schema with example types**
```json
{
  "match_score": 78,
  "grade": "B+",
  "strengths": ["strength 1", "strength 2"],
  "missing_skills": ["skill1", "skill2"]
}
```
Providing the exact schema with example values dramatically improves consistency.

### The Six AI Functions

| Function | Input | Output |
|----------|-------|--------|
| `parse_resume(text)` | Raw resume text | Structured candidate dict |
| `match_job(resume, jd)` | Resume dict + JD string | Score, grade, gaps, recs |
| `check_ats(text, jd)` | Resume text + JD | ATS score, keyword analysis |
| `generate_cover_letter(...)` | Resume + JD + tone | Formatted letter text |
| `generate_interview_questions(...)` | Resume + JD | Categorised Q&A |
| `get_resume_improvements(...)` | Resume data | Specific rewrite suggestions |

---

## 8. File 4 — `exporter.py`

> **What this file does:** Generates downloadable PDFs from cover letters and analysis reports using ReportLab.

### Key ReportLab Concepts

**Story** — a list of elements rendered top-to-bottom:
```python
story = []
story.append(Paragraph("Your Name", header_style))
story.append(Spacer(1, 0.2 * inch))
story.append(HRFlowable(width="100%"))
```

**Styles** — define font, size, color, spacing:
```python
header_style = ParagraphStyle("Header",
    fontSize=14, fontName="Helvetica-Bold",
    textColor=colors.HexColor("#1e3a5f"))
```

**Building to bytes** — Streamlit's `st.download_button` accepts bytes:
```python
buffer = io.BytesIO()
doc = SimpleDocTemplate(buffer, pagesize=letter)
doc.build(story)
buffer.seek(0)
return buffer.read()  # bytes → download button
```

---

## 9. File 5 — `app.py`

> **What this file does:** The entire Streamlit UI — sidebar navigation, 8 pages, custom CSS, and all session state management.

### Page Architecture

The app uses a single file with a radio button router:

```python
page = st.radio("Navigation", [
    "🏠 Dashboard",
    "📄 Upload Resume",
    "🔍 Job Matching",
    "🤖 ATS Checker",
    "✉️ Cover Letter",
    "💬 Interview Prep",
    "📊 Analytics",
    "📁 History",
])

if page == "🏠 Dashboard":
    # dashboard code
elif page == "📄 Upload Resume":
    # upload code
# ... etc
```

### Session State — The Most Important Streamlit Concept

Streamlit reruns your **entire script** on every user interaction. Session state persists values between reruns:

```python
# Initialise once
if "active_resume_id" not in st.session_state:
    st.session_state.active_resume_id = None

# Set after upload
st.session_state.active_resume_id = resume_id

# Read on any page — value persists
resume_id = st.session_state.active_resume_id
```

**Key session variables used:**

| Variable | Purpose |
|----------|---------|
| `active_resume_id` | DB id of the currently loaded resume |
| `active_resume_data` | Full resume dict (raw text + parsed JSON) |
| `active_job_analysis_id` | DB id of the latest job analysis |
| `active_match` | Latest GPT-4o match result dict |
| `active_ats` | Latest ATS result dict |
| `active_cover_letter` | Generated cover letter text |
| `active_interview_qs` | Generated questions dict |

### Custom CSS Technique

```python
st.markdown("""
<style>
.metric-card {
    background: white;
    border-radius: 16px;
    padding: 24px;
    border-left: 4px solid #3b82f6;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.score-high { background: linear-gradient(135deg, #22c55e, #16a34a); }
.pill { background: #eff6ff; border-radius: 20px; padding: 4px 12px; }
</style>
""", unsafe_allow_html=True)
```

Then use in components:
```python
st.markdown(f'<div class="metric-card">...</div>', unsafe_allow_html=True)
```

### The Credential Check

The app runs `_show_setup_banner()` at startup before any page renders. It checks all three required secrets and shows a clear error with the exact TOML to paste if any are missing — then calls `st.stop()` so nothing else runs:

```python
def _show_setup_banner():
    missing = []
    try:
        ok_openai = bool(st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY"))
    except Exception:
        ok_openai = bool(os.environ.get("OPENAI_API_KEY"))
    # ... check supabase keys ...
    if missing:
        st.error("Setup required — missing: " + ", ".join(missing))
        st.code('OPENAI_API_KEY = "sk-..."\nSUPABASE_URL = "..."\nSUPABASE_KEY = "..."')
        st.stop()
```

---

## 10. Supabase Setup

### Step 1 — Create a free project

1. Go to [supabase.com](https://supabase.com) → **Sign up** (free)
2. Click **New Project** → fill in name and password
3. Wait ~2 minutes for provisioning

### Step 2 — Run the schema

1. In your project dashboard → click **SQL Editor** (left sidebar)
2. Click **New Query**
3. Paste the entire contents of `supabase_schema.sql`:

```sql
-- Create all tables
CREATE TABLE IF NOT EXISTS resumes (
    id          BIGSERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    filename    TEXT,
    raw_text    TEXT,
    parsed_data JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS job_analyses (
    id              BIGSERIAL PRIMARY KEY,
    resume_id       BIGINT REFERENCES resumes(id) ON DELETE CASCADE,
    job_title       TEXT,
    company_name    TEXT,
    job_description TEXT,
    match_result    JSONB,
    ats_result      JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cover_letters (
    id              BIGSERIAL PRIMARY KEY,
    resume_id       BIGINT REFERENCES resumes(id) ON DELETE CASCADE,
    job_analysis_id BIGINT,
    company_name    TEXT,
    job_title       TEXT,
    content         TEXT,
    tone            TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS interview_questions (
    id              BIGSERIAL PRIMARY KEY,
    resume_id       BIGINT REFERENCES resumes(id) ON DELETE CASCADE,
    job_analysis_id BIGINT,
    questions_data  JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Grant permissions
GRANT ALL ON resumes, job_analyses, cover_letters, interview_questions TO anon, authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- Disable RLS for simplicity
ALTER TABLE resumes              DISABLE ROW LEVEL SECURITY;
ALTER TABLE job_analyses         DISABLE ROW LEVEL SECURITY;
ALTER TABLE cover_letters        DISABLE ROW LEVEL SECURITY;
ALTER TABLE interview_questions  DISABLE ROW LEVEL SECURITY;
```

4. Click **Run ▶** — you should see "Success. No rows returned."

### Step 3 — Get your credentials

Go to **Project Settings → API**:
- Copy **Project URL** → this is your `SUPABASE_URL`
- Copy **anon public** key → this is your `SUPABASE_KEY`

---

## 11. Running Locally

```bash
# 1. Activate your virtual environment
source venv/bin/activate

# 2. Make sure .env exists with all three keys
cat .env
# OPENAI_API_KEY=sk-...
# SUPABASE_URL=https://...
# SUPABASE_KEY=...

# 3. Run
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501)

### First Run Walkthrough

1. Go to **📄 Upload Resume** → upload a PDF or DOCX
2. Click **Parse Resume with GPT-4o** → see extracted skills, experience, education
3. Go to **🔍 Job Matching** → paste the sample job from `sample_data/`
4. Click **Analyze Match** → see your score, radar chart, missing skills
5. Go to **🤖 ATS Checker** → run ATS analysis on your resume
6. Go to **✉️ Cover Letter** → paste the JD, click Generate
7. Go to **💬 Interview Prep** → get role-specific questions with answer guidance
8. Go to **📊 Analytics** → see your score history and distribution charts

---

## 12. Deploying to Streamlit Cloud

### Step 1 — Push to GitHub

```bash
git add .
git commit -m "AI Resume Job Agent — production ready"
git push origin main
```

> ⚠️ Never commit `.env`. Check with `git status` — it should NOT appear.

### Step 2 — Create app on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **New app**
4. Select your repository and branch
5. Set **Main file path**: `app.py` (or the full path if in a subfolder)

### Step 3 — Add secrets (TOML format — quotes required)

Click **Advanced settings → Secrets** and paste:

```toml
OPENAI_API_KEY = "sk-your-openai-key-here"
SUPABASE_URL   = "https://your-project-id.supabase.co"
SUPABASE_KEY   = "your-supabase-anon-key-here"
```

> ⚠️ **Common mistake:** Using `KEY=value` (dotenv format) instead of `KEY = "value"` (TOML format). Streamlit Cloud requires TOML — values must be in quotes.

### Step 4 — Deploy

Click **Deploy** — your app will be live at a URL like:
```
https://your-username-resume-agent-app-xxxx.streamlit.app
```

In ~2 minutes. ✅

---

## 13. Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `relation "resumes" does not exist` | Schema not created in Supabase | Run `supabase_schema.sql` in Supabase SQL Editor |
| `postgrest.exceptions.APIError` | Table exists but no permissions | Run the `GRANT` and `DISABLE ROW LEVEL SECURITY` statements |
| `Invalid format: please enter valid TOML` | Using `KEY=value` not `KEY = "value"` | Add quotes and spaces: `KEY = "value"` |
| `openai.AuthenticationError` | Wrong OpenAI API key | Check `OPENAI_API_KEY` in Streamlit secrets |
| `Supabase credentials missing` | Secrets not set in Streamlit Cloud | Add all 3 keys to App → Settings → Secrets |
| `ImportError: No module named 'supabase'` | Package not installed | `pip install -r requirements.txt` |
| Cover letter contains `[placeholders]` | Job description not provided | Always paste the full job description before generating |
| PDF export returns garbled bytes | reportlab not installed | Already in requirements.txt — trigger a redeploy |
| `RateLimitError` from OpenAI | Quota exceeded | Add billing at [platform.openai.com](https://platform.openai.com) |
| Dashboard shows zeros | Supabase connected but tables empty | Normal on first run — upload a resume and run an analysis |

---

## 14. What You Learned

By completing this tutorial, you've learned:

- ✅ **Modular Python architecture** — splitting a complex app into focused single-responsibility files
- ✅ **Prompt engineering** — writing system prompts that reliably return structured JSON
- ✅ **Streamlit session state** — persisting data across script reruns
- ✅ **Supabase (PostgreSQL)** — cloud database with JSONB columns, nested selects, and permissions
- ✅ **File handling** — reading PDF and DOCX in memory without writing to disk
- ✅ **PDF generation** — building professional documents with ReportLab
- ✅ **Plotly charts** — radar, histogram, and scatter plots in Streamlit
- ✅ **Custom Streamlit CSS** — making Streamlit look production-quality
- ✅ **OpenAI GPT-4o API** — chat completions with system/user message structure
- ✅ **Streamlit Cloud deployment** — secrets management, TOML format, common pitfalls

---

## 15. What's Next

Now that you have a working production app, here are some ideas to extend it:

### Easy
- **LinkedIn URL scraper** — paste a LinkedIn job URL and auto-fill the job description
- **Resume score without JD** — standalone quality score before any job application
- **Dark mode toggle** — add a theme switcher to the sidebar

### Intermediate
- **Multi-language support** — add a language selector; GPT-4o handles most languages natively
- **Salary estimator** — add a GPT-4o call that estimates salary range from the job description
- **Batch job matching** — upload 5 JDs at once and rank them by match score

### Advanced
- **Vector search** — embed resumes with OpenAI embeddings; find best-fit jobs from a stored database
- **Resume builder** — let users create a resume from scratch using structured input + GPT-4o
- **API mode** — expose resume matching as a REST API endpoint using FastAPI

---

## ⭐ Enjoyed this tutorial?

If you learned something from this project, it would mean a lot if you could:

- ⭐ **[Star the repository](https://github.com/adityasharmadotai-hash)** — helps others discover this project
- 💼 **[Follow on LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)** — daily AI news, tools, and updates
- 📺 **[Subscribe on YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)** — AI agents, tutorials, and the latest in AI
- 🚀 **[AI Jobs in the USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)** — apply now

---

*Built with ❤️ using Python, OpenAI GPT-4o, Supabase, and Streamlit*
