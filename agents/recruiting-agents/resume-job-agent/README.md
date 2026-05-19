# 🎯 AI Resume & Job Match Agent

> An AI-powered career assistant that parses your resume, scores job matches, optimizes for ATS, writes cover letters, and preps you for interviews — all in one Streamlit app.

---

> ⭐ **Star the repo:** [github.com/adityasharmadotai-hash](https://github.com/adityasharmadotai-hash)
> 💼 **Follow on LinkedIn:** [linkedin.com/in/aditya-hicounselor](https://www.linkedin.com/in/aditya-hicounselor/)
> 📺 **Subscribe on YouTube:** [YouTube Channel](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)
> 🚀 **AI Jobs in the USA:** [Apply Now](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)

---

**👉 STEP-BY-STEP TUTORIAL: [Tutorial.md](./Tutorial.md)**

---

## Overview

Job hunting is broken. You spend hours tailoring your resume for each role, not knowing if it even passes the ATS filter or if your skills actually match what the employer wants.

**AI Resume & Job Match Agent** solves this. Upload your resume once — PDF or DOCX — and instantly get:

- A precise **match score** against any job description
- Exact **missing skills** you need to fill the gap
- An **ATS compatibility score** with keyword-level analysis
- A fully written, tailored **cover letter** in seconds
- **Interview questions** specific to your background and the role

Built on **OpenAI GPT-4o** with a modular Python architecture, **Supabase (PostgreSQL)** for persistent cloud storage, and a polished custom UI. Fully deployable on **Streamlit Community Cloud — free**.

---

## Features

| Feature | What It Does |
|---------|-------------|
| 📄 **Resume Upload & Parsing** | Upload PDF or DOCX — GPT-4o extracts skills, experience, education, projects |
| 🔍 **AI Job Matching** | Match score 0–100%, letter grade, strengths, missing skills, radar chart |
| 🤖 **ATS Checker** | Keyword gap analysis, formatting issues, section-by-section scores |
| ✉️ **Cover Letter Generator** | Tailored letters in your chosen tone, editable, exportable to PDF |
| 💬 **Interview Prep** | Behavioral, technical, situational & culture-fit Q&A with answer guidance |
| 📊 **Analytics Dashboard** | Score history charts, distribution plots, match vs. ATS scatter |
| 📁 **History** | All analyses saved permanently in Supabase with one-click PDF export |
| ☁️ **Cloud-Ready** | Zero filesystem issues on Streamlit Community Cloud |

---

## How It Works

```
┌──────────────────────────────────────────────────────────────┐
│                    APPLICATION FLOW                          │
│                                                              │
│  1. Upload Resume (.pdf or .docx)                           │
│            ↓                                                 │
│     parser.py — extracts raw text                           │
│            ↓                                                 │
│     agent.py → GPT-4o — parses structured JSON             │
│     (name, skills, experience, education, projects)         │
│            ↓                                                 │
│     database.py → Supabase — saves resume permanently       │
│                                                              │
│  2. Paste Job Description                                   │
│            ↓                                                 │
│     agent.py → GPT-4o — computes match score & gaps        │
│     agent.py → GPT-4o — runs ATS compatibility check       │
│            ↓                                                 │
│     database.py → Supabase — saves analysis permanently     │
│            ↓                                                 │
│     app.py — renders score, radar chart, pill tags          │
│                                                              │
│  3. Generate Assets                                         │
│     agent.py → GPT-4o — writes cover letter                │
│     agent.py → GPT-4o — generates interview questions      │
│     exporter.py → ReportLab — exports PDFs                 │
└──────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Core language |
| Streamlit | Web UI framework |
| OpenAI GPT-4o | AI reasoning — parsing, matching, generation |
| Supabase | Persistent PostgreSQL cloud database |
| Plotly | Interactive charts (radar, histogram, scatter) |
| ReportLab | PDF cover letter & analysis export |
| pypdf / pdfplumber | PDF text extraction |
| python-docx | DOCX text extraction |

---

## Project Structure

```
resume-job-agent/
├── app.py                     # Main Streamlit app — 8 pages, routing, CSS
├── modules/
│   ├── __init__.py
│   ├── agent.py               # All 6 GPT-4o API functions
│   ├── parser.py              # PDF & DOCX text extraction
│   ├── database.py            # Supabase CRUD — all tables
│   └── exporter.py            # ReportLab PDF generation
├── supabase_schema.sql        # ← Run once in Supabase SQL Editor
├── sample_data/
│   ├── sample_resume.txt      # Test resume to try the app
│   └── sample_job_description.txt
├── .streamlit/
│   ├── config.toml            # Streamlit theme & server settings
│   └── secrets.toml.example  # Template — copy and fill in your keys
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── Tutorial.md
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/adityasharmadotai-hash/amazing-ai-agents.git
cd amazing-ai-agents/agents/recruiting-agents/resume-job-agent
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate      # macOS / Linux
venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create a free Supabase project

1. Go to [supabase.com](https://supabase.com) → **New Project** (free tier)
2. Wait ~2 minutes for provisioning
3. Go to **SQL Editor → New Query**
4. Paste the entire `supabase_schema.sql` file and click **Run ▶**
5. Go to **Project Settings → API** — copy your **Project URL** and **anon public key**

### 5. Set your credentials

```bash
cp .env.example .env
```

Edit `.env`:
```
OPENAI_API_KEY=sk-your-openai-key-here
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key-here
```

Get your OpenAI key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

### 6. Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) 🎉

---

## Deploy to Streamlit Cloud (Free)

### Step 1 — Push to GitHub

```bash
git add .
git commit -m "Add resume job agent"
git push origin main
```

> ⚠️ Never commit `.env`. Your `.gitignore` already excludes it.

### Step 2 — Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
2. Select your GitHub repo
3. Set **Main file path**: `agents/recruiting-agents/resume-job-agent/app.py`
4. Click **Advanced settings → Secrets** and paste:

```toml
OPENAI_API_KEY = "sk-your-openai-key-here"
SUPABASE_URL   = "https://your-project-id.supabase.co"
SUPABASE_KEY   = "your-supabase-anon-key-here"
```

5. Click **Deploy** — live in ~2 minutes ✅

All data persists permanently in Supabase — no resets on sleep or redeploy.

---

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `relation "resumes" does not exist` | Schema not created | Run `supabase_schema.sql` in Supabase SQL Editor |
| `postgrest.exceptions.APIError` | Missing table permissions | Run the GRANT statements in `supabase_schema.sql` |
| `Invalid format: please enter valid TOML` | Wrong secrets format | Use `KEY = "value"` with quotes, not `KEY=value` |
| `openai.AuthenticationError` | Wrong OpenAI key | Check `OPENAI_API_KEY` in Streamlit secrets |
| `Supabase credentials missing` | Secrets not set | Add all 3 keys to Streamlit Cloud → App → Secrets |
| `ModuleNotFoundError` | Packages not installed | `pip install -r requirements.txt` |
| PDF export fails | reportlab missing | Already in requirements.txt — redeploy |
| `RateLimitError` | OpenAI quota exceeded | Add billing at [platform.openai.com](https://platform.openai.com) |

---

## Contributing

Pull requests are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## License

MIT License — free to use, modify, and share.

---

## ⭐ If you found this useful...

If this project helped you, it would mean a lot if you could:

- ⭐ **[Star the repository](https://github.com/adityasharmadotai-hash)** — helps others discover this project
- 💼 **[Follow on LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)** — daily AI news, tools, and updates
- 📺 **[Subscribe on YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)** — AI agents, tutorials, and the latest in AI
- 🚀 **[AI Jobs in the USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)** — apply now

---

*Built with ❤️ using Python, OpenAI GPT-4o, Supabase, and Streamlit*
