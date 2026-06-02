<div align="center">

### ⭐ Support & Connect

[![Star the repo](https://img.shields.io/badge/⭐_Star_the_repo-amazing--ai--agents-FFD43B?style=for-the-badge&logo=github&logoColor=black)](https://github.com/adityasharmadotai-hash/amazing-ai-agents)

💼 **Follow on LinkedIn:** [aditya-hicounselor](https://www.linkedin.com/in/aditya-hicounselor/) &nbsp;•&nbsp; 📺 **Subscribe on YouTube:** [@adityasharma](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)

🚀 **Looking for jobs at top AI companies in the U.S.?** [**Apply here →**](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)

</div>

---

# 🎓 Build an AI Executive Email Assistant — Full Tutorial

A complete, beginner-friendly walkthrough for building a **voice-first AI email assistant** with Python, Streamlit, the OpenAI API, and the Gmail API. No prior AI experience required — if you can write basic Python, you can build this.

---

## 📑 Table of Contents

1. [What We're Building & Why](#1-what-were-building--why)
2. [How It Works (Flow Diagram)](#2-how-it-works-flow-diagram)
3. [Prerequisites Checklist](#3-prerequisites-checklist)
4. [Project Setup](#4-project-setup)
5. [The Files, Explained](#5-the-files-explained)
   - [5.1 `config/settings.py` — configuration](#51-configsettingspy--configuration)
   - [5.2 `database/` — the SQLite cache](#52-database--the-sqlite-cache)
   - [5.3 `prompts/templates.py` — the AI's instructions](#53-promptstemplatespy--the-ais-instructions)
   - [5.4 `services/auth_service.py` — Google sign-in](#54-servicesauth_servicepy--google-sign-in)
   - [5.5 `services/gmail_service.py` — talking to Gmail](#55-servicesgmail_servicepy--talking-to-gmail)
   - [5.6 `services/ai_service.py` — the brain](#56-servicesai_servicepy--the-brain)
   - [5.7 `services/voice_service.py` — speech in, speech out](#57-servicesvoice_servicepy--speech-in-speech-out)
   - [5.8 `utils/ui.py` — the glue](#58-utilsuipy--the-glue)
   - [5.9 `pages/4_Voice.py` — the star feature](#59-pages4_voicepy--the-star-feature)
   - [5.10 `app.py` — the entry point](#510-apppy--the-entry-point)
6. [Running It Locally](#6-running-it-locally)
7. [Deploying on Streamlit Cloud](#7-deploying-on-streamlit-cloud)
8. [Common Errors & Fixes](#8-common-errors--fixes)
9. [What You Learned](#9-what-you-learned)
10. [What's Next](#10-whats-next)

---

## 1. What We're Building & Why

We're building an **AI Executive Email Assistant**: a web app that connects to your Gmail and lets you manage your inbox using plain language — ideally, **your voice**.

Instead of clicking through dozens of emails, you say *"summarize my unread mail"* or *"draft a reply to the last email from Rahul,"* and the assistant does it.

**Why build this?**

- **It's a real, useful product.** Email overload is a universal problem.
- **It teaches the full AI-app stack.** You'll touch OAuth, REST APIs, LLM prompting, speech-to-text, async Python, a database cache, and deployment — the same skills used in production AI products.
- **It's modular.** Each piece (auth, Gmail, AI, voice) is isolated, so you can understand one part at a time.

By the end, you'll have a deployed app **and** a mental model for how AI assistants are wired together.

---

## 2. How It Works (Flow Diagram)

```
        ┌──────────────────────────────────────────────────────────┐
        │                     YOU (voice or UI)                     │
        └───────────────────────────┬───────────────────────────────┘
                                     │
                 🎤 speak            │            🖱  click
                                     ▼
        ┌──────────────────────────────────────────────────────────┐
        │              Streamlit UI  (app.py + pages/)              │
        └───────────────────────────┬───────────────────────────────┘
                                     │
                                     ▼
        ┌──────────────────────────────────────────────────────────┐
        │                     Services layer                        │
        │   voice_service ──▶ Whisper (speech → text)               │
        │        ▼                                                   │
        │   ai_service ─────▶ OpenAI (understand + write)           │
        │        ▼                                                   │
        │   gmail_service ──▶ Gmail API (read / search / draft)     │
        └───────────────────────────┬───────────────────────────────┘
                                     ▼
        ┌──────────────────────────────────────────────────────────┐
        │            SQLite cache  (fast dashboards)                │
        └──────────────────────────────────────────────────────────┘
```

**The voice journey, step by step:**

1. You speak a command into the browser.
2. `voice_service` sends the audio to **Whisper**, which returns text.
3. `ai_service` sends that text to an **LLM** with a prompt that says *"figure out what the user wants and reply in JSON."*
4. The app reads the JSON `intent` (e.g. `search_emails`) and calls the matching `gmail_service` method.
5. Results render on screen, and the assistant can **speak the answer back** via text-to-speech.

---

## 3. Prerequisites Checklist

Before you start, make sure you have:

- [ ] **Python 3.10+** installed (`python --version`)
- [ ] A code editor (VS Code recommended)
- [ ] A **Google account** with Gmail
- [ ] An **OpenAI account** with an API key — <https://platform.openai.com/api-keys>
- [ ] Basic comfort with the terminal (running commands, `cd`)
- [ ] (Optional) A **GitHub account** for deployment

> 💡 You do **not** need to know machine learning. We use the OpenAI API as a service — like any other web API.

---

## 4. Project Setup

### Step 1 — Get the code

```bash
git clone https://github.com/adityasharmadotai-hash/amazing-ai-agents.git
cd amazing-ai-agents/agents/productivity-agents/ai-exec-email-assistant
```

### Step 2 — Create an isolated environment

A virtual environment keeps this project's packages separate from the rest of your system.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Set up Google OAuth

Follow [`docs/OAUTH_SETUP.md`](docs/OAUTH_SETUP.md) to create OAuth credentials and enable the Gmail API. It takes about 5 minutes. You'll end up with a **Client ID** and **Client Secret**.

### Step 5 — Add your secrets

```bash
cp .env.example .env
```

Open `.env` and fill in three values to start:

```ini
OPENAI_API_KEY=sk-your-key-here
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

You're ready to explore the code.

---

## 5. The Files, Explained

We'll go through the project in the order data actually flows. Each section shows the key code and explains it in plain English.

> The project uses a **layered architecture**: pages (UI) → services (logic) → database (storage). Each layer only talks to the one below it. This is the single most important idea in the whole project.

---

### 5.1 `config/settings.py` — configuration

Everything configurable (API keys, model names, fetch limits) lives in one place, read from environment variables.

```python
@dataclass(frozen=True)
class Settings:
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_transcribe_model: str = "whisper-1"
    openai_tts_model: str = "gpt-4o-mini-tts"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8501"
    max_emails_fetch: int = 50
    enable_voice: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            # ...read each value from the environment...
        )
```

**What's happening:**

- `@dataclass(frozen=True)` makes an immutable settings object — once built, it can't be accidentally changed.
- `from_env()` reads each value from the environment at the moment it's called, so secrets stay out of the code.
- The Google **scopes** (the permissions we request) are also defined here — Gmail read/modify, compose, and basic profile. **No calendar access** — this app is inbox-only.

There's also a small "runtime overrides" layer so you can type your keys into the app's **Settings page** instead of editing `.env`. The takeaway: **config is centralized and never hard-coded.**

---

### 5.2 `database/` — the SQLite cache

Calling Gmail on every page load would be slow. So we cache emails in a local SQLite file.

```python
# database/models.py
@dataclass
class Email:
    id: str
    thread_id: str
    sender: str
    sender_email: str
    subject: str
    snippet: str
    body: str
    is_unread: bool = False
    is_important: bool = False
    needs_followup: bool = False
    ai_summary: str = ""
    priority_score: float = 0.0
```

**What's happening:**

- The `Email` dataclass is our clean, internal shape for an email — much friendlier than Gmail's raw nested JSON.
- Repository functions like `upsert_emails()` and `get_cached_emails()` read and write these to SQLite.
- The dashboard reads from this cache, so it loads instantly; we only hit Gmail when we deliberately fetch.

**Why it matters:** separating "fetch from Gmail" from "read for display" is a classic performance pattern — fetch occasionally, read often.

---

### 5.3 `prompts/templates.py` — the AI's instructions

An LLM is only as good as its instructions. We keep **every prompt in one file** so they're easy to read and tune.

```python
VOICE_INTENT = """You route a spoken command to one assistant action.
Return STRICT JSON only.

Available intents:
- read_inbox
- read_unread
- search_emails (params: {{"query": "<gmail search query>"}})
- summarize_inbox
- followups
- draft_reply (params: {{"target": "<who/what>"}})
- daily_briefing
- unknown

Schema:
{{"intent": "<one of above>", "params": {{}}, "spoken_response": "<one short sentence>"}}

User said: "{transcript}"
"""
```

**What's happening:**

- We give the model a **fixed menu of intents** and force it to answer in **strict JSON**. This turns a fuzzy sentence ("can you check what's unread?") into a structured command (`{"intent": "read_unread"}`) our code can act on.
- The doubled braces `{{ }}` are escaped so Python's `.format()` leaves them alone and only replaces `{transcript}`.

**Key lesson:** when you want an LLM to *control software*, make it return structured data (JSON), not prose.

---

### 5.4 `services/auth_service.py` — Google sign-in

This handles the OAuth 2.0 "Sign in with Google" dance, using the secure **PKCE** flow.

```python
def get_authorization_url() -> tuple[str, str]:
    verifier = _new_code_verifier()                 # a secret we keep
    flow = _build_web_flow(code_verifier=verifier)
    auth_url, state = flow.authorization_url(
        access_type="offline", prompt="consent",
    )
    _save_pkce(state, verifier)                      # remember it for later
    return auth_url, state
```

**What's happening:**

- OAuth lets the user grant our app access to *their* Gmail **without ever giving us their password**. Google issues us a token instead.
- **PKCE** adds a secret "code verifier" we generate at sign-in and prove we own when exchanging the login code for a token. We persist it because Streamlit re-runs the script on the redirect (a subtle but important detail).
- Tokens are cached so users don't sign in every time.

**Don't be intimidated by OAuth** — the pattern is always: send user to Google → Google sends back a code → exchange code for a token → use token to call the API.

---

### 5.5 `services/gmail_service.py` — talking to Gmail

A thin, friendly wrapper around the Gmail API.

```python
class GmailService:
    def __init__(self, credentials):
        self.service = build("gmail", "v1", credentials=credentials)

    def read_inbox(self, max_results: int = 25) -> list[Email]:
        return self._fetch_and_cache("in:inbox", max_results)

    def search(self, query: str, max_results: int = 25) -> list[Email]:
        return self._fetch_and_cache(query, max_results)

    def create_draft(self, to, subject, body, thread_id=None):
        # builds a MIME message and saves it as a Gmail draft
        ...
```

**What's happening:**

- Each public method maps to one user action: `read_inbox`, `read_unread`, `search`, `starred`, `important`, `create_draft`, `send_email`.
- `search()` accepts **Gmail search syntax** (`from:rahul newer_than:7d`) — so the AI can build powerful queries.
- Private helpers (`_parse_message`, `_extract_body`) convert Gmail's messy nested JSON into our clean `Email` objects.

**Safety note:** the app can *create drafts* freely, but `send_email` is only ever triggered by an explicit button — the AI never sends mail on its own.

---

### 5.6 `services/ai_service.py` — the brain

This wraps the OpenAI API and exposes one method per capability.

```python
class AIService:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.aclient = AsyncOpenAI(api_key=self.settings.openai_api_key)

    def summarize_inbox(self, emails: list[Email]) -> str:
        prompt = P.INBOX_SUMMARY.format(emails=_format_emails(emails))
        return self._chat(P.SYSTEM_ASSISTANT, prompt)

    def route_voice_intent(self, transcript: str) -> dict:
        prompt = P.VOICE_INTENT.format(transcript=transcript)
        data = _safe_json(self._chat(P.SYSTEM_ASSISTANT, prompt,
                                     json_mode=True, temperature=0.0))
        data.setdefault("params", {})
        return data
```

**What's happening:**

- `_chat()` is a single helper that sends a system prompt + user prompt to OpenAI and returns the text. Every feature reuses it.
- `route_voice_intent()` uses `json_mode=True` and `temperature=0.0` — we want **deterministic, structured** output, not creativity.
- `_safe_json()` strips stray code fences and safely parses the model's reply, so one malformed response can't crash the app.
- There's also `classify_batch()`, which uses **async** to classify many emails **concurrently** — much faster than one at a time.

**Key lesson:** wrap your AI calls in small, named methods. Your UI should call `ai.summarize_inbox(...)`, never raw OpenAI code.

---

### 5.7 `services/voice_service.py` — speech in, speech out

Two methods: speech-to-text and text-to-speech.

```python
class VoiceService:
    def transcribe(self, audio_bytes: bytes, filename="audio.wav") -> str:
        result = self.client.audio.transcriptions.create(
            model=self.settings.openai_transcribe_model,   # whisper-1
            file=(filename, audio_bytes),
        )
        return result.text

    def synthesize(self, text: str, voice=None) -> bytes | None:
        speech = self.client.audio.speech.create(
            model=self.settings.openai_tts_model,           # gpt-4o-mini-tts
            voice=voice or self.settings.openai_tts_voice,
            input=text,
        )
        return speech.read()
```

**What's happening:**

- `transcribe()` sends recorded audio bytes to **Whisper** and gets text back.
- `synthesize()` does the reverse — turns the assistant's reply into spoken MP3 audio.
- Together they make the app **hands-free**: talk to it, and it talks back.

---

### 5.8 `utils/ui.py` — the glue

Shared UI logic so every page behaves consistently: the auth gate, the service factory, and the sidebar.

```python
def require_auth():
    creds = get_credentials()
    if creds:
        return creds
    # ...otherwise render the "Sign in with Google" screen and stop...

def gmail_service() -> "GmailService":
    from services.gmail_service import GmailService
    creds = require_auth()
    return GmailService(creds)
```

**What's happening:**

- `require_auth()` is called at the top of every page. If the user isn't signed in, it shows the sign-in screen and halts — so no page can be used unauthenticated.
- The service factory functions (`gmail_service()`, `ai_service()`) build services **on demand** with lazy imports. This means a missing optional package won't crash the whole app at startup — only the feature that needs it.
- `render_sidebar()` builds a **custom navigation** with **Voice featured at the top** as the primary control, and hides Streamlit's auto-generated menu.

---

### 5.9 `pages/4_Voice.py` — the star feature

This is where everything comes together. It's the primary way to drive the app.

```python
# 1) Get a command — by voice or by typing
audio = st.audio_input("Speak now")
if audio and st.button("Transcribe & run"):
    transcript = voice.transcribe(audio.getvalue(), "command.wav")

# 2) Ask the AI what the user meant
route = ai.route_voice_intent(transcript)
intent = route.get("intent", "unknown")
params = route.get("params", {})

# 3) Act on the intent
if intent == "read_unread":
    email_list(gmail.read_unread(max_results=20))
elif intent == "search_emails":
    q = params.get("query", transcript)
    email_list(gmail.search(q, max_results=20))
elif intent == "summarize_inbox":
    st.markdown(ai.summarize_inbox(gmail.read_inbox(max_results=20)))
elif intent == "draft_reply":
    thread = gmail.get_thread(gmail.search(params.get("target",""))[0].thread_id)
    st.text_area("Suggested reply", ai.reply_with_context(thread))
# ...and so on
```

**What's happening — the whole loop in one place:**

1. **Capture** a command (microphone or text box).
2. **Transcribe** it to text (Whisper).
3. **Route** it to an intent (the AI returns JSON).
4. **Act** — a simple `if/elif` chain maps each intent to the right `gmail`/`ai` call.
5. (Optionally) **speak** the response back.

This is the canonical "AI agent" pattern: *perceive → decide → act.* Read this file slowly; once it clicks, the whole app makes sense.

---

### 5.10 `app.py` — the entry point

The home dashboard and the file you actually run.

```python
bootstrap()                       # set up logging + database
page_config("Home", "🏠")          # title, icon, inject the theme
render_sidebar()                  # the custom nav

creds = require_auth()            # gate everything behind sign-in
if not creds:
    st.stop()

# Show quick inbox metrics + a grid of features
analytics = analytics_service().compute()
metric_card(c1, analytics.health_score, "Inbox Health")
```

**What's happening:**

- `bootstrap()` runs one-time setup (logging, creating the SQLite tables).
- `page_config()` sets the page title/icon and injects the shared dark theme.
- The auth gate ensures you can't see the dashboard until you've signed in.
- Then it shows a few key metrics and links to every feature.

Running `streamlit run app.py` starts here.

---

## 6. Running It Locally

With your `.env` filled in and dependencies installed:

```bash
streamlit run app.py
```

Then:

1. Open <http://localhost:8501>.
2. Click **Continue with Google** and approve the permissions.
3. Visit the **🎤 Voice** page and try: *"Show my unread emails."*
4. Try the **Inbox**, **AI Assistant**, and **Briefing** pages too.

> If the browser doesn't open automatically, copy the URL from your terminal.

---

## 7. Deploying on Streamlit Cloud

1. **Push to GitHub.** Make sure `.env` is *not* committed (the `.gitignore` already handles this).
2. Go to <https://share.streamlit.io> → **New app**, pick your repo, and set the **Main file path** to this project's `app.py`.
3. In **Advanced settings → Secrets**, add your config in TOML format:

   ```toml
   OPENAI_API_KEY = "sk-..."
   GOOGLE_CLIENT_ID = "xxxx.apps.googleusercontent.com"
   GOOGLE_CLIENT_SECRET = "GOCSPX-..."
   GOOGLE_REDIRECT_URI = "https://your-app-name.streamlit.app/"
   ```

4. In **Google Cloud Console → your OAuth client → Authorized redirect URIs**, add that **exact** URL (with the trailing slash).
5. Click **Deploy**.

> ⚠️ The redirect URI must match **character-for-character** between Streamlit secrets and Google Cloud Console, or sign-in will fail.

---

## 8. Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Error 400: redirect_uri_mismatch` | The redirect URI sent to Google isn't registered | Add the **exact** URL (trailing slash included) under Authorized redirect URIs in Google Cloud Console |
| `redirect_uri` points to `localhost` on a deployed app | Redirect URI still set to the dev default | Set `GOOGLE_REDIRECT_URI` to your live `https://...streamlit.app/` URL in secrets |
| `Missing code verifier` | PKCE secret lost between sign-in and redirect | Don't refresh mid-login; the app persists the verifier — just click **Continue with Google** once and let it complete |
| `Scope has changed...` | Google granted broader scopes than requested | Harmless — the app sets `OAUTHLIB_RELAX_TOKEN_SCOPE`; if you changed scopes, revoke old access and sign in again |
| `ImportError: No module named 'openai'` | Dependencies not installed in that environment | Run `pip install -r requirements.txt`; on Streamlit Cloud, confirm the requirements file is found (check **Settings → Diagnostics**) |
| `OpenAI features unavailable` | Missing or invalid `OPENAI_API_KEY` | Add a valid key in `.env` or the in-app **Settings** page |
| Dashboard is empty | No emails cached yet | Open the **Inbox** page once to fetch and cache mail |

---

## 9. What You Learned

By building this, you now understand:

- ✅ **Layered architecture** — UI → services → database, where each layer has one job.
- ✅ **OAuth 2.0 + PKCE** — how apps access user data securely without passwords.
- ✅ **Calling REST APIs** — wrapping the Gmail API in a clean service.
- ✅ **Practical LLM prompting** — system vs user prompts, and forcing **JSON output** to control software.
- ✅ **Speech-to-text and text-to-speech** — building a hands-free voice loop.
- ✅ **The agent pattern** — perceive (transcribe) → decide (route intent) → act (Gmail).
- ✅ **Async Python** — running many AI calls concurrently for speed.
- ✅ **Caching with SQLite** — fetch occasionally, read often.
- ✅ **Deployment** — shipping a real app to Streamlit Cloud with secrets and OAuth.

That's the core toolkit behind most modern AI applications.

---

## 10. What's Next

Ideas to extend the project and deepen your skills:

- 🗣️ **Always-on voice button** — add a floating "tap to speak" control on every page, not just the Voice page.
- 🧠 **Memory** — let the assistant remember past commands and your preferences across sessions.
- 🏷️ **Auto-labeling** — have the AI apply Gmail labels automatically based on its classification.
- 📅 **Smart scheduling** — re-introduce a calendar integration and let the assistant propose meeting times.
- 🔌 **More providers** — abstract the AI layer so you can swap in other LLM providers behind the same interface.
- 🧪 **Tests** — add unit tests for the services using mocked API responses.
- 🌐 **Multi-language** — Whisper handles many languages; expose a language selector.

Pick one, build it, and you'll cement everything you learned here.

---

<div align="center">

### 🎉 You built an AI assistant!

If this tutorial helped you, please ⭐ the repo and share it.

[![Star](https://img.shields.io/badge/⭐_Star_on_GitHub-amazing--ai--agents-FFD43B?style=for-the-badge&logo=github&logoColor=black)](https://github.com/adityasharmadotai-hash/amazing-ai-agents)

💼 [LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/) &nbsp;•&nbsp; 📺 [YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ) &nbsp;•&nbsp; 🚀 [Apply for U.S. AI jobs](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)

</div>
