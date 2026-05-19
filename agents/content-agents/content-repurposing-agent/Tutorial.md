# 🎬 Build an AI Content Repurposing Agent from Scratch

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

> **What you'll build:** A Streamlit app that takes any YouTube URL and generates 6 platform-ready content formats in 4 writing styles — powered by OpenAI GPT-4o, with a persistent history database and analytics dashboard.

---

## 📋 Table of Contents

1. [What Are We Building?](#1-what-are-we-building)
2. [How It Works](#2-how-it-works)
3. [Prerequisites](#3-prerequisites)
4. [Project Setup](#4-project-setup)
5. [File 1 — transcript.py](#5-file-1--transcriptpy)
6. [File 2 — prompts.py](#6-file-2--promptspy)
7. [File 3 — agent.py](#7-file-3--agentpy)
8. [File 4 — database.py](#8-file-4--databasepy)
9. [File 5 — app.py](#9-file-5--apppy)
10. [Supabase Setup](#10-supabase-setup)
11. [Running Locally](#11-running-locally)
12. [Deploying to Streamlit Cloud](#12-deploying-to-streamlit-cloud)
13. [Common Errors & Fixes](#13-common-errors--fixes)
14. [What You Learned](#14-what-you-learned)
15. [What's Next](#15-whats-next)

---

## 1. What Are We Building?

Content creators spend hours turning one video into posts for every platform. This agent does it in seconds.

```
One YouTube video
      ↓
💼 LinkedIn post (professional, engagement-optimised)
🐦 Twitter/X thread (viral, 8-12 tweets)
📸 Instagram caption (hook + hashtags)
🎣 10 viral hooks (scroll-stopping openers)
🎠 10-slide carousel (one insight per slide)
📝 Blog summary (SEO structure, 400-600 words)
```

And you can do all of that in **4 different writing styles** — Viral, Educational, Founder, Technical — giving you 24 total variations from a single video.

**Why this matters:**
- Content creators spend 3-4 hours repurposing one video manually
- This agent does it in under 60 seconds
- Quality is genuinely high because of careful prompt engineering

---

## 2. How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                         AGENT FLOW                              │
│                                                                 │
│  USER PASTES YouTube URL                                        │
│           ↓                                                      │
│    transcript.py                                                │
│    youtube-transcript-api fetches captions (no API key!)        │
│    returns: full text, segments with timestamps, word count     │
│           ↓                                                      │
│  USER PICKS a writing style                                     │
│    Viral / Educational / Founder / Technical                    │
│           ↓                                                      │
│    prompts.py                                                   │
│    builds system prompt + user prompt from templates            │
│    injects: style instruction + transcript text                 │
│           ↓                                                      │
│    agent.py → OpenAI GPT-4o                                    │
│    returns: generated content text                              │
│           ↓                                                      │
│    database.py → Supabase                                       │
│    saves: video_id, style, content_type, generated_text        │
│           ↓                                                      │
│    app.py                                                       │
│    displays content, download button, history                  │
└─────────────────────────────────────────────────────────────────┘
```

**Four files, each with one job:**

| File | Job |
|------|-----|
| `transcript.py` | YouTube URL → raw transcript text |
| `prompts.py` | Template library for all content types + styles |
| `agent.py` | OpenAI GPT-4o API calls |
| `database.py` | Supabase read/write + analytics |

---

## 3. Prerequisites

### ✅ Required

- [ ] Python 3.10+ — [python.org/downloads](https://python.org/downloads)
- [ ] OpenAI API key — [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- [ ] GitHub account — [github.com](https://github.com)
- [ ] Streamlit account — [share.streamlit.io](https://share.streamlit.io) (free)

### 🔶 Optional (for History + Analytics)

- [ ] Supabase account — [supabase.com](https://supabase.com) (free tier)

### 💰 API Cost Estimate

Using `gpt-4o`:
- Per content type generated: ~$0.01–0.02
- Generating all 6 content types: ~$0.08–0.12
- Very affordable for regular use

---

## 4. Project Setup

### Step 1 — Create folders

```bash
mkdir content-repurposing-agent
cd content-repurposing-agent
mkdir modules .streamlit
```

### Step 2 — Virtual environment

```bash
python3 -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows
```

### Step 3 — Install packages

```bash
pip install streamlit openai youtube-transcript-api supabase plotly python-dotenv
```

### Step 4 — Set your API key

```bash
cp .env.example .env
# Edit .env:
# OPENAI_API_KEY=sk-your-key-here
```

---

## 5. File 1 — `transcript.py`

> **What this file does:** Takes a YouTube URL in any format, extracts the video ID, fetches the English transcript using `youtube-transcript-api` (no YouTube API key needed), and returns structured data.

### Key Function: `get_transcript(url)`

```python
from youtube_transcript_api import YouTubeTranscriptApi

def get_transcript(url: str) -> dict:
    video_id = extract_video_id(url)

    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
    except NoTranscriptFound:
        # Try auto-generated captions
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript_obj = transcripts.find_generated_transcript(["en"])
        transcript_list = transcript_obj.fetch()

    full_text = " ".join(seg["text"] for seg in transcript_list)

    return {
        "video_id": video_id,
        "transcript": full_text,
        "segments": transcript_list,   # [{text, start, duration}]
        "word_count": len(full_text.split()),
        "duration_minutes": ...,
    }
```

**Why no YouTube API key?**
`youtube-transcript-api` fetches captions directly from YouTube's public caption endpoint — the same way the "CC" button works. No authentication required.

**The segments list** enables the timestamped Transcript Viewer:
```python
{"text": "So today we're going to talk about", "start": 12.4, "duration": 2.1}
```

**`chunk_transcript()`** trims very long transcripts to 12,000 chars (keeping start + end) to stay within GPT-4o's context window.

---

## 6. File 2 — `prompts.py`

> **What this file does:** The entire prompt library. Every content type has a system prompt + user prompt template. Every writing style has an instruction string injected into every prompt.

### Writing Styles — the Key to 24 Variations

```python
WRITING_STYLES = {
    "Viral": {
        "instruction": "Write in a VIRAL style: bold claims, emotional triggers,
                        power numbers, curiosity gaps, pattern interrupts..."
    },
    "Educational": {
        "instruction": "Write in an EDUCATIONAL style: clear structure, step-by-step,
                        practical examples, actionable takeaways..."
    },
    "Founder": {
        "instruction": "Write in a FOUNDER style: personal story, behind-the-scenes,
                        vulnerability + confidence, lessons learned..."
    },
    "Technical": {
        "instruction": "Write in a TECHNICAL style: precise terminology, deep insights,
                        implementation details, expert-level audience..."
    },
}
```

The `instruction` string is injected as `{style_instruction}` into every content prompt. Same template → 4 completely different tones.

### `build_prompt()` — The Assembly Function

```python
def build_prompt(content_type: str, transcript: str, style: str) -> dict:
    style_instruction = WRITING_STYLES[style]["instruction"]
    template = CONTENT_PROMPTS[content_type]

    return {
        "system": template["system"],
        "user": template["user"].format(
            style_instruction=style_instruction,
            transcript=transcript,
        ),
    }
```

---

## 7. File 3 — `agent.py`

> **What this file does:** Makes OpenAI GPT-4o API calls. One function per use case. Returns plain text or a safe error string.

### The Main Function

```python
from openai import OpenAI

def generate_content(content_type, transcript, style, max_tokens=2000) -> str:
    client = OpenAI(api_key=...)
    prompt = build_prompt(content_type, transcript, style)

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": prompt["system"]},
            {"role": "user",   "content": prompt["user"]},
        ],
    )
    return response.choices[0].message.content.strip()
```

**Why `gpt-4o`?**
It produces higher-quality, more nuanced content than smaller models — especially for creative writing like viral hooks and founder stories. For a content creation tool, quality justifies the cost.

**Error handling** — returns strings, not raises, so the UI can display them gracefully:

```python
except Exception as e:
    if "authentication" in str(e).lower():
        return "Error: Invalid API key."
    if "rate_limit" in str(e).lower():
        return "Error: Rate limit exceeded. Wait and retry."
    return f"Error: {str(e)}"
```

In `app.py`, we check `if result.startswith("Error:")` before displaying or saving.

---

## 8. File 4 — `database.py`

> **What this file does:** All Supabase operations. One table: `content_history`. Falls back gracefully if Supabase isn't configured — the app still works without history.

### The Graceful Fallback Pattern

```python
def _db():
    url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        return None      # ← None, not raise
    return create_client(url, key)

def save_content(...) -> int:
    db = _db()
    if not db:
        return -1        # ← caller handles safely
```

This means the app works even without Supabase — you just don't get history or analytics.

### The Schema — One Simple Table

```sql
CREATE TABLE content_history (
    id              BIGSERIAL PRIMARY KEY,
    video_id        TEXT,       -- YouTube video ID
    video_title     TEXT,       -- extracted by GPT-4o
    style           TEXT,       -- Viral / Educational / Founder / Technical
    content_type    TEXT,       -- linkedin_post / twitter_thread / etc.
    generated_text  TEXT,       -- the actual content
    char_count      INTEGER,    -- for analytics
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

One table handles all content types — they're all the same shape (text + metadata). One table makes analytics queries trivial.

---

## 9. File 5 — `app.py`

> **What this file does:** The entire Streamlit UI across 7 pages. Uses `st.button()` for navigation (not `st.radio()`) so sidebar styling works reliably on Streamlit Cloud.

### The 7 Pages

| Page | What It Shows |
|------|--------------|
| 🏠 Home | URL input, video info card after extraction |
| 📄 Transcript | Full text + timestamped segments viewer |
| ✨ Generate | Generate each content type individually or all at once |
| 📋 All Content | All generated content + export all as one .txt file |
| 📁 History | Past generations from Supabase with filter and delete |
| 📊 Analytics | Charts: by type, by style, daily activity, top videos |
| ⚙️ Prompts | View built-in prompts, create and test custom prompts |

### Why `st.button()` for Navigation (Not `st.radio()`)?

`st.radio()` relies on CSS selectors that changed between Streamlit versions. On Streamlit Cloud, the radio circles often show through and the label leaks. `st.button()` is a stable, reliable element:

```python
NAV_PAGES = [
    ("🏠", "Home"), ("📄", "Transcript"), ("✨", "Generate"),
    ("📋", "All Content"), ("📁", "History"), ("📊", "Analytics"), ("⚙️", "Prompts"),
]

for icon, label in NAV_PAGES:
    if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
        st.session_state.page = f"{icon} {label}"
        st.rerun()
```

The CSS targets `[data-testid="stSidebar"] .stButton > button` — a stable selector that works across Streamlit versions.

### Session State Variables

```python
st.session_state.transcript_data    # dict from get_transcript()
st.session_state.generated_content  # {content_type: text}
st.session_state.current_style      # "Educational" etc.
st.session_state.video_meta         # title, channel, description
st.session_state.custom_prompts     # user-created templates
```

---

## 10. Supabase Setup

### Step 1 — Create free project

1. [supabase.com](https://supabase.com) → **Sign up** → **New Project** (free)
2. Wait ~2 minutes

### Step 2 — Run the schema

Go to **SQL Editor → New Query**, paste `supabase_schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS content_history (
    id              BIGSERIAL PRIMARY KEY,
    video_id        TEXT NOT NULL,
    video_url       TEXT,
    video_title     TEXT,
    video_summary   TEXT,
    transcript      TEXT,
    duration_mins   REAL,
    word_count      INTEGER,
    style           TEXT,
    content_type    TEXT,
    generated_text  TEXT,
    char_count      INTEGER,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

GRANT ALL ON content_history TO anon, authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
ALTER TABLE content_history DISABLE ROW LEVEL SECURITY;
```

Click **Run ▶** — "Success. No rows returned." means it worked.

### Step 3 — Get credentials

**Project Settings → API:**
- **Project URL** → `SUPABASE_URL`
- **anon public** key → `SUPABASE_KEY`

---

## 11. Running Locally

```bash
source venv/bin/activate
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501)

### First Run Walkthrough

1. **🏠 Home** — Paste a YouTube URL (try a TED talk or tutorial with English captions)
2. Click **Extract ▶** — transcript loads in a few seconds
3. In the sidebar, pick a **Writing Style** — try Viral first
4. Go to **✨ Generate** — click **⚡ Generate ALL Content**
5. Watch 6 pieces generate with a progress bar (~30-60 seconds)
6. Go to **📋 All Content** — see everything, download all as one .txt file
7. Go to **📄 Transcript** — browse the timestamped segments
8. Go to **📊 Analytics** — see usage charts (requires Supabase)
9. Go to **⚙️ Prompts** — create a custom content type

---

## 12. Deploying to Streamlit Cloud

### Step 1 — Push to GitHub

```bash
git add .
git commit -m "AI Content Repurposing Agent"
git push origin main
```

### Step 2 — Streamlit Cloud

1. [share.streamlit.io](https://share.streamlit.io) → **New app**
2. Select your repo, set main file: `app.py`
3. **Advanced settings → Secrets** — paste in TOML format:

```toml
OPENAI_API_KEY = "sk-your-openai-key-here"
SUPABASE_URL   = "https://your-project-id.supabase.co"
SUPABASE_KEY   = "your-supabase-anon-key-here"
```

> ⚠️ **Common mistake:** Using `KEY=value` (dotenv format) instead of `KEY = "value"` (TOML). Streamlit Cloud requires TOML — values must have quotes and spaces around `=`.

4. Click **Deploy** — live in ~2 minutes ✅

---

## 13. Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `No English transcript available` | No English captions | Try a different video; look for CC badge |
| `Transcripts are disabled` | Creator disabled captions | Try a different video |
| `Invalid API key` | Wrong OpenAI key | Check `OPENAI_API_KEY` in secrets |
| `relation does not exist` | Supabase schema not created | Run `supabase_schema.sql` in SQL Editor |
| `postgrest.exceptions.APIError` | No table permissions | Re-run the GRANT statements in the schema |
| `Invalid format: TOML` | Using `KEY=value` not `KEY = "value"` | Add quotes and spaces |
| `RateLimitError` | OpenAI quota exceeded | Wait or add billing at platform.openai.com |
| Content is short or incomplete | Transcript was trimmed | Normal for very long videos — `chunk_transcript()` trims to 12k chars |

---

## 14. What You Learned

- ✅ **YouTube transcript extraction** — without any YouTube API key using `youtube-transcript-api`
- ✅ **Prompt engineering** — system vs user prompts, style injection, structured output control
- ✅ **Prompt management system** — template library with runtime variable injection
- ✅ **OpenAI GPT-4o API** — `client.chat.completions.create()` with system/user messages
- ✅ **Graceful degradation** — optional Supabase with fallback to in-memory state
- ✅ **Streamlit session state** — persisting data across page navigations and reruns
- ✅ **Sidebar navigation with `st.button()`** — reliable cross-version alternative to `st.radio()`
- ✅ **Custom CSS in Streamlit** — targeting `[data-testid="stSidebar"] .stButton > button`
- ✅ **Plotly analytics** — bar charts, pie charts, line charts in Streamlit
- ✅ **Supabase** — single-table schema, JSONB storage, permissions setup

---

## 15. What's Next

### Easy
- **More content types** — podcast show notes, YouTube description, email newsletter section
- **Multiple URLs at once** — batch process a whole playlist
- **Language support** — detect non-English transcripts and generate in that language

### Intermediate
- **Tone customisation sliders** — control formality, length, emoji usage with Streamlit sliders
- **Scheduled posting** — connect to Buffer or Hootsuite API to post directly
- **Image prompt generation** — generate Midjourney prompts for each carousel slide visual

### Advanced
- **Auto-post to LinkedIn** — use the LinkedIn API to publish directly from the app
- **Video topic clustering** — group your history by topic using OpenAI embeddings
- **A/B hook testing** — track which hooks perform best with UTM parameters

---

## ⭐ Enjoyed this tutorial?

- ⭐ **[Star the repository](https://github.com/adityasharmadotai-hash)** — helps others discover this project
- 🌐 **[Visit adityasharma.ai](https://www.adityasharma.ai)** — AI training & tools for professionals
- 💼 **[Follow on LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)** — daily AI news, tools, and updates
- 📺 **[Subscribe on YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)** — AI agents, tutorials, and the latest in AI
- 🚀 **[AI Jobs in the USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)** — apply now

---

*Built with ❤️ by [Aditya Sharma](https://www.adityasharma.ai) · Powered by OpenAI GPT-4o + Streamlit*
