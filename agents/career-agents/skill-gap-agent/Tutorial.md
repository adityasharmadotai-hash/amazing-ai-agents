# 📘 AI Skill Gap Agent — Complete Tutorial

This tutorial explains every file, every function, and every design decision.
By the end you will understand how to build, extend, and deploy this application yourself.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Application Flow](#2-application-flow)
3. [File 1 — `modules/parser.py`](#3-file-1--modulesparserpy)
4. [File 2 — `modules/database.py`](#4-file-2--modulesdatabasepy)
5. [File 3 — `modules/agent.py`](#5-file-3--modulesagentpy)
6. [File 4 — `modules/exporter.py`](#6-file-4--modulesexporterpy)
7. [File 5 — `app.py`](#7-file-5--apppy)
8. [Prompt Engineering Deep Dive](#8-prompt-engineering-deep-dive)
9. [Database Design](#9-database-design)
10. [UI/CSS System](#10-uicss-system)
11. [Extending the App](#11-extending-the-app)
12. [Deployment Guide](#12-deployment-guide)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AI SKILL GAP AGENT                              │
│                                                                     │
│  INPUT LAYER          AI LAYER              STORAGE LAYER           │
│  ──────────          ──────────             ──────────────           │
│  parser.py           agent.py              database.py              │
│  • PDF/DOCX          • parse_profile()     • SQLite                 │
│  • LinkedIn text     • analyze_skill_gap() • profiles table         │
│                      • calculate_readiness • analyses table         │
│                      • generate_roadmap()  • progress table         │
│                      • recommend_courses()                          │
│                      • generate_interview()                         │
│                      • suggest_projects()  OUTPUT LAYER             │
│                                            ──────────────           │
│  UI LAYER                                  exporter.py              │
│  ─────────                                 • PDF reports            │
│  app.py (Streamlit)                        • ReportLab              │
│  • 9 pages                                                          │
│  • Plotly charts                                                    │
│  • Interactive UI                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

**Five files, each with one clear responsibility:**

| File | Job | Key complexity |
|------|-----|----------------|
| `modules/parser.py` | Extract text from files | Multiple file formats |
| `modules/database.py` | SQLite CRUD | 3 tables, relationships |
| `modules/agent.py` | All GPT-4o calls | Prompt engineering |
| `modules/exporter.py` | PDF generation | ReportLab layout |
| `app.py` | Streamlit UI | 9 pages, custom CSS |

---

## 2. Application Flow

```
USER UPLOADS RESUME (.pdf or .docx) + pastes LinkedIn text
          ↓
    parser.py
    pdfplumber reads PDF pages → raw text string
    pypdf fallback if pdfplumber fails
    python-docx reads DOCX paragraphs
          ↓
    agent.py → OpenAI GPT-4o (parse_profile)
    sends raw text + structured parsing prompt
    GPT-4o returns JSON: skills, experience, education, projects
          ↓
    agent.py → GPT-4o (analyze_skill_gap)
    compares profile JSON vs target role requirements
    returns matched skills, missing skills, readiness breakdown
          ↓
    agent.py → GPT-4o (calculate_readiness)
    computes weighted score across 6 dimensions
    returns 0-100 score, letter grade, timeline
          ↓
    agent.py → GPT-4o (generate_roadmap)
    builds month-by-month 6-month plan
    includes weekly schedule + project milestones
          ↓
    agent.py → GPT-4o (recommend_courses)
    finds courses/books/certs per missing skill
          ↓
    agent.py → GPT-4o (generate_interview_prep)
    creates technical Qs, STAR behavioral Qs, salary tips
          ↓
    database.py → SQLite
    saves profile, analysis, and weekly progress tasks
          ↓
    app.py (Streamlit)
    renders score badge, radar chart, skill pills
    roadmap timeline, course cards, progress tracker
    PDF export via exporter.py
```

---

## 3. File 1 — `modules/parser.py`

> **What this file does:** Extracts raw text from uploaded resume files and normalizes LinkedIn text for AI processing.

### Why two PDF libraries?

```python
# Try pdfplumber first — better layout handling for complex PDFs
try:
    import pdfplumber
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        pages = [p.extract_text() or "" for p in pdf.pages]
        text = "\n".join(pages)
    if text.strip():
        return _clean_text(text)
except Exception:
    pass

# Fallback: pypdf — simpler, handles more edge cases
from pypdf import PdfReader
reader = PdfReader(io.BytesIO(file_bytes))
```

pdfplumber handles complex layouts (columns, tables) better. pypdf handles more corrupted files. Using both gives maximum coverage.

### The `_clean_text()` function

```python
def _clean_text(text: str) -> str:
    text = re.sub(r"[^\x20-\x7E\n]", " ", text)   # Remove non-printable chars
    text = re.sub(r" {2,}", " ", text)               # Collapse multiple spaces
    text = re.sub(r"\n{3,}", "\n\n", text)           # Max 2 newlines in a row
    return text.strip()
```

This normalization is critical — unclean text causes GPT-4o to waste tokens on garbage characters and sometimes hallucinate structure.

### The dispatch pattern

```python
def extract_text(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    file_bytes = uploaded_file.read()
    
    if name.endswith(".pdf"):   return extract_text_from_pdf(file_bytes)
    elif name.endswith(".docx"): return extract_text_from_docx(file_bytes)
    elif name.endswith(".txt"):  return _clean_text(file_bytes.decode("utf-8"))
    else: raise ValueError(f"Unsupported file type")
```

A clean dispatch pattern — adding a new format (e.g. `.odt`) means adding one elif.

---

## 4. File 2 — `modules/database.py`

> **What this file does:** All SQLite operations — creating tables, saving profiles, saving analyses, tracking progress.

### The Three Tables

```sql
profiles            -- Who the candidate is
  id, created_at, name, target_role, industry,
  resume_text, linkedin_text, parsed_data (JSON)

analyses            -- What AI found
  id, created_at, profile_id, readiness_score,
  skill_data, gap_data, roadmap_data, courses_data, interview_data (all JSON)

progress            -- Weekly task completion
  id, created_at, analysis_id, week_number, task_label, completed
```

### Why store everything as JSON?

The AI returns complex nested structures (lists of dicts inside dicts). Storing as JSON strings means:
- Zero schema migrations when AI output structure changes
- No ORM complexity
- Easy to deserialize: `json.loads(d["gap_data"])`

The tradeoff: you can't SQL-query inside the JSON (without SQLite JSON functions). For this app, that's fine — we always load full records.

### The connection pattern

```python
def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row   # rows behave like dicts
    return conn
```

`check_same_thread=False` is needed because Streamlit runs in a threaded environment. `row_factory = sqlite3.Row` means `dict(row)` works directly.

### JSON roundtrip pattern

```python
# Saving
conn.execute("INSERT ... VALUES (?)", (json.dumps(parsed_data),))

# Loading
d = dict(row)
d["parsed_data"] = json.loads(d["parsed_data"])
```

Every AI-generated field goes through this roundtrip. The `_safe_json()` function in agent.py handles the serialization side.

---

## 5. File 3 — `modules/agent.py`

> **What this file does:** Contains one function per AI-powered feature. Each function has a carefully engineered system prompt and safely parses the JSON response.

### The Core Pattern

Every AI function follows the same structure:

```python
def some_feature(input_data) -> dict:
    system = """You are an expert in X.
    Return ONLY valid JSON with these exact keys:
    { "key1": ..., "key2": ... }"""

    user = f"Here is the data:\n{input_data}"

    raw = _call_gpt(system, user, max_tokens=2000)
    return _safe_json(raw)
```

### The GPT-4o Call

```python
def _call_gpt(system: str, user: str, max_tokens: int = 3000) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=max_tokens,
        temperature=0.3,           # Lower = more consistent JSON
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
    )
    return response.choices[0].message.content
```

`temperature=0.3` is the sweet spot — low enough for consistent JSON structure, high enough for varied (not generic) recommendations.

### The `_safe_json()` Function

GPT-4o sometimes wraps JSON in markdown fences:
````
```json
{ "readiness_score": 72 }
```
````

`_safe_json()` strips those before parsing:

```python
def _safe_json(text: str) -> dict:
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: find the first JSON object
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise
```

### The Seven AI Functions

| Function | Input | Output | Tokens |
|----------|-------|--------|--------|
| `parse_profile()` | Resume + LinkedIn text | Structured candidate dict | 2000 |
| `analyze_skill_gap()` | Profile + target role | Matched, missing, transferable skills | 2500 |
| `calculate_readiness()` | Gap analysis | 0-100 score + grade + breakdown | 1500 |
| `generate_roadmap()` | Gap + readiness | 6-month monthly plan | 3000 |
| `recommend_courses()` | Missing skills | Courses, certs, books | 2500 |
| `generate_interview_prep()` | Profile + gaps | Technical Qs, STAR Qs, salary | 2500 |
| `suggest_portfolio_projects()` | Profile + gaps | Projects with tech stack | 2000 |

### API Cost Estimate

One full analysis (all 6 calls, excluding project suggestions which are on-demand):
- Input tokens: ~4,000
- Output tokens: ~6,000
- GPT-4o pricing: ~$0.05–0.08 per full analysis

---

## 6. File 4 — `modules/exporter.py`

> **What this file does:** Generates downloadable PDF reports using ReportLab's Platypus layout engine.

### ReportLab Concepts

```python
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, Spacer

# 1. Create a document with margins
doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.75*inch, ...)

# 2. Build a list of "flowables" (elements)
elements = [
    Paragraph("Title", title_style),
    Spacer(1, 10),
    Table(data, colWidths=[...]),
]

# 3. Render everything into PDF bytes
doc.build(elements)
```

### Why ReportLab (not WeasyPrint or Pandoc)?

- Zero system dependencies — installs with pip
- Works in any cloud environment
- Precise layout control
- No browser required (WeasyPrint needs Chrome-like rendering)

### The Table Style Pattern

```python
t = Table(data, colWidths=[...])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), PURPLE),   # header row purple
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
]))
```

`(col, row)` uses 0-indexing. `(-1, -1)` means last column, last row.

---

## 7. File 5 — `app.py`

> **What this file does:** The Streamlit frontend — 9 pages, custom CSS dark theme, interactive charts, and all UI logic.

### Page structure

```python
PAGES = {
    "🏠 Dashboard": "dashboard",
    "📄 New Analysis": "new_analysis",
    ...
}

# Session state tracks current page
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

# Router
page = st.session_state.page
if page == "dashboard": ...
elif page == "new_analysis": ...
```

No `st.Page` / multi-page file structure — everything is in one file with manual routing. This keeps the app self-contained and deployment-simple.

### The Analysis Pipeline in `new_analysis`

```python
# Step 1: Parse files
resume_text = parser.extract_text(resume_file)

# Steps 2-7: AI calls with progress bar
progress_bar = st.progress(0)
profile = agent.parse_profile(...)
progress_bar.progress(25)
gap_analysis = agent.analyze_skill_gap(...)
progress_bar.progress(42)
...

# Save to DB
profile_id = database.save_profile(...)
analysis_id = database.save_analysis(...)
```

The progress bar updates between each AI call. Each call takes 3-8 seconds, so visual feedback is critical for UX.

### The `_analysis_selector()` Helper

```python
def _analysis_selector() -> tuple[dict | None, dict | None]:
    analyses = database.get_analyses()
    options = {f"#{a['id']} — {role} ({date})": a["id"] for a in analyses}
    chosen_id = options[st.selectbox("Select Analysis", list(options.keys()))]
    return database.get_analysis(chosen_id), database.get_profile(...)
```

Every page except Dashboard and New Analysis starts by loading an existing analysis. This helper shows a dropdown and returns the selected analysis + profile.

### Plotly Chart Pattern

```python
fig = go.Figure(go.Scatterpolar(
    r=values,
    theta=categories,
    fill="toself",
    fillcolor="rgba(124,58,237,0.2)",
    line=dict(color="#7C3AED", width=2),
))
fig.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",   # transparent background
    paper_bgcolor="rgba(0,0,0,0)",  # transparent outer
    font_color="#E2E8F0",           # matches dark theme text
    height=360,
)
st.plotly_chart(fig, use_container_width=True)
```

All charts use `rgba(0,0,0,0)` backgrounds to blend with the dark CSS.

---

## 8. Prompt Engineering Deep Dive

Prompts are the most important part of the app. Here are the key techniques used.

### Technique 1: Role Assignment

```
"You are a senior talent acquisition specialist and career strategist."
```

This activates GPT-4o's domain knowledge and makes the output domain-appropriate rather than generic.

### Technique 2: Strict JSON-only Output

```
"Return ONLY valid JSON (no markdown, no extra text) with these exact keys:"
```

Without "ONLY", GPT-4o often adds helpful explanatory text before or after the JSON, which breaks parsing.

### Technique 3: Schema with Example Types

```json
{
  "readiness_score": 72,
  "grade": "B",
  "grade_label": "Strong Candidate",
  "score_breakdown": {
    "technical_skills": {"score": 70, "weight": 0.35, "weighted": 24.5}
  }
}
```

Providing an example schema (with real example values, not just type names) dramatically improves consistency.

### Technique 4: Constrained Enumerations

```
"Priority must be one of: critical, high, medium, low."
"Difficulty must be one of: easy, medium, hard."
```

Without these constraints, GPT-4o might use "urgent" or "moderate" — which breaks color-coding logic that checks for exact strings.

### Technique 5: Business Logic in the Prompt

```
"Grade scale: A (90-100, Ready Now), B (75-89, Almost Ready), 
C (60-74, Needs Work), D (45-59, Significant Gaps), F (<45, Major Rebuild)"
```

Encoding business rules directly in the prompt means no post-processing logic needed.

### Technique 6: Temperature Control

```python
response = client.chat.completions.create(
    model="gpt-4o",
    temperature=0.3,   # Lower = more consistent output
    ...
)
```

For structured JSON outputs, lower temperature (0.2–0.4) gives more reliable structure. For creative content (project suggestions), you could go up to 0.6–0.7.

---

## 9. Database Design

### Why SQLite?

- Zero setup — no server, no config, no credentials
- File-based — `data/skill_gap.db` travels with the project
- Handles multiple analyses, profiles, and progress tracking
- Perfect for single-user or small-team use

### The Three Tables in Detail

```sql
-- profiles: stores raw input + AI-parsed data
CREATE TABLE profiles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT NOT NULL,
    name        TEXT,
    target_role TEXT NOT NULL,
    industry    TEXT NOT NULL,
    resume_text TEXT,        -- original raw text
    linkedin_text TEXT,      -- original raw text
    parsed_data TEXT NOT NULL -- JSON: skills, experience, education
);

-- analyses: stores all AI outputs for one analysis run
CREATE TABLE analyses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at      TEXT NOT NULL,
    profile_id      INTEGER NOT NULL,
    readiness_score INTEGER NOT NULL,  -- denormalized for fast sorting
    skill_data      TEXT NOT NULL,     -- JSON
    gap_data        TEXT NOT NULL,     -- JSON
    roadmap_data    TEXT NOT NULL,     -- JSON
    courses_data    TEXT NOT NULL,     -- JSON
    interview_data  TEXT NOT NULL,     -- JSON
    FOREIGN KEY (profile_id) REFERENCES profiles(id)
);

-- progress: weekly task completion (one row per task)
CREATE TABLE progress (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT NOT NULL,
    analysis_id INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    task_label  TEXT NOT NULL,
    completed   INTEGER DEFAULT 0,  -- SQLite has no BOOLEAN; use 0/1
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);
```

### Why `readiness_score` Is Denormalized

The score is stored as a plain integer column (not buried in JSON) so we can:
- `ORDER BY readiness_score DESC` without parsing JSON
- `AVG(readiness_score)` for stats
- Filter `WHERE readiness_score >= 75` for "ready candidates"

---

## 10. UI/CSS System

All styling lives in a single `st.markdown("""<style>...</style>""")` block at the top of app.py.

### CSS Custom Properties (Variables)

The Streamlit theme sets base colors in `.streamlit/config.toml`:
```toml
primaryColor = "#7C3AED"      # purple
backgroundColor = "#0F0F1A"   # near-black
secondaryBackgroundColor = "#1A1A2E"
textColor = "#E2E8F0"
```

The custom CSS extends this with component-specific styles.

### The HTML Component Pattern

Streamlit's built-in components are limited. For rich UI elements, we use:

```python
st.markdown(f"""
<div class='gap-card critical'>
    <div style='font-weight:700;color:#E2E8F0;'>{skill}</div>
    <div style='font-size:0.78rem;color:#64748B;'>Priority: CRITICAL</div>
</div>
""", unsafe_allow_html=True)
```

`unsafe_allow_html=True` is required. The CSS classes are defined in the global style block.

### The Color System

```python
def _score_color(score: int) -> str:
    if score >= 90: return "#10B981"   # green — ready
    if score >= 75: return "#3B82F6"   # blue — almost ready
    if score >= 60: return "#F59E0B"   # yellow — needs work
    if score >= 45: return "#EF4444"   # red — significant gaps
    return "#DC2626"                   # dark red — major rebuild
```

This function is used everywhere scores appear — cards, badges, progress bars.

---

## 11. Extending the App

### Add a new AI feature

1. Add a new function in `agent.py` following the `_call_gpt` + `_safe_json` pattern
2. Add a new page key to `PAGES` dict in `app.py`
3. Add a new `elif page == "your_page":` block
4. Optionally add a new column to `analyses` table in `database.py`

### Add a new database field

1. Add the column to `CREATE TABLE` in `init_db()` with `DEFAULT NULL`
2. Add it to `save_analysis()` parameters
3. Add it to `get_analysis()` JSON deserialization

SQLite doesn't enforce schema on existing DBs — delete `data/skill_gap.db` to reset.

### Switch from SQLite to PostgreSQL

Replace `_connect()` in `database.py`:
```python
import psycopg2

def _connect():
    return psycopg2.connect(os.environ["DATABASE_URL"])
```

Change `?` placeholders to `%s`. Everything else stays the same.

### Add Anthropic Claude instead of OpenAI

In `agent.py`, replace `_call_gpt`:
```python
import anthropic

def _call_gpt(system: str, user: str, max_tokens: int = 3000) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text
```

---

## 12. Deployment Guide

### Streamlit Community Cloud (Free)

1. Push your code to GitHub (make sure `data/` and `.env` are in `.gitignore`)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo, set `app.py` as the main file
4. In Secrets, add: `OPENAI_API_KEY = "sk-..."`
5. Deploy — live URL in ~2 minutes

**Note:** Streamlit Cloud has an ephemeral filesystem — SQLite data won't persist between restarts. For persistent storage on Cloud, switch to a free PostgreSQL DB (Railway, Supabase, Neon).

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.headless=true"]
```

```bash
docker build -t skill-gap-agent .
docker run -p 8501:8501 -e OPENAI_API_KEY=sk-... skill-gap-agent
```

### Fly.io (Free tier)

```bash
fly launch
fly secrets set OPENAI_API_KEY=sk-...
fly deploy
```

Add a persistent volume for SQLite:
```toml
# fly.toml
[mounts]
  source = "skill_gap_data"
  destination = "/app/data"
```

---

## 13. Troubleshooting

### "OPENAI_API_KEY not found"
Set it in the sidebar input, `.env` file, or `.streamlit/secrets.toml`.

### "Could not parse PDF"
Some PDFs are image-based (scanned). Try converting to DOCX first, or copy-paste the text as a `.txt` file.

### "JSON decode error" from AI functions
Rare — happens when GPT-4o returns truncated output. Increase `max_tokens` in the relevant `_call_gpt` call.

### Streamlit "DuplicateWidgetID" error
Each widget needs a unique `key=` parameter. If you see this in loops, add `key=f"widget_{i}"`.

### SQLite "database is locked"
Happens when two browser tabs run the app simultaneously. The `check_same_thread=False` flag mitigates this, but for concurrent users, switch to PostgreSQL.

### Charts not showing in dark mode
All Plotly charts need:
```python
fig.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#E2E8F0",
)
```

---

*Built with ❤️ using Python, Streamlit, and OpenAI GPT-4o*
