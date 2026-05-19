# 🎯 AI Resume & Job Match Agent

An intelligent career assistant that parses resumes, matches them against job descriptions, checks ATS compatibility, generates cover letters, and prepares you for interviews — powered by OpenAI GPT-4o and Supabase.

**👉 STEP-BY-STEP TUTORIAL: [Tutorial.md](./Tutorial.md)**

---

## Overview

AI Resume & Job Match Agent is an open-source, production-ready Streamlit application that brings AI-powered career coaching to anyone. Instead of guessing how well your resume matches a job, you get a precise score, specific gap analysis, and actionable steps to improve — instantly.

Built on OpenAI GPT-4o with a modular Python architecture, **Supabase (PostgreSQL)** for persistent cloud storage, and a beautiful custom UI. Fully deployable on **Streamlit Community Cloud** — free.

---

## Features

- 📄 **Resume Upload & Parsing** — Upload PDF or DOCX; GPT-4o extracts skills, experience, education, and projects
- 🔍 **AI Job Matching** — Match score (0–100%), grade, strengths, missing skills, and recommendations
- 🤖 **ATS Checker** — Keyword analysis, formatting issues, section scores, and optimization tips
- ✉️ **Cover Letter Generator** — Tailored letters in your chosen tone; editable and exportable to PDF
- 💬 **Interview Prep** — Role-specific behavioral, technical, situational, and culture-fit questions with answer guidance
- 📊 **Analytics Dashboard** — Score history charts, distribution plots, and match vs. ATS scatter plots
- 📁 **History** — All past analyses saved permanently in Supabase with one-click PDF export
- ☁️ **Cloud-ready** — Works perfectly on Streamlit Community Cloud with zero file system issues

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Core language |
| Streamlit | Web UI framework |
| OpenAI GPT-4o | AI reasoning (parsing, matching, generation) |
| **Supabase** | **Persistent PostgreSQL database** |
| Plotly | Interactive charts |
| ReportLab | PDF export |
| pypdf / pdfplumber | PDF text extraction |
| python-docx | DOCX text extraction |

---

## Project Structure

```
resume-job-agent/
├── app.py                      # Main Streamlit app (all pages)
├── modules/
│   ├── __init__.py
│   ├── agent.py                # All OpenAI GPT-4o API calls
│   ├── parser.py               # PDF & DOCX text extraction
│   ├── database.py             # Supabase CRUD operations
│   └── exporter.py             # PDF report generation
├── supabase_schema.sql         # ← Run this once in Supabase SQL Editor
├── sample_data/
│   ├── sample_resume.txt
│   └── sample_job_description.txt
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example   # ← Template for your secrets
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── Tutorial.md
```

---

## Getting Started

### Step 1 — Clone the repo

```bash
git clone https://github.com/your-username/resume-job-agent.git
cd resume-job-agent
```

### Step 2 — Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate       # macOS/Linux
venv\Scripts\activate          # Windows
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Create a Supabase project (free)

1. Go to [supabase.com](https://supabase.com) → **New Project** (free tier)
2. Wait ~2 minutes for provisioning
3. Go to **SQL Editor** → **New Query**
4. Paste the entire contents of `supabase_schema.sql` and click **Run ▶**
5. Go to **Project Settings → API**
6. Copy your **Project URL** and **anon public key**

### Step 5 — Set credentials

```bash
cp .env.example .env
```

Edit `.env`:
```
OPENAI_API_KEY=sk-your-openai-key-here
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key-here
```

### Step 6 — Run the app

```bash
streamlit run app.py
```

Open `http://localhost:8501` 🎉

---

## Deploy to Streamlit Cloud (Free)

### Step 1 — Push to GitHub

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

> ⚠️ Never commit `.env`. Your `.gitignore` already excludes it.

### Step 2 — Create app on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
2. Select your GitHub repo
3. Set **Main file path**: `app.py`

### Step 3 — Add secrets

Click **Advanced settings → Secrets** and paste:

```toml
OPENAI_API_KEY  = "sk-your-openai-key-here"
SUPABASE_URL    = "https://your-project-id.supabase.co"
SUPABASE_KEY    = "your-supabase-anon-key-here"
```

### Step 4 — Deploy

Click **Deploy** — live in ~2 minutes with a permanent URL. ✅

All data (resumes, analyses, cover letters, interview questions) persists permanently in Supabase — no resets on sleep or redeploy.

---

## How the AI Works

```
Resume Upload
      ↓
parser.py — extracts raw text from PDF/DOCX
      ↓
agent.py → GPT-4o — parses structured JSON (skills, experience, etc.)
      ↓
User pastes job description
      ↓
agent.py → GPT-4o — computes match score, gaps, recommendations
agent.py → GPT-4o — runs ATS compatibility check
      ↓
database.py → Supabase — saves everything permanently
      ↓
app.py — renders results, charts, downloadable PDFs
```

---

## Common Errors & Fixes

| Error | Cause | Fix |
|---|---|---|
| `Supabase credentials missing` | No env vars set | Add keys to `.env` or Streamlit secrets |
| `openai.AuthenticationError` | Wrong OpenAI key | Check `OPENAI_API_KEY` in secrets |
| `relation "resumes" does not exist` | Schema not created | Run `supabase_schema.sql` in Supabase SQL Editor |
| `ModuleNotFoundError: supabase` | Not installed | `pip install -r requirements.txt` |
| PDF export fails | reportlab missing | `pip install reportlab` |
| `RateLimitError` | OpenAI quota | Add billing at platform.openai.com |

---

## Contributing

Pull requests welcome! Fork → feature branch → PR.

---

## License

MIT License — free to use, modify, and share.

---

*Built with ❤️ using Python, OpenAI GPT-4o, Supabase, and Streamlit*
