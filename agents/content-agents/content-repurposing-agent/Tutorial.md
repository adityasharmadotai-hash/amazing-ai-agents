# 🎬 Build an AI Content Repurposing Agent from Scratch

### A Step-by-Step Tutorial for Beginners to Intermediate Developers

> ⭐ **Star the repo:** [github.com/adityasharmadotai-hash](https://github.com/adityasharmadotai-hash)
> 💼 **Follow on LinkedIn:** [linkedin.com/in/aditya-hicounselor](https://www.linkedin.com/in/aditya-hicounselor/)
> 📺 **Subscribe on YouTube:** [YouTube Channel](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)
> 🚀 **AI Jobs in the USA:** [Apply Now](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)

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

And you can do all of that in 4 different writing styles — Viral, Educational, Founder, Technical — for 24 total variations from a single video.

**Why this matters:**
- Content creators spend 3-4 hours repurposing one video manually
- This agent does it in under 60 seconds
- The quality is genuinely good because of careful prompt engineering

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
│    agent.py → OpenAI GPT-4o                            │
│    returns: generated content text                              │
│           ↓                                                      │
│    database.py → Supabase                                       │
│    saves: video_id, style, content_type, generated_text        │
│           ↓                                                      │
│    app.py                                                       │
│    displays content, copy button, download, history            │
└─────────────────────────────────────────────────────────────────┘
```

**Four files, each with one job:**

| File | Job |
|------|-----|
| `transcript.py` | YouTube URL → raw transcript text |
| `prompts.py` | Template library for all content types + styles |
| `agent.py` | Claude API calls |
| `database.py` | Supabase read/write + analytics |

---

## 3. Prerequisites

### ✅ Required

- [ ] Python 3.10+ — [python.org/downloads](https://python.org/downloads)
- [ ] OpenAI API key — [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- [ ] GitHub account — [github.com](https://github.com)
- [ ] Streamlit account — [share.streamlit.io](https://share.streamlit.io) (free)

### 🔶 Optional (for history + analytics)

- [ ] Supabase account — [supabase.com](https://supabase.com) (free)

### 💰 Cost estimate

- gpt-4o per content generation: ~$0.01-0.02
- Generating all 6 content types: ~$0.08-0.12
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
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```

### Step 3 — Install packages

```bash
pip install streamlit openai youtube-transcript-api supabase plotly python-dotenv
```

### Step 4 — API key

```bash
cp .env.example .env
# Edit .env and add: OPENAI_API_KEY=sk-ant-...
```

---

## 5. File 1 — `transcript.py`

> **What this file does:** Takes a YouTube URL in any format, extracts the video ID, fetches the English transcript using the `youtube-transcript-api` library (which works without a YouTube API key), and returns structured data.

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
        "segments": transcript_list,   # list of {text, start, duration}
        "word_count": len(full_text.split()),
        "duration_minutes": ...,
    }
```

**Why no YouTube API key?**
`youtube-transcript-api` fetches captions directly from YouTube's public caption endpoint — the same way the "CC" button on YouTube works. No authentication needed.

**The segments list** contains each caption chunk with its timestamp, which powers the Transcript Viewer's timestamped display:
```python
{"text": "So today we're going to talk about", "start": 12.4, "duration": 2.1}
```

**`chunk_transcript()`** — The transcript can be very long (10k+ words for a 1-hour video). Claude has a context limit. This function keeps the first and last portions of the transcript (most information-dense) and trims the middle:

```python
def chunk_transcript(transcript: str, max_chars: int = 12000) -> str:
    if len(transcript) <= max_chars:
        return transcript
    half = max_chars // 2
    return transcript[:half] + "\n\n[...trimmed...]\n\n" + transcript[-half:]
```

---

## 6. File 2 — `prompts.py`

> **What this file does:** The entire prompt library. Every content type has a system prompt and a user prompt template. Every writing style has an instruction string that gets injected into every prompt.

### Writing Styles

```python
WRITING_STYLES = {
    "Viral": {
        "icon": "🔥",
        "instruction": "Write in a VIRAL style: use bold claims, emotional triggers, "
                       "power numbers, pattern interrupts, and curiosity gaps..."
    },
    "Educational": {
        "icon": "📚", 
        "instruction": "Write in an EDUCATIONAL style: clear structure, step-by-step, "
                       "practical examples, actionable takeaways..."
    },
    "Founder": {
        "icon": "🚀",
        "instruction": "Write in a FOUNDER style: personal story, behind-the-scenes, "
                       "vulnerability + confidence, lessons learned..."
    },
    "Technical": {
        "icon": "⚙️",
        "instruction": "Write in a TECHNICAL style: precise terminology, deep insights, "
                       "implementation details, expert-level..."
    },
}
```

The `instruction` string is injected into every content prompt as `{style_instruction}`. This is how the same template produces 4 completely different tones.

### Content Type Prompts

Each content type has two parts:

```python
CONTENT_PROMPTS = {
    "linkedin_post": {
        "label": "LinkedIn Post",
        "icon": "💼",
        "system": "You are an expert LinkedIn content strategist...",
        "user": """Based on this YouTube transcript, write a high-performing LinkedIn post.

STYLE: {style_instruction}

RULES:
- 150-300 words
- Hook that stops scrolling (NOT 'I' as first word)
- Line breaks every 1-2 sentences
- 3-5 hashtags at end
- End with question or CTA

TRANSCRIPT:
{transcript}

Write only the post.""",
    },
```

**Why separate system and user prompts?**
The system prompt sets Claude's persona and domain expertise. The user prompt contains the actual task and the dynamic data (transcript + style). This separation produces more consistent, higher-quality output than putting everything in one message.

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

This function is the bridge between the template library and the API call.

---

## 7. File 3 — `agent.py`

> **What this file does:** Makes Claude API calls. One function per use case. Returns plain text.

### The Main Function

```python
import openai

def generate_content(content_type, transcript, style, max_tokens=2000) -> str:
    client = openai.OpenAI(api_key=...)
    prompt = build_prompt(content_type, transcript, style)
    
    response = client.messages.create(
        model="gpt-4o",
        max_tokens=max_tokens,
        system=prompt["system"],
        messages=[{"role": "user", "content": prompt["user"]}],
    )
    return response.content[0].text.strip()
```

**Why gpt-4o?**
It produces higher-quality, more nuanced content than smaller models, especially for creative writing tasks like viral hooks and founder stories. For a content creation tool where quality matters, the slightly higher cost is worth it.

**Error handling** — the function returns error strings (not raises) so the UI can display them gracefully:

```python
except openai.AuthenticationError:
    return "Error: Invalid API key."
except openai.RateLimitError:
    return "Error: Rate limit exceeded. Wait and retry."
except Exception as e:
    return f"Error: {str(e)}"
```

In `app.py`, we check `if result.startswith("Error:")` before displaying or saving.

### `generate_all_content()` — Batch Generation

```python
def generate_all_content(transcript, style, content_types=None) -> dict:
    results = {}
    for ct in content_types:
        results[ct] = generate_content(ct, transcript, style)
    return results
```

Called by the "Generate ALL" button in the UI — loops through all content types sequentially with a progress bar.

---

## 8. File 4 — `database.py`

> **What this file does:** All Supabase operations. One table: `content_history`. Falls back gracefully if Supabase isn't configured — the app still works, just without history.

### The Graceful Fallback Pattern

```python
def _db():
    url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        return None          # ← returns None, not raises
    return create_client(url, key)

def save_content(...) -> int:
    db = _db()
    if not db:
        return -1            # ← caller handles this gracefully
    # ... actual save
```

Every function checks `if not db: return safe_default`. This means the app works even without Supabase — you just don't get history or analytics.

### The Schema — One Table

```sql
CREATE TABLE content_history (
    id              BIGSERIAL PRIMARY KEY,
    video_id        TEXT,      -- YouTube video ID
    video_title     TEXT,      -- extracted by Claude
    style           TEXT,      -- Viral / Educational / Founder / Technical  
    content_type    TEXT,      -- linkedin_post / twitter_thread / etc.
    generated_text  TEXT,      -- the actual content
    char_count      INTEGER,   -- for analytics
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

Why one table instead of separate tables per content type? Simplicity. All content is the same shape — it's just text associated with a video and a style. One table makes analytics queries trivial.

### Analytics Query

```python
def get_analytics() -> dict:
    resp = db.table("content_history").select(
        "id, video_id, style, content_type, char_count, created_at"
    ).execute()
    rows = resp.data or []
    
    # Content type breakdown
    ct_counts = {}
    for r in rows:
        ct = r["content_type"]
        ct_counts[ct] = ct_counts.get(ct, 0) + 1
    
    return {"content_type_counts": ct_counts, ...}
```

We fetch all rows once and compute all analytics in Python — no complex SQL needed at this scale.

---

## 9. File 5 — `app.py`

> **What this file does:** The entire Streamlit UI across 7 pages. Uses session state to persist the transcript and generated content between page navigations.

### The 7 Pages

| Page | What It Shows |
|------|--------------|
| 🏠 Home | URL input, video info after extraction |
| 📄 Transcript | Full text + timestamped segments |
| ✨ Generate | Generate each content type individually or all at once |
| 📋 All Content | All generated content in one scrollable page + export all |
| 📁 History | Past generations from Supabase with filter and delete |
| 📊 Analytics | Charts: by type, by style, daily activity, top videos |
| ⚙️ Prompts | View built-in prompts, create custom prompts, test them |

### Session State Variables

```python
st.session_state.transcript_data    # dict from get_transcript()
st.session_state.generated_content  # {ct_key: text}
st.session_state.current_style      # "Educational" etc.
st.session_state.video_meta         # title, channel, description
st.session_state.custom_prompts     # user-created prompt templates
```

When the user changes the writing style in the sidebar, we clear `generated_content`:
```python
if selected_style != st.session_state.current_style:
    st.session_state.current_style = selected_style
    st.session_state.generated_content = {}  # force regeneration
```

### The Generate Page Pattern

```python
# Show content if generated, otherwise show generate button
generated = st.session_state.generated_content.get(ct_key, "")

with st.expander(f"{icon} {label}", expanded=bool(generated)):
    if generated and not generated.startswith("Error:"):
        st.markdown(f'<div class="content-box">{generated}</div>', ...)
        # Download button, char count, regenerate button
    else:
        if st.button(f"Generate {label}", type="primary"):
            result = generate_content(ct_key, transcript, style)
            st.session_state.generated_content[ct_key] = result
            if db_ok():
                save_content(...)
            st.rerun()
```

The expander is `expanded=True` only when content has been generated — so the page is collapsed by default and opens up as content appears.

### Custom Prompt System

Users can create their own content types in the Prompts page:

```python
# User fills in name, icon, system prompt, user prompt template
# Saved to session_state.custom_prompts

st.session_state.custom_prompts[key] = {
    "label": cp_label,
    "icon": cp_icon,
    "system": cp_system,
    "user": cp_user,  # must contain {transcript} and {style_instruction}
}
```

The Generate page merges built-in and custom prompts, so custom types appear alongside built-in ones.

---

## 10. Supabase Setup

### Step 1 — Create free project

1. [supabase.com](https://supabase.com) → **New Project**
2. Wait ~2 minutes

### Step 2 — Run the schema

Go to **SQL Editor → New Query**, paste `supabase_schema.sql`, click **Run ▶**:

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

### Step 3 — Get credentials

**Project Settings → API:**
- Copy **Project URL** → `SUPABASE_URL`
- Copy **anon public** key → `SUPABASE_KEY`

---

## 11. Running Locally

```bash
source venv/bin/activate
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501)

### First Run Walkthrough

1. **🏠 Home** — Paste a YouTube URL (try a TED talk or tutorial)
2. Click **Extract ▶** — transcript loads in seconds
3. In the sidebar, pick a **Writing Style** (start with Viral)
4. Go to **✨ Generate** — click **⚡ Generate ALL Content**
5. Watch 6 pieces generate with a progress bar
6. Go to **📋 All Content** — see everything, download all as one file
7. Go to **📄 Transcript** — browse the timestamped segments
8. Go to **📊 Analytics** — see your usage charts
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
2. Select repo, set main file: `app.py`
3. **Advanced settings → Secrets**:

```toml
OPENAI_API_KEY = "sk-your-openai-key-here"
SUPABASE_URL      = "https://your-project.supabase.co"
SUPABASE_KEY      = "your-anon-key-here"
```

> ⚠️ Must use TOML format: `KEY = "value"` with quotes. Not `KEY=value`.

4. Click **Deploy** — live in ~2 minutes ✅

**Without Supabase:** The app works without Supabase secrets. History and analytics pages show a "configure database" message. All generation features work normally.

---

## 13. Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `No English transcript available` | Video has no English captions | Try a different video; look for CC badge |
| `Transcripts are disabled` | Creator disabled captions | Try a different video |
| `Invalid API key` | Wrong OpenAI key | Check `OPENAI_API_KEY` in secrets |
| `relation does not exist` | Supabase schema not created | Run `supabase_schema.sql` in SQL Editor |
| `postgrest.exceptions.APIError` | No table permissions | Re-run the GRANT statements in the schema |
| `Invalid format: TOML` | Using `KEY=value` in Streamlit secrets | Use `KEY = "value"` with quotes and spaces |
| `RateLimitError` | OpenAI quota exceeded | Wait or add billing at platform.openai.com/api-keys |
| Video loads but content is short | Transcript was trimmed | Normal for long videos — `chunk_transcript()` trims to 12k chars |

---

## 14. What You Learned

- ✅ **YouTube transcript extraction** — without any YouTube API key using `youtube-transcript-api`
- ✅ **Prompt engineering** — system vs user prompts, style injection, structured output control
- ✅ **Prompt management system** — template library with runtime variable injection
- ✅ **Claude API** — `client.messages.create()` with system/user message structure
- ✅ **Graceful degradation** — optional Supabase with fallback to in-memory state
- ✅ **Streamlit session state** — persisting data across page navigations and reruns
- ✅ **Multi-page Streamlit app** — radio button routing with shared state
- ✅ **Custom CSS in Streamlit** — cards, badges, dark transcript viewer
- ✅ **Plotly analytics** — bar charts, pie charts, line charts in Streamlit
- ✅ **Supabase** — single-table schema for flexible content storage

---

## 15. What's Next

### Easy
- **More content types** — podcast show notes, YouTube description, email newsletter
- **Multiple URLs at once** — batch process a whole playlist
- **Language support** — add non-English language detection and generation

### Intermediate
- **Tone customisation sliders** — control formality, length, emoji usage
- **Scheduled posting** — connect to Buffer or Hootsuite API
- **Image prompt generation** — generate Midjourney prompts for carousel visuals

### Advanced
- **Auto-post to LinkedIn** — use LinkedIn API to post directly
- **Video topic clustering** — group your history by topic using embeddings
- **A/B hook testing** — track which hooks perform best using bit.ly or UTM params

---

## ⭐ Enjoyed this tutorial?

- ⭐ **[Star the repository](https://github.com/adityasharmadotai-hash)**
- 💼 **[Follow on LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)**
- 📺 **[Subscribe on YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)**
- 🚀 **[AI Jobs in the USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

---

*Built with ❤️ using Python, OpenAI GPT-4o, Supabase, and Streamlit*
