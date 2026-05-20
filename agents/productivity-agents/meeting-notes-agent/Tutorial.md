# 🎙️ Build an AI Meeting Notes Agent from Scratch

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

> **What you'll build:** A Streamlit app that transcribes meeting recordings using OpenAI Whisper, analyzes them with GPT-4o to extract action items, decisions, and summaries, then exports professional reports as PDF, DOCX, or Markdown.

---

## 📋 Table of Contents

1. [What Are We Building?](#1-what-are-we-building)
2. [How It Works](#2-how-it-works)
3. [Prerequisites](#3-prerequisites)
4. [Project Setup](#4-project-setup)
5. [File 1 — transcriber.py](#5-file-1--transcriberpy)
6. [File 2 — agent.py](#6-file-2--agentpy)
7. [File 3 — database.py](#7-file-3--databasepy)
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

Meeting notes are a massive pain point:
- Someone has to take notes during the call (and miss the conversation)
- Action items get lost in Slack
- No one remembers what was actually decided
- Writing the follow-up email takes 20 minutes

This agent solves all of it:

```
Upload recording (MP3/WAV/MP4)
      ↓
🎙️ Whisper AI: "Let's talk about the Q4 budget..."
      ↓
📝 Summary: "Team discussed Q4 budget allocation..."
✅ Action Items: "Alice to prepare budget proposal by Friday"
⚖️ Decisions: "Approved $50K for marketing campaign"
👤 Tasks by Person: "Alice: [2 tasks], Bob: [1 task]"
✉️ Email Draft: "Hi team, following up on today's call..."
📥 Export: PDF / DOCX / Markdown
```

---

## 2. How It Works

```
┌──────────────────────────────────────────────────────────────────┐
│                         AGENT FLOW                               │
│                                                                  │
│  USER UPLOADS audio/video file                                   │
│           ↓                                                       │
│    transcriber.py                                                │
│    Write to temp file → OpenAI Whisper API                      │
│    Returns: text, segments with timestamps, language            │
│           ↓                                                       │
│    agent.py → OpenAI GPT-4o                                     │
│    One large prompt → structured JSON analysis                  │
│    {summary, action_items, decisions, tasks_by_person, ...}     │
│           ↓                                                       │
│    agent.py → GPT-4o (second call)                              │
│    Generate follow-up email from analysis                       │
│           ↓                                                       │
│    database.py → Supabase                                       │
│    Save permanently (optional)                                  │
│           ↓                                                       │
│    exporter.py                                                   │
│    PDF via ReportLab / DOCX via python-docx / Markdown          │
│           ↓                                                       │
│    app.py                                                        │
│    7-page Streamlit UI: upload, analysis, email, search, charts │
└──────────────────────────────────────────────────────────────────┘
```

**Four modules, each with one responsibility:**

| File | Job |
|------|-----|
| `transcriber.py` | Audio file → text + timestamps via Whisper |
| `agent.py` | Text → structured analysis + email via GPT-4o |
| `database.py` | Supabase CRUD + analytics queries |
| `exporter.py` | Analysis → PDF / DOCX / Markdown |

---

## 3. Prerequisites

### ✅ Required

- [ ] Python 3.10+ — [python.org/downloads](https://python.org/downloads)
- [ ] OpenAI API key — [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- [ ] GitHub account — [github.com](https://github.com)
- [ ] Streamlit account — [share.streamlit.io](https://share.streamlit.io) (free)

### 🔶 Optional

- [ ] Supabase account — [supabase.com](https://supabase.com) (free — for history/search/analytics)

### 💰 Cost Estimate

- Whisper transcription: ~$0.006/minute of audio
- GPT-4o analysis: ~$0.02–0.05 per meeting
- **60-minute meeting: ~$0.40–0.55 total**

---

## 4. Project Setup

```bash
mkdir meeting-notes-agent
cd meeting-notes-agent
mkdir modules .streamlit

python3 -m venv venv
source venv/bin/activate

pip install streamlit openai supabase reportlab python-docx plotly python-dotenv

cp .env.example .env
# Edit .env with your OPENAI_API_KEY
```

---

## 5. File 1 — `transcriber.py`

> **What this file does:** Takes an uploaded audio/video file, writes it to a temp file (required by the Whisper API), calls OpenAI's Whisper model, and returns structured transcript data including timestamped segments.

### Why a temp file?

The Whisper API requires a `file` object with a `.name` attribute to detect the format. Streamlit's uploaded files are in-memory bytes — we write them to a temp file so the API knows the extension (`.mp3`, `.mp4`, etc.).

```python
with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
    tmp.write(file_bytes)
    tmp_path = tmp.name

with open(tmp_path, "rb") as audio_file:
    response = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="verbose_json",        # ← gives us segments + timestamps
        timestamp_granularities=["segment"],   # ← per-sentence timestamps
    )
```

`verbose_json` returns a `FetchedTranscript` object with:
- `response.text` — full transcript string
- `response.segments` — list of timestamped chunks
- `response.language` — detected language
- `response.duration` — total audio length in seconds

### The 25 MB Limit

Whisper API has a hard 25 MB file size limit. We check this before uploading:

```python
size_mb = len(file_bytes) / (1024 * 1024)
if size_mb > 25:
    return {"error": f"File too large ({size_mb:.1f} MB)..."}
```

**Tip:** For larger files, compress MP4 to MP3 first (FFmpeg: `ffmpeg -i meeting.mp4 -q:a 0 meeting.mp3`).

---

## 6. File 2 — `agent.py`

> **What this file does:** Two GPT-4o calls — one for full meeting analysis (returns JSON), one for the follow-up email (returns text).

### The Analysis Prompt — One Big Call

Rather than making 5 separate API calls (summary, actions, decisions, etc.), we do it all in one structured JSON prompt. This is 5x cheaper and 5x faster:

```python
def analyze_meeting(transcript, meeting_title, attendees) -> dict:
    system = "You are an expert meeting analyst..."

    user = f"""Analyze this transcript. Return this exact JSON:
{{
  "title": "...",
  "summary": "...",
  "action_items": [{{"task": "...", "owner": "...", "deadline": "...", "priority": "..."}}],
  "decisions": [{{"decision": "...", "context": "...", "owner": "..."}}],
  "tasks_by_person": {{"Alice": ["task1"], "Bob": ["task2"]}},
  "sentiment": "Positive / Neutral / Mixed / Tense",
  ...
}}

TRANSCRIPT:
{transcript}"""

    raw = _call_gpt(system, user, max_tokens=3000)
    return json.loads(raw)
```

**Why include example values in the JSON schema?**
GPT-4o uses few-shot patterns. Showing `"priority": "High / Medium / Low"` tells it exactly what values are valid — no post-processing or validation needed.

### Transcript Truncation

Long meetings can exceed GPT-4o's context limit. `_truncate()` keeps the beginning and end (most information-dense parts):

```python
def _truncate(transcript, max_chars=14000):
    if len(transcript) <= max_chars:
        return transcript
    half = max_chars // 2
    return transcript[:half] + "\n\n[...middle omitted...]\n\n" + transcript[-half:]
```

---

## 7. File 3 — `database.py`

> **What this file does:** All Supabase operations — save meetings, fetch history, search by title, analytics queries. Returns safe defaults if Supabase isn't configured.

### The Graceful Fallback

```python
def _db():
    url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        return None   # ← app keeps working without DB
    return create_client(url, key)
```

### Storing the Analysis as JSONB

The analysis is a nested dict with variable structure. We store it as Supabase's JSONB type:

```python
db.table("meetings").insert({
    "title": title,
    "analysis": analysis,    # ← Python dict → PostgreSQL JSONB
    ...
}).execute()
```

On retrieval it comes back as a Python dict — no `json.loads()` needed.

### Analytics Query

```python
def get_analytics() -> dict:
    resp = db.table("meetings").select(
        "id, duration_secs, word_count, attendee_count, sentiment, created_at"
    ).execute()
    rows = resp.data or []

    # Compute in Python — no complex SQL needed at this scale
    sentiment_counts = {}
    for r in rows:
        s = r.get("sentiment", "Neutral")
        sentiment_counts[s] = sentiment_counts.get(s, 0) + 1

    return {"sentiment_counts": sentiment_counts, ...}
```

---

## 8. File 4 — `exporter.py`

> **What this file does:** Converts the analysis dict into three export formats. Each function returns `bytes` which Streamlit's `st.download_button` accepts directly.

### PDF with ReportLab

ReportLab uses a "story" — a list of flowable elements rendered top-to-bottom:

```python
story = []
story.append(Paragraph(title, title_style))
story.append(HRFlowable(width="100%", thickness=2, color=INDIGO))
story.append(Paragraph(summary, body_style))
# Add action items as a Table
table = Table(data, colWidths=[...])
table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), INDIGO), ...]))
story.append(table)
doc.build(story)
```

### DOCX with python-docx

```python
doc = Document()
doc.add_heading(title, 0)
doc.add_paragraph(summary)
# Action items as a Word table
table = doc.add_table(rows=1, cols=5)
table.style = "Table Grid"
```

### Markdown

The simplest export — just Python f-strings with `|` table syntax:

```python
md = f"# {title}\n\n## Action Items\n\n"
md += "| Task | Owner | Deadline | Priority |\n"
md += "|------|-------|----------|----------|\n"
for ai in action_items:
    md += f"| {ai['task']} | {ai['owner']} | {ai['deadline']} | {ai['priority']} |\n"
```

---

## 9. File 5 — `app.py`

> **What this file does:** 7-page Streamlit UI with sidebar navigation using `st.button()` for reliable cross-version rendering.

### The 7 Pages

| Page | What It Does |
|------|-------------|
| 🏠 Home | Overview, quick stats, how-it-works |
| 🎙️ Upload & Transcribe | File upload, Whisper transcription, transcript viewer |
| 📋 Meeting Analysis | 6-tab analysis: summary, actions, decisions, by person, risks, Q&A, export |
| ✉️ Follow-up Email | Editable email draft + download |
| 🔍 Search Meetings | Search past meetings by title |
| 📊 Analytics | Sentiment pie, duration bars, activity timeline |
| 📁 History | All saved meetings with load/export/delete |

### Session State Flow

```python
# Set after transcription
st.session_state.transcript_data = {
    "text": "...",           # full transcript
    "segments": [...],       # timestamped chunks
    "duration_seconds": 3420,
    "word_count": 4521,
    ...
}

# Set after analysis
st.session_state.analysis = {
    "title": "Q4 Planning",
    "summary": "...",
    "action_items": [...],
    "decisions": [...],
    ...
}

# Set after email generation
st.session_state.follow_up_email = "Subject: ..."
```

### The Analysis + Email Pattern

After GPT-4o analysis, we immediately generate the follow-up email and save to DB — all in one user interaction:

```python
if st.button("🧠 Analyze with GPT-4o"):
    analysis = analyze_meeting(transcript, title, "")
    email = generate_follow_up_email(analysis, transcript)  # ← auto-generate
    if db_ok():
        save_meeting(title, filename, transcript, analysis, email, ...)  # ← auto-save
    st.session_state.analysis = analysis
    st.session_state.follow_up_email = email
```

---

## 10. Supabase Setup

### Step 1 — Create free project
[supabase.com](https://supabase.com) → New Project → wait ~2 minutes

### Step 2 — Run schema
SQL Editor → New Query → paste `supabase_schema.sql` → Run ▶

```sql
CREATE TABLE IF NOT EXISTS meetings (
    id              BIGSERIAL PRIMARY KEY,
    title           TEXT NOT NULL,
    transcript      TEXT,
    analysis        JSONB,
    follow_up_email TEXT,
    duration_secs   REAL,
    word_count      INTEGER,
    sentiment       TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

GRANT ALL ON meetings TO anon, authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
ALTER TABLE meetings DISABLE ROW LEVEL SECURITY;
```

### Step 3 — Get credentials
Project Settings → API → copy Project URL + anon public key

---

## 11. Running Locally

```bash
source venv/bin/activate
streamlit run app.py
```

### First Run Walkthrough

1. **🎙️ Upload & Transcribe** — Upload any MP3/WAV/MP4 (try a recorded meeting or voice note)
2. Wait for Whisper to transcribe (~30 sec for a 10-minute recording)
3. Review the transcript and timestamped segments
4. **📋 Meeting Analysis** — Click "Analyze with GPT-4o"
5. Wait ~15-30 seconds
6. Review all 6 tabs: summary, action items, decisions, tasks by person, risks, Q&A
7. **✉️ Follow-up Email** — Review and edit the auto-drafted email
8. **📋 Export tab** — Download PDF, DOCX, or Markdown

---

## 12. Deploying to Streamlit Cloud

```bash
git add .
git commit -m "AI Meeting Notes Agent"
git push origin main
```

1. [share.streamlit.io](https://share.streamlit.io) → New app
2. Select repo, main file: `app.py`
3. Advanced → Secrets:

```toml
OPENAI_API_KEY = "sk-your-key"
SUPABASE_URL   = "https://xxx.supabase.co"
SUPABASE_KEY   = "your-anon-key"
```

4. Deploy ✅

---

## 13. Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `audio_too_short` | File < 1 second | Use a longer recording |
| `Invalid API key` | Wrong OpenAI key | Check `OPENAI_API_KEY` |
| `File too large` | > 25 MB | Compress: `ffmpeg -i file.mp4 file.mp3` |
| `invalid_file_format` | Corrupted audio | Re-export from source |
| `relation does not exist` | No Supabase schema | Run `supabase_schema.sql` |
| `Invalid format: TOML` | Wrong secrets format | Use `KEY = "value"` with quotes |
| Analysis returns empty | Transcript too short | Needs at least a few sentences |
| PDF export fails | reportlab missing | Already in requirements.txt |

---

## 14. What You Learned

- ✅ **OpenAI Whisper API** — speech-to-text with timestamps, language detection
- ✅ **Temp file handling** — why APIs need file objects, not bytes
- ✅ **Structured JSON prompts** — one GPT-4o call for multiple outputs
- ✅ **Transcript truncation** — keeping start/end for long context
- ✅ **Supabase JSONB** — storing nested dicts natively in PostgreSQL
- ✅ **ReportLab PDFs** — Tables, styles, page breaks, multi-page documents
- ✅ **python-docx** — programmatic Word documents with tables and formatting
- ✅ **Markdown export** — simple, universal, works with Notion/Obsidian/GitHub
- ✅ **Plotly in Streamlit** — pie charts, bar charts, line charts
- ✅ **Streamlit session state** — multi-step workflow across 7 pages

---

## 15. What's Next

### Easy
- **Speaker diarization** — identify who said what (requires Whisper large + pyannote)
- **More languages** — Whisper auto-detects; just change GPT-4o analysis language
- **Custom templates** — let users define their own action item format

### Intermediate
- **Real-time transcription** — stream audio using Whisper's streaming mode
- **Calendar integration** — auto-create calendar events from action items
- **Slack integration** — post action items directly to a Slack channel

### Advanced
- **Meeting comparison** — track how action items from last meeting were completed
- **Sentiment trend alerts** — notify if team meetings become consistently negative
- **Auto-scheduling** — integrate with Google Calendar to suggest follow-up meeting times

---

## ⭐ Enjoyed this tutorial?

- ⭐ **[Star the repository](https://github.com/adityasharmadotai-hash)**
- 🌐 **[Visit adityasharma.ai](https://www.adityasharma.ai)** — AI training for professionals
- 💼 **[Follow on LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)**
- 📺 **[Subscribe on YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)**
- 🚀 **[AI Jobs in the USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

---

*Built with ❤️ by [Aditya Sharma](https://www.adityasharma.ai) · OpenAI Whisper + GPT-4o + Streamlit*
