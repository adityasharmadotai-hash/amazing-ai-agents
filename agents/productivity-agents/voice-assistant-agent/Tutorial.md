# 🤖 Build ARIA — AI Voice Assistant Agent from Scratch

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

> **What you'll build:** A browser-based AI voice assistant that records your voice in real-time, transcribes it with Whisper, detects your intent with GPT-4o, auto-creates tasks/notes/reminders/events, and speaks responses back using OpenAI TTS — all in a Streamlit web app.

---

## 📋 Table of Contents

1. [What Are We Building?](#1-what-are-we-building)
2. [How It Works](#2-how-it-works)
3. [Prerequisites](#3-prerequisites)
4. [Project Setup](#4-project-setup)
5. [File 1 — recorder.py (Browser Microphone)](#5-file-1--recorderpy)
6. [File 2 — stt.py (Whisper Transcription)](#6-file-2--sttpy)
7. [File 3 — tts.py (Text-to-Speech)](#7-file-3--ttspy)
8. [File 4 — agent.py (Conversational AI)](#8-file-4--agentpy)
9. [File 5 — tasks.py (Task Management)](#9-file-5--taskspy)
10. [File 6 — database.py (Persistence)](#10-file-6--databasepy)
11. [File 7 — app.py (Streamlit UI)](#11-file-7--apppy)
12. [Running Locally](#12-running-locally)
13. [Deploying to Streamlit Cloud](#13-deploying-to-streamlit-cloud)
14. [Common Errors & Fixes](#14-common-errors--fixes)
15. [What You Learned](#15-what-you-learned)
16. [What's Next](#16-whats-next)

---

## 1. What Are We Building?

Most AI assistants require a native app or special hardware. ARIA runs in a browser tab and uses three OpenAI APIs plus the browser's own microphone:

```
🎙️ You click mic    →  Browser records WebM audio
🌐 Whisper API       →  "Add a task to review the proposal by Friday"
🧠 GPT-4o            →  [INTENT: CREATE_TASK] + "Done! I've added that task."
✅ tasks.py          →  Task created in session state
🔊 TTS API           →  ARIA speaks the confirmation aloud
```

No third-party libraries needed for the microphone. No audio processing on the server. The browser handles the recording natively.

---

## 2. How It Works

```
┌──────────────────────────────────────────────────────────────────┐
│                    FULL ARCHITECTURE                             │
│                                                                  │
│  INPUT LAYER                                                     │
│  ├── recorder.py  — JS MediaRecorder in iframe → base64 bytes   │
│  ├── stt.py       — file upload → Whisper API → text            │
│  └── app.py       — st.chat_input → direct text                 │
│                          ↓                                       │
│  AI LAYER                                                        │
│  └── agent.py — GPT-4o with intent schema in system prompt      │
│      Returns: [INTENT: {"type":"...", "data":{...}}]            │
│               + spoken response text                             │
│                          ↓                                       │
│  ACTION LAYER                                                    │
│  └── tasks.py — session-state store for all data types          │
│      add_task() / add_note() / add_reminder() / add_calendar()  │
│                          ↓                                       │
│  OUTPUT LAYER                                                    │
│  ├── tts.py   — OpenAI TTS → MP3 → base64 HTML audio player    │
│  └── app.py   — chat bubble + action card + audio autoplay      │
│                          ↓                                       │
│  OPTIONAL PERSISTENCE                                            │
│  └── database.py — Supabase conversations table                 │
└──────────────────────────────────────────────────────────────────┘
```

**Six files, each with one clear job:**

| File | Job | Key technology |
|------|-----|----------------|
| `recorder.py` | Browser mic recording | WebRTC MediaRecorder API (JS) |
| `stt.py` | Audio → text | OpenAI Whisper API |
| `tts.py` | Text → speech | OpenAI TTS API |
| `agent.py` | Chat + intent detection | OpenAI GPT-4o |
| `tasks.py` | Data store | Streamlit session state |
| `database.py` | Cloud persistence | Supabase (optional) |

---

## 3. Prerequisites

### ✅ Required

- [ ] Python 3.10+ — [python.org/downloads](https://python.org/downloads)
- [ ] OpenAI API key — [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- [ ] A modern browser (Chrome recommended for mic recording)
- [ ] GitHub + Streamlit accounts for deployment

### 🔶 Optional

- [ ] Supabase account — [supabase.com](https://supabase.com) — for persistent history

### 💰 Cost per session (~20 messages)

| API | Cost |
|-----|------|
| Whisper (5 voice messages, 1 min each) | ~$0.03 |
| GPT-4o (20 chat messages) | ~$0.10 |
| TTS (20 responses, ~200 chars each) | ~$0.06 |
| **Total** | **~$0.19** |

---

## 4. Project Setup

```bash
mkdir voice-assistant-agent && cd voice-assistant-agent
mkdir modules .streamlit

python3 -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows

pip install streamlit openai supabase plotly python-dotenv

cp .env.example .env
# Set OPENAI_API_KEY=sk-your-key in .env
```

---

## 5. File 1 — `recorder.py`

> **What this file does:** Embeds a complete HTML/JavaScript microphone recorder inside a Streamlit `components.html()` iframe. The browser records audio using the native **MediaRecorder API**, encodes it as WebM/Opus, and passes the base64 bytes back to Python via a `postMessage`.

### Why not use a Python audio library?

Streamlit runs on a server. Python has no access to the user's microphone. The only way to record in a Streamlit app is via browser JavaScript injected through `st.components.v1.html()`.

### The Architecture

```
Streamlit Python process
    └── st.components.v1.html(RECORDER_HTML, height=320)
              ↓
         Browser renders HTML in an <iframe>
              ↓
         User clicks mic → navigator.mediaDevices.getUserMedia()
              ↓
         MediaRecorder collects audio chunks every 100ms
              ↓
         User clicks stop → Blob assembled from chunks
              ↓
         User clicks "Send to ARIA"
              ↓
         FileReader → base64 string
              ↓
         window.parent.postMessage({type: "streamlit:setComponentValue", value: {...}})
              ↓
         Python receives: {"audio_b64": "...", "ext": ".webm", "duration": 12}
```

### Key JavaScript Concepts

**`navigator.mediaDevices.getUserMedia()`** — prompts the user for mic permission and returns an audio stream:

```javascript
const stream = await navigator.mediaDevices.getUserMedia({
    audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true }
});
```

**`MediaRecorder`** — records chunks from the stream:

```javascript
const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
mediaRecorder.start(100);   // collect chunk every 100ms
```

**Sending back to Python:**
```javascript
window.parent.postMessage({
    type: 'streamlit:setComponentValue',
    value: { audio_b64: base64String, ext: '.webm', duration: secondsElapsed }
}, '*');
```

**MIME type fallback** — different browsers support different formats:
```javascript
const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
    ? 'audio/webm;codecs=opus'
    : MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm'
    : MediaRecorder.isTypeSupported('audio/ogg') ? 'audio/ogg'
    : '';  // browser decides
```

### Python Side

```python
def mic_recorder(key="mic_recorder", height=320):
    result = components.html(RECORDER_HTML, height=height, scrolling=False)
    return result   # dict or None

def decode_recording(result: dict) -> tuple[bytes, str]:
    b64 = result.get("audio_b64", "")
    ext = result.get("ext", ".webm")
    return base64.b64decode(b64), ext
```

### Deduplication — Preventing Double Processing

Each recording has a `duration` field. We track the last processed duration in session state to avoid sending the same recording twice when Streamlit reruns:

```python
rec_hash = rec_result.get("duration", 0)
last_hash = st.session_state.get("_last_rec_hash", -1)
if audio_bytes and rec_hash != last_hash:
    st.session_state["_last_rec_hash"] = rec_hash
    # process...
```

### Browser Compatibility

| Browser | MediaRecorder | WebM/Opus |
|---------|--------------|-----------|
| Chrome 70+ | ✅ | ✅ |
| Edge 79+ | ✅ | ✅ |
| Firefox 65+ | ✅ | ✅ (OGG fallback) |
| Safari 14.1+ | ✅ | ✅ |

> **HTTPS requirement:** `getUserMedia()` only works on HTTPS or `localhost`. Streamlit Cloud provides HTTPS automatically. For local development, `http://localhost:8501` works fine.

---

## 6. File 2 — `stt.py`

> **What this file does:** Sends audio bytes (from the mic recorder or a file upload) to OpenAI Whisper API and returns structured transcript data.

### The Temp File Pattern

Whisper API requires a file-like object with an extension. Raw bytes don't have a name, so we write to a temp file:

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
    os.unlink(tmp_path)   # always clean up
```

`verbose_json` returns timestamps, detected language, and duration — not just the text.

### Language Support

Whisper auto-detects the language. You can also specify `language="en"` to force English and slightly improve accuracy and speed. The app exposes this as a dropdown in the Upload tab.

---

## 7. File 3 — `tts.py`

> **What this file does:** Converts ARIA's text responses to speech using OpenAI TTS API, then generates an HTML `<audio>` tag with base64-encoded MP3 for browser playback.

### The Base64 Audio Pattern

Streamlit's `st.audio()` doesn't support autoplay. We inject a raw HTML audio tag:

```python
def audio_to_html(audio_bytes: bytes, autoplay: bool = True) -> str:
    b64 = base64.b64encode(audio_bytes).decode()
    return f"""
    <audio controls {'autoplay'} style="width:100%;border-radius:8px;">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """
```

Then: `st.markdown(audio_to_html(bytes), unsafe_allow_html=True)`

### 6 Available Voices

| Voice | Character |
|-------|-----------|
| alloy | Neutral, balanced |
| echo | Clear, male |
| fable | Warm, British |
| onyx | Deep, authoritative |
| nova | Bright, female (default) |
| shimmer | Soft, friendly |

---

## 8. File 4 — `agent.py`

> **What this file does:** The brain of ARIA. Sends the user's message to GPT-4o with a carefully engineered system prompt that forces structured intent output before every response.

### Intent Detection via Prompting

Instead of OpenAI's function calling API, we use a simpler pattern — the system prompt instructs GPT-4o to output a JSON intent block at the start of every response:

```
[INTENT: {"type": "CREATE_TASK", "data": {"task": "Review proposal", "deadline": "Friday", "priority": "High"}}]
Done! I've added that task to your list.
```

We parse this with a regex and execute the action in `app.py`:

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

### Why this works better than function calling for voice

Function calling requires pre-defined schemas and multiple round trips. The prompt-based approach:
- Works in a single API call
- The intent and response come together
- Easier to customise for new intent types
- GPT-4o is instruction-following enough to be reliable

### Context Injection

ARIA's responses are smarter because we inject the user's current data:

```python
context = "TASKS: Review proposal; Send invoice\nNOTES: Meeting summary"
messages.append({"role": "system", "content": f"CONTEXT:\n{context}"})
```

This lets ARIA say "You already have 3 pending tasks" or reference a previous note.

---

## 9. File 5 — `tasks.py`

> **What this file does:** Session-state-based in-memory store for tasks, notes, reminders, and calendar events. No database required — everything persists within a browser tab.

### Why Session State?

Streamlit reruns the entire script on every user interaction. `st.session_state` persists Python objects between reruns — it's essentially a per-user in-memory dictionary.

```python
def init_stores():
    if "tasks" not in st.session_state:
        st.session_state.tasks = []

def add_task(task, deadline="", priority="Medium") -> dict:
    item = {"id": _id(), "task": task, "deadline": deadline,
            "priority": priority, "status": "pending", "created_at": _now()}
    st.session_state.tasks.insert(0, item)
    return item
```

Each item gets a random 8-character UUID as its `id` — used for the complete/delete buttons.

### All Four Stores

```python
st.session_state.tasks          # list of task dicts
st.session_state.notes          # list of note dicts
st.session_state.reminders      # list of reminder dicts
st.session_state.calendar_events  # list of event dicts
```

---

## 10. File 6 — `database.py`

> **What this file does:** Optional Supabase persistence for conversation history. Falls back gracefully — the entire app works without it.

```python
def _db():
    url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        return None        # ← safe fallback
    return create_client(url, key)
```

Every function checks `if not db: return` — so `save_message()`, `get_history()`, etc. all silently no-op when Supabase isn't configured.

---

## 11. File 7 — `app.py`

> **What this file does:** 8-page Streamlit UI. The Voice Chat page has two input methods (🔴 Record tab, 📁 Upload tab) and a full chat interface with styled bubbles, action cards, and TTS playback.

### The Voice Chat Page Layout

```
┌─────────────────────────┬──────────────────────────┐
│  CHAT (col ratio 3)     │  VOICE INPUT (col ratio 2)│
│                         │                           │
│  Welcome card /         │  Tab: 🔴 Record           │
│  Conversation bubbles   │   └── JS recorder iframe  │
│                         │   └── Transcription result│
│  TTS audio player       │                           │
│  Chat input box         │  Tab: 📁 Upload           │
│  Quick action buttons   │   └── File uploader       │
│  Clear button           │   └── Language selector   │
│                         │   └── Transcribe button   │
│                         │                           │
│                         │  🔊 ARIA's Voice          │
│                         │   └── TTS toggle          │
│                         │   └── Voice selector      │
│                         │   └── Speed slider        │
│                         │   └── Preview button      │
│                         │                           │
│                         │  🔔 Active Reminders      │
└─────────────────────────┴──────────────────────────┘
```

### The Message Processing Pipeline

All three input methods (mic, upload, type) funnel through one function:

```python
def _process_message(user_text: str, is_audio: bool = False):
    # 1. Add user bubble
    st.session_state.conversation.append({"role": "user", "content": user_text, ...})

    # 2. Build context from tasks/notes
    context = "TASKS: " + "; ".join(t["task"] for t in get_tasks("pending")[:5])

    # 3. GPT-4o → intent + response
    result = ai_chat(user_text, history, context)
    intent_type = result["intent"]["type"]   # e.g. "CREATE_TASK"
    intent_data = result["intent"]["data"]   # e.g. {"task": "..."}

    # 4. Execute intent
    if intent_type == "CREATE_TASK":
        task = add_task(intent_data["task"], ...)
        action_msg = f"✅ Task added: {task['task']}"

    # 5. Add ARIA bubble with action card
    st.session_state.conversation.append({
        "role": "assistant", "content": response_text,
        "intent": intent_type, "action": action_msg, ...
    })

    # 6. TTS
    if st.session_state.tts_enabled:
        st.session_state.last_audio = synthesize(response_text, voice, speed)
```

### Handling the Mic Recording in app.py

```python
rec_result = mic_recorder(key="live_mic", height=320)

if rec_result and isinstance(rec_result, dict) and rec_result.get("audio_b64"):
    audio_bytes, ext = decode_recording(rec_result)
    rec_hash = rec_result.get("duration", 0)

    if audio_bytes and rec_hash != st.session_state.get("_last_rec_hash", -1):
        st.session_state["_last_rec_hash"] = rec_hash
        result = transcribe_bytes(audio_bytes, ext)   # Whisper
        if result.get("text"):
            _process_message(result["text"], is_audio=True)
            st.rerun()
```

---

## 12. Running Locally

```bash
source venv/bin/activate
streamlit run app.py
# Opens at http://localhost:8501
```

### First Run Walkthrough

1. **⚙️ Settings** → Enter your OpenAI API key → Save
2. **🎙️ Voice Chat** → Click **🔴 Record** tab
3. Click the **pulse mic button** → allow microphone access
4. Say: *"Add a task to finish the report by Thursday"*
5. Click the mic again to stop → preview plays in browser
6. Click **📤 Send to ARIA** → see the transcript → ARIA responds
7. Watch the task get created automatically in the chat
8. Click **✅ Tasks** in sidebar → your task is there
9. Say: *"Remind me to check emails every morning at 8 AM"*
10. Say: *"Schedule a team standup tomorrow at 10 AM"*
11. Go to **📊 Dashboard** → see your intent breakdown chart

---

## 13. Deploying to Streamlit Cloud

```bash
git add . && git commit -m "ARIA Voice Assistant" && git push
```

1. [share.streamlit.io](https://share.streamlit.io) → New app
2. Select repo, main file: `app.py`
3. **Advanced → Secrets** (TOML format — quotes required):

```toml
OPENAI_API_KEY = "sk-your-openai-key"
SUPABASE_URL   = "https://xxx.supabase.co"
SUPABASE_KEY   = "your-anon-key"
```

4. Deploy ✅ — live in ~2 minutes

**Microphone on Streamlit Cloud:** Works automatically because Streamlit Cloud serves on HTTPS, which is required for `getUserMedia()`.

**Public access without sharing your key:** Users can enter their own OpenAI key on the **⚙️ Settings** page.

---

## 14. Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| Mic button does nothing | No mic permission | Click the lock icon in browser URL bar → allow mic |
| `NotAllowedError` in JS console | Mic permission denied | Allow in browser settings → refresh |
| `Invalid API key` | Wrong key | Go to ⚙️ Settings → re-enter key |
| `Audio too short` | < 1 second recorded | Speak for at least 2 seconds |
| `File too large` | > 25 MB | Compress: `ffmpeg -i file.mp4 file.mp3` |
| TTS doesn't autoplay | Browser policy | Click the audio player manually |
| Intent not detected | Very short message | ARIA defaults to CHAT — rephrase |
| Recording works locally but not on server | HTTP vs HTTPS | Streamlit Cloud uses HTTPS — deploy there |
| `relation does not exist` | No Supabase schema | Run `supabase_schema.sql` in SQL Editor |
| No audio in recording | Wrong input device | Check OS microphone settings |

---

## 15. What You Learned

- ✅ **Browser MediaRecorder API** — recording audio in the browser with JavaScript
- ✅ **Streamlit HTML components** — embedding JavaScript and communicating back to Python
- ✅ **Base64 audio transfer** — encoding audio bytes for browser-to-Python transfer
- ✅ **OpenAI Whisper API** — temp file pattern, verbose_json response format
- ✅ **OpenAI TTS API** — MP3 bytes → base64 HTML audio tag for browser playback
- ✅ **Intent detection via prompting** — structured JSON extraction without function calling
- ✅ **GPT-4o system prompt engineering** — forcing consistent structured output
- ✅ **Streamlit session state** — using it as an in-memory database across reruns
- ✅ **Graceful degradation** — optional Supabase, optional TTS, always works
- ✅ **HTTPS/microphone security** — why browser mic requires secure context

---

## 16. What's Next

### Easy
- **More languages** — Whisper supports 99 languages; just change `language` param
- **Larger context** — pass more history to GPT-4o for better follow-up handling
- **Custom wake word UI** — add a "listening" animation while waiting for speech

### Intermediate
- **Real-time streaming TTS** — stream GPT-4o tokens and feed to TTS progressively
- **Live web search** — integrate Serper/Tavily for real-time search results
- **Google Calendar sync** — push events to actual Google Calendar via OAuth

### Advanced
- **Continuous listening mode** — poll `getUserMedia` in a loop to detect silence/speech
- **Speaker identification** — use pyannote to identify who spoke in a group meeting
- **Multi-session persistence** — store tasks/notes per user using Supabase Auth

---

## ⭐ Enjoyed this tutorial?

- ⭐ **[Star the repository](https://github.com/adityasharmadotai-hash)** — helps others discover this
- 🌐 **[Visit adityasharma.ai](https://www.adityasharma.ai)** — AI training for professionals
- 💼 **[Follow on LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)** — daily AI updates
- 📺 **[Subscribe on YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)** — AI agent tutorials
- 🚀 **[AI Jobs in the USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

---

*Built with ❤️ by [Aditya Sharma](https://www.adityasharma.ai) · OpenAI Whisper + GPT-4o + TTS + WebRTC + Streamlit*