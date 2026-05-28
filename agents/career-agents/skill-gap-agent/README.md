# 🎯 AI Skill Gap Agent

> **Your personal AI-powered career intelligence platform.**
> Upload your resume, pick your target role, and get a complete gap analysis, 6-month roadmap, curated courses, project suggestions, and interview prep — all powered by GPT-4o.

**👉 STEP-BY-STEP TUTORIAL: [Tutorial.md](./Tutorial.md)**

---

## Overview

AI Skill Gap Agent is an open-source, production-ready Streamlit application that brings AI-powered career coaching to anyone. Instead of guessing what skills you need, you get a precise readiness score, specific gap analysis, and a week-by-week learning plan — instantly.

Built on OpenAI's GPT-4o with a modular Python architecture, SQLite storage, and a beautiful dark-mode UI.

<img width="1921" height="1621" alt="screencapture-skill-gap-agent-streamlit-app-2026-05-28-14_59_28" src="https://github.com/user-attachments/assets/4feb9c2f-dc80-4dea-bcfa-94d61bc5a29a" />

---

## Features

- 📄 **Resume & LinkedIn Parsing** — Upload PDF or DOCX; GPT-4o extracts skills, experience, education, and projects
- 🔍 **AI Skill Gap Analysis** — Matched skills, missing skills, priority gaps, and transferable skills
- 📊 **Career Readiness Score** — 0–100% score with grade (A–F) across 6 weighted dimensions
- 🗺️ **6-Month Learning Roadmap** — Month-by-month plan with themes, goals, milestones, and weekly schedules
- 📚 **Course Recommendations** — Platform-specific courses, certifications, books, and free resources per skill gap
- 🏗️ **Project Suggestions** — Portfolio projects with tech stack, difficulty, and "wow factor" for recruiters
- 💬 **Interview Preparation** — Technical questions, STAR behavioral questions, salary negotiation, and a 7-day prep plan
- 📈 **Progress Tracker** — Interactive weekly checklist with completion charts
- 📊 **Analytics Dashboard** — Readiness history, score distribution, and radar charts
- 📁 **History** — All past analyses saved in SQLite with one-click PDF export
- 🗃️ **SQLite Storage** — Zero-config local database; no external services needed
- 🎨 **Beautiful Dark UI** — Custom CSS with score badges, skill pills, radar charts, and gradient cards

---

## Screenshots

```
┌─────────────────────────────────────────────────────────────┐
│  🎯 AI Skill Gap Agent                                      │
│                                                             │
│  📄 Profiles  🔍 Analyses  📈 Avg Score  ✅ Ready           │
│     3             12          68%           4               │
│                                                             │
│  📈 Readiness Score History  │  🕐 Recent Analyses          │
│  [Line Chart with 75% line]  │  [Role cards with scores]   │
│                                                             │
│  📊 Score Distribution                                      │
│  [Histogram across all runs]                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Core language |
| Streamlit | Web UI framework |
| OpenAI GPT-4o | AI reasoning (parsing, gap analysis, roadmap, courses) |
| SQLite | Local data storage |
| Plotly | Interactive charts (radar, bar, histogram, line) |
| ReportLab | PDF report export |
| pypdf / pdfplumber | PDF text extraction |
| python-docx | DOCX text extraction |

---

## Project Structure

```
skill-gap-agent/
├── app.py                    # Main Streamlit app (all 9 pages)
├── modules/
│   ├── __init__.py
│   ├── agent.py              # All 7 GPT-4o API calls
│   ├── parser.py             # PDF & DOCX text extraction
│   ├── database.py           # SQLite CRUD operations
│   └── exporter.py           # PDF report generation
├── sample_data/
│   ├── sample_resume.txt     # Example resume for testing
│   └── sample_linkedin.txt   # Example LinkedIn text for testing
├── .streamlit/
│   ├── config.toml           # Dark theme & server config
│   └── secrets.toml.example  # Secrets template
├── data/                     # Auto-created; holds SQLite DB
├── exports/                  # Auto-created; holds exported PDFs
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── Tutorial.md
```

<img width="1834" height="995" alt="image" src="https://github.com/user-attachments/assets/515590cc-2df6-4976-b89a-2de8cfa0b3bb" />

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/adityasharmadotai-hash/amazing-ai-agents.git
cd skill-gap-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your OpenAI API key

**Option A — .env file:**
```bash
cp .env.example .env
# Edit .env and add: OPENAI_API_KEY=sk-...
```

**Option B — Streamlit secrets:**
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml and add: OPENAI_API_KEY = "sk-..."
```

**Option C — Sidebar input:**
Enter your key directly in the sidebar when the app is running.

### 4. Run the app

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## How to Use

```
📄 Upload Resume (PDF/DOCX) + paste LinkedIn text
      ↓
🎯 Enter your target role and industry
      ↓
🚀 Click "Run AI Analysis"
      ↓
📊 Get your Readiness Score (0-100%)
      ↓
🔍 Explore your Skill Map (matched vs. missing skills)
      ↓
🗺️ Follow your 6-Month Learning Roadmap
      ↓
📚 Browse curated Course Recommendations
      ↓
🏗️ Pick Portfolio Projects to build
      ↓
💬 Prepare with your Interview Plan
      ↓
📈 Track progress week by week
```

---

## Pages

| Page | What you get |
|------|-------------|
| 🏠 Dashboard | Score history, recent analyses, distribution charts |
| 📄 New Analysis | Upload + run the full AI pipeline |
| 📊 Skill Map | Radar chart, matched/missing skills, gap priorities |
| 🗺️ Learning Roadmap | 6-month monthly plan, weekly schedule, checkpoints |
| 📚 Courses | Curated resources per skill gap, certifications, books |
| 🏗️ Projects | Portfolio projects with tech stack and wow factor |
| 💬 Interview Prep | Technical Qs, STAR behavioral, salary tips, 7-day plan |
| 📈 Progress Tracker | Weekly checklist with completion progress |
| 📁 History | All past analyses with load and PDF export |

---

## AI Functions (agent.py)

| Function | Input | Output |
|----------|-------|--------|
| `parse_profile()` | Resume + LinkedIn text | Structured candidate dict |
| `analyze_skill_gap()` | Profile + target role | Matched, missing, transferable skills |
| `calculate_readiness()` | Gap analysis + profile | Score, grade, breakdown, timeline |
| `generate_roadmap()` | Gap + readiness data | 6-month monthly plan + weekly schedule |
| `recommend_courses()` | Missing skills list | Courses, certs, books per skill |
| `generate_interview_prep()` | Profile + gaps | Technical Qs, STAR Qs, salary tips |
| `suggest_portfolio_projects()` | Profile + gaps | Projects with tech stack and difficulty |

---

## License

MIT — free to use, modify, and deploy.
