# 🤖 Build an AI Voice Assistant Agent from Scratch

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

> **What you'll build:** A fully voice-enabled AI assistant that transcribes audio, understands intent, creates tasks/notes/reminders/events automatically, speaks responses aloud, and tracks everything in a dashboard.

---

## 📋 Table of Contents

1. [What Are We Building?](#1-what-are-we-building)
2. [How It Works](#2-how-it-works)
3. [Prerequisites](#3-prerequisites)
4. [Project Setup](#4-project-setup)
5. [File 1 — stt.py (Speech-to-Text)](#5-file-1--sttpy)
6. [File 2 — tts.py (Text-to-Speech)](#6-file-2--ttspy)
7. [File 3 — agent.py (Conversational AI)](#7-file-3--agentpy)
8. [File 4 — tasks.py (Task Management)](#8-file-4--taskspy)
9. [File 5 — database.py (Persistence)](#9-file-5--databasepy)
10. [File 6 — app.py (Streamlit UI)](#10-file-6--apppy)
11. [Running Locally](#11-running-locally)
12. [Deploying to Streamlit Cloud](#12-deploying-to-streamlit-cloud)
13. [Common Errors & Fixes](#13-common-errors--fixes)
14. [What You Learned](#14-what-you-learned)
15. [What's Next](#15-whats-next)

---

## 1. What Are We Building?

Most AI assistants require a native app. This one runs in a browser tab and uses three OpenAI APIs together:

```
🎙️ You speak  →  Whisper transcribes  →  GPT-4o understands  →  TTS speaks back
```

Example interaction:

```
You (voice): "Remind me to call the doctor tomorrow at 9 AM"
      ↓
Whisper: "Remind me to call the doctor tomorrow at 9 AM"
      ↓
GPT-4o:  [INTENT: {"type": "CREATE_REMINDER", "data": {"reminder": "Call the doctor", "time": "Tomorrow 9 AM"}}]
         "Done! I've set a reminder to call the doctor tomorrow at 9 AM."
      ↓
tasks.py: Reminder added to session state
      ↓
TTS: ARIA speaks the confirmation aloud
```

ARIA understands 8 intent types: CHAT, CREATE_TASK, CREATE_NOTE, CREATE_REMINDER, CALENDAR_EVENT, SEARCH_WEB, UPDATE_TASK, SUMMARISE.

---

## 2. How It Works

```
┌──────────────────────────────────────────────────────────────────┐
│                    ARIA AGENT FLOW                               │
│                                                                  │
│  USER uploads audio / types message                             │
│           ↓                                                       │
│    stt.py — OpenAI Whisper                                       │
│    audio bytes → temp file → transcript text                    │
│           ↓                                                       │
│    agent.py — OpenAI GPT-4o                                     │
│    system prompt with intent schema                             │
│    → [INTENT: {"type": "...", "data": {...}}]                   │
│    → spoken response text                                       │
│           ↓                                                       │
│    Intent execution in app.py                                   │
│    CREATE_TASK → tasks.add_task()                               │
│    CREATE_NOTE → tasks.add_note()                               │
│    CREATE_REMINDER → tasks.add_reminder()                       │
│    CALENDAR_EVENT → tasks.add_calendar_event()                  │
│           ↓                                                       │
│    tts.py — OpenAI TTS                                           │
│    response text → MP3 bytes → HTML audio player               │
│           ↓                                                       │
│    app.py — Streamlit                                            │
│    render chat bubble + audio autoplay                          │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Prerequisites

- [ ] Python 3.10+ — [python.org](https://python.org/downloads)
- [ ] OpenAI API key — [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- [ ] GitHub + Streamlit accounts (for deployment)
- [ ] Supabase account (optional — for persistent history)

### 💰 Cost estimate

- Whisper: ~$0.006/minute
- GPT-4o: ~$0.005/message
- TTS: ~$0.015/1K characters
- **Typical 20-message session: ~$0.15**

---

## 4. Project Setup

```bash
mkdir voice-assistant-agent && cd voice-assistant-agent
mkdir modules .streamlit
python3 -m venv venv && source venv/bin/activate
pip install streamlit openai supabase plotly python-dotenv
cp .env.example .env  # add OPENAI_API_KEY
```

---

## 5. File 1 — `stt.py`

> **What it does:** Converts audio bytes to text using OpenAI Whisper. Handles the temp file requirement, file size validation, and multiple language support.

### Key Pattern: Temp File

Whisper API needs a file object with an extension — not raw bytes. We write to a temp file:

```python
with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
    tmp.write(audio_bytes)
    tmp_path = tmp.name

try:
    with open(tmp_path, "rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
        )
finally:
    os.unlink(tmp_path)   # ← always clean up
```

`verbose_json` returns timestamps + detected language in addition to text.

---

## 6. File 2 — `tts.py`

> **What it does:** Converts text to speech using OpenAI's TTS API. Returns MP3 bytes and provides a helper to render an HTML audio player in Streamlit.

### Key Pattern: Base64 Audio in Streamlit

Streamlit can't play audio bytes directly via `st.audio` with autoplay. We encode to base64 and inject an HTML `<audio>` tag:

```python
def audio_to_html(audio_bytes: bytes, autoplay: bool = True) -> str:
    b64 = base64.b64encode(audio_bytes).decode()
    return f"""
    <audio controls {'autoplay'} style="width:100%;">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """
```

Then in the app: `st.markdown(audio_to_html(bytes), unsafe_allow_html=True)`

### 6 Available Voices

alloy (neutral) · echo (male) · fable (British) · onyx (deep) · nova (female) · shimmer (soft)

---

## 7. File 3 — `agent.py`

> **What it does:** Sends messages to GPT-4o with a system prompt that instructs it to output a structured intent JSON block before every response.

### The Intent Detection Trick

The system prompt tells GPT-4o to start every response with:
```
[INTENT: {"type": "CREATE_TASK", "data": {"task": "Review proposal", "deadline": "Friday", "priority": "High"}}]
```

We parse this with a regex, execute the action, then show only the clean spoken response:

```python
def _parse_intent(text: str) -> tuple[dict, str]:
    pattern = r"\[INTENT:\s*(\{.*?\})\s*\]"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        intent = json.loads(match.group(1))
        clean = text[:match.start()] + text[match.end():]
        return intent, clean.strip()
    return {"type": "CHAT"}, text
```

This gives us structured data extraction without any function calling setup — just clever prompting.

### Context Injection

We pass the user's current tasks and notes as context so ARIA can reference them:

```python
context = "CURRENT TASKS: Review proposal; Send invoice\nRECENT NOTES: Meeting summary"
messages.append({"role": "system", "content": f"CONTEXT:\n{context}"})
```

---

## 8. File 4 — `tasks.py`

> **What it does:** Session-state-based storage for tasks, notes, reminders, and calendar events. No database required — everything lives in `st.session_state`.

### Why Session State (Not a Database)?

For a demo/personal tool, session state is perfect:
- Zero setup
- Instant reads/writes
- No network latency
- Works without Supabase

For production, swap to Supabase (database.py handles this).

### The Pattern

```python
def init_stores():
    """Called once at app startup."""
    if "tasks" not in st.session_state:
        st.session_state.tasks = []

def add_task(task, deadline="", priority="Medium") -> dict:
    item = {"id": _id(), "task": task, "deadline": deadline,
            "priority": priority, "status": "pending", "created_at": _now()}
    st.session_state.tasks.insert(0, item)  # newest first
    return item
```

---

## 9. File 5 — `database.py`

> **What it does:** Optional Supabase persistence. Saves conversations, tasks, and notes permanently. Returns empty/None gracefully if not configured.

```python
def _db():
    url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        return None       # ← app works without DB
    return create_client(url, key)
```

---

## 10. File 6 — `app.py`

> **What it does:** 8-page Streamlit UI with voice chat, task manager, notes, reminders, calendar, dashboard, and settings.

### The Message Processing Pipeline

Every user message (voice or text) goes through one function:

```python
def _process_message(user_text: str, is_audio: bool = False):
    # 1. Add user message to conversation
    st.session_state.conversation.append({"role": "user", "content": user_text, ...})

    # 2. Build context from current tasks/notes
    context = "CURRENT TASKS: " + "; ".join(t["task"] for t in get_tasks("pending")[:5])

    # 3. Get AI response with intent
    result = ai_chat(user_text, st.session_state.conversation[:-1], context)
    intent = result["intent"]         # {"type": "CREATE_TASK", "data": {...}}
    response = result["response"]     # clean spoken text

    # 4. Execute intent
    if intent["type"] == "CREATE_TASK":
        add_task(intent["data"]["task"], ...)

    # 5. Add assistant response
    st.session_state.conversation.append({"role": "assistant", "content": response})

    # 6. TTS if enabled
    if st.session_state.tts_enabled:
        audio = synthesize(response, st.session_state.tts_voice)
        st.session_state.last_audio = audio
```

### Chat Bubbles via HTML

Streamlit's `st.chat_message` doesn't support the custom bubble styling we want. We use `st.markdown` with `unsafe_allow_html=True`:

```python
st.markdown(f'<div class="bubble-user">{content}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="bubble-assistant">{content}</div>', unsafe_allow_html=True)
```

---

## 11. Running Locally

```bash
source venv/bin/activate
streamlit run app.py
```

### First Run Walkthrough

1. **⚙️ Settings** — Enter your OpenAI API key → Save
2. **🎙️ Voice Chat** — Type "Add a task to review the proposal by Friday"
3. Watch ARIA create the task automatically and confirm
4. Upload an MP3/WAV recording → Transcribe & Send
5. Toggle "Auto-speak responses" → ARIA speaks back
6. **✅ Tasks** — See your task created automatically
7. **📊 Dashboard** — See intent breakdown and task stats
8. Try: "Set a reminder to call Alice tomorrow at 2 PM"
9. Try: "Schedule a team meeting on Thursday at 3 PM"

---

## 12. Deploying to Streamlit Cloud

```bash
git add . && git commit -m "ARIA Voice Assistant" && git push
```

1. [share.streamlit.io](https://share.streamlit.io) → New app → your repo
2. Main file: `app.py`
3. Secrets:
```toml
OPENAI_API_KEY = "sk-your-key"
SUPABASE_URL   = "https://xxx.supabase.co"
SUPABASE_KEY   = "your-anon-key"
```
4. Deploy ✅

Users can also add their own key via **⚙️ Settings** — no server key needed for public demos.

---

## 13. Common Errors & Fixes

| Error | Fix |
|-------|-----|
| `Invalid API key` | Check key in ⚙️ Settings |
| `Audio too short` | Record > 1 second of speech |
| `File too large` | Max 25 MB — compress to MP3 |
| `Rate limit` | Wait 10s and retry |
| Intent not detected | GPT-4o sometimes skips intent block — normal for very short messages |
| TTS not playing | Some browsers block autoplay — click the audio player manually |
| No speech in audio | Ensure mic is recording / file has actual audio |

---

## 14. What You Learned

- ✅ **OpenAI Whisper API** — audio bytes → text via temp file pattern
- ✅ **OpenAI TTS API** — text → MP3 bytes → base64 HTML audio player
- ✅ **Intent detection via prompting** — structured JSON in LLM responses without function calling
- ✅ **Context injection** — feeding task/note state into GPT-4o for smart responses
- ✅ **Session state as database** — storing structured data in st.session_state
- ✅ **Chat bubble UI** — custom styled bubbles via HTML in Streamlit
- ✅ **Multi-page Streamlit** — 8-page app with sidebar button navigation
- ✅ **Graceful degradation** — optional Supabase, optional TTS, optional DB

---

## 15. What's Next

### Easy
- **Browser microphone recording** — use `streamlit-webrtc` for real-time mic input
- **More languages** — Whisper supports 99 languages, just change the `language` param
- **Voice command shortcuts** — map specific phrases to instant actions

### Intermediate
- **Live web search** — integrate Serper/Tavily API for real-time web answers
- **Google Calendar sync** — push events to real Google Calendar via OAuth
- **Recurring reminders** — add repeat logic with APScheduler

### Advanced
- **Real-time streaming** — stream GPT-4o responses token-by-token with TTS
- **Wake word detection** — listen continuously for "Hey ARIA"
- **Multi-user sessions** — tie session_id to user auth via Supabase Auth

---

## ⭐ Enjoyed this tutorial?

- ⭐ **[Star the repository](https://github.com/adityasharmadotai-hash)**
- 🌐 **[Visit adityasharma.ai](https://www.adityasharma.ai)**
- 💼 **[Follow on LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)**
- 📺 **[Subscribe on YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)**
- 🚀 **[AI Jobs in the USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

---

*Built with ❤️ by [Aditya Sharma](https://www.adityasharma.ai) · OpenAI Whisper + GPT-4o + TTS + Streamlit*
