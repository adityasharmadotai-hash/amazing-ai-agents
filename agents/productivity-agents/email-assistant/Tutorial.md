# 📘 Personal Email Assistant Agent — Complete Tutorial

This tutorial explains every file, every function, and every design decision in depth.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Application Flow](#2-application-flow)
3. [Gmail & Calendar Integration](#3-gmail--calendar-integration)
4. [Database Design](#4-database-design)
5. [AI Agent — All 12 Functions](#5-ai-agent--all-12-functions)
6. [Demo Mode — Testing Without Gmail](#6-demo-mode--testing-without-gmail)
7. [UI Architecture — 9 Pages](#7-ui-architecture--9-pages)
8. [Prompt Engineering Deep Dive](#8-prompt-engineering-deep-dive)
9. [OAuth 2.0 Flow Explained](#9-oauth-20-flow-explained)
10. [Extending the App](#10-extending-the-app)
11. [Deployment Guide](#11-deployment-guide)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                   PERSONAL EMAIL ASSISTANT AGENT                     │
│                                                                      │
│  INPUT SOURCES          AI LAYER              STORAGE LAYER          │
│  ─────────────          ──────────            ──────────────          │
│  gmail_client.py        agent.py             database.py             │
│  • Gmail API            • summarize_email    • SQLite                │
│  • Calendar API         • suggest_replies    • emails table          │
│  • OAuth 2.0            • classify_priority  • contacts table        │
│  • Email parsing        • meeting_brief      • reminders table       │
│  • Event fetching       • draft_email        • follow_ups table      │
│                         • rewrite_tone       • drafts table          │
│  demo_data.py           • 8 more...          • ai_cache table        │
│  • Test emails                               • analytics table       │
│  • Test contacts                                                     │
│  • Test events                                                       │
│                                                                      │
│  UI LAYER (app.py — 9 pages)                                         │
│  ─────────────────────────────                                       │
│  📬 Inbox  ✨ Triage  📅 Calendar  🧠 Meeting Prep                   │
│  ✍️ Compose  👥 Contacts  ⏰ Reminders  📊 Dashboard  ⚙️ Settings    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Application Flow

```
USER TOGGLES DEMO MODE OFF → connects Gmail
          ↓
    gmail_client.py → OAuth 2.0 flow
    get_oauth_flow() creates Google authorization URL
    User clicks URL → Google auth page → redirected with code
    exchange_code() trades code for access + refresh tokens
    Tokens saved to credentials/google_token.json
          ↓
    gmail_client.fetch_emails()
    Gmail API: messages.list → messages.get (metadata)
    _parse_email() normalizes headers, labels, snippet
    database.upsert_emails() caches to SQLite
          ↓
    app.py renders inbox
    User clicks email → fetch_email_body() for full text
          ↓
    AI Features (on demand, user-triggered):
    agent.summarize_email()     → GPT-4o → 2-3 sentence summary
    agent.classify_priority()   → GPT-4o → critical/high/medium/low
    agent.suggest_replies()     → GPT-4o → 3 reply options
    agent.generate_conversation_context() → GPT-4o → thread analysis
          ↓
    Meeting Prep:
    gmail_client.fetch_upcoming_events() → Calendar API
    Find related emails by attendee email addresses
    agent.prepare_meeting_brief() → GPT-4o → talking points + context
          ↓
    All results cached in SQLite ai_cache table
    Reminders/follow-ups saved to their respective tables
```

---

## 3. Gmail & Calendar Integration

### OAuth 2.0 Scopes

```python
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",    # read emails
    "https://www.googleapis.com/auth/gmail.send",         # send emails
    "https://www.googleapis.com/auth/gmail.modify",       # mark read, star, label
    "https://www.googleapis.com/auth/calendar.readonly",  # read calendar
    "https://www.googleapis.com/auth/contacts.readonly",  # read contacts
]
```

We request minimum necessary scopes. `gmail.modify` is needed to mark-as-read and star messages.

### The Token Refresh Pattern

```python
def load_credentials():
    data = json.loads(TOKEN_PATH.read_text())
    creds = Credentials(token=data["token"], refresh_token=data["refresh_token"], ...)
    
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())   # Google refreshes automatically
        data["token"] = creds.token
        TOKEN_PATH.write_text(json.dumps(data))  # Save refreshed token
    
    return creds
```

Access tokens expire after 1 hour. The refresh token is permanent (until revoked). This pattern silently refreshes without requiring user re-auth.

### Email Parsing

```python
def _parse_email(msg, include_body=False):
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    return {
        "subject": headers.get("Subject", "(no subject)"),
        "from": headers.get("From", ""),
        "is_unread": "UNREAD" in msg.get("labelIds", []),
        "is_important": "IMPORTANT" in msg.get("labelIds", []),
        ...
    }
```

Gmail uses `labelIds` for unread/important/starred status — not header fields. The `UNREAD` label is removed when a message is read; `IMPORTANT` is set by Gmail's auto-prioritization.

### Body Extraction

```python
def _extract_body(payload):
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")
    
    if body_data and mime_type == "text/plain":
        return base64.urlsafe_b64decode(body_data + "==").decode()
    if body_data and mime_type == "text/html":
        text = base64.urlsafe_b64decode(body_data + "==").decode()
        return re.sub(r"<[^>]+>", " ", text)  # Strip HTML tags
    
    for part in payload.get("parts", []):  # Recurse into multipart
        result = _extract_body(part)
        if result: return result
```

Gmail bodies are base64url-encoded. Multipart emails have nested `parts`. We cap at 3000 chars to avoid excessive token usage.

---

## 4. Database Design

### Seven Tables

```sql
emails          -- Cached email metadata + AI classifications
contacts        -- Extracted contact profiles + AI summaries  
reminders       -- User-created email-linked reminders
follow_ups      -- Tracked sent emails awaiting responses
drafts          -- AI-generated or manually saved drafts
ai_cache        -- MD5-keyed cache for AI results
analytics       -- Daily email volume metrics
```

### The AI Cache Pattern

```python
def _cache_key(prefix, content):
    return f"{prefix}:{hashlib.md5(content.encode()).hexdigest()[:12]}"

# Before calling GPT-4o:
key = _cache_key("summary", subject + body[:200])
cached = database.get_cached(key)
if cached: return cached

# After calling:
result = _call(system, user)
database.set_cache(key, result)
```

This avoids re-calling GPT-4o for emails you've already summarized, saving both time and money. The key is a hash of the email content, so if the email changes, a new summary is generated.

### JSON in SQLite

Complex fields like `labels` are stored as JSON strings:
```python
conn.execute("INSERT ... VALUES (?)", (json.dumps(e.get("labels", [])),))
# Reading back:
d["labels"] = json.loads(d.get("labels") or "[]")
```

This avoids a many-to-many `email_labels` table while keeping label data queryable from Python.

---

## 5. AI Agent — All 12 Functions

### The Core Call Pattern

Every function follows the same structure:
```python
def some_feature(input_data) -> str | dict:
    system = "You are an expert in X. Return ONLY valid JSON with: {...}"
    user = f"Input: {input_data}"
    raw = _call(system, user, max_tokens=N, temperature=0.3)
    return _safe_json(raw)  # or raw for text responses
```

### Temperature Guide

| Function | Temp | Why |
|----------|------|-----|
| `classify_priority` | 0.1 | Must be consistent (critical vs high) |
| `rank_priority_inbox` | 0.1 | Batch ranking needs consistency |
| `summarize_email` | 0.3 | Factual, accurate |
| `suggest_replies` | 0.5 | Needs some variety across 3 options |
| `draft_email` | 0.5 | Creative but on-topic |
| `rewrite_tone` | 0.4 | Faithful to original but natural |
| `generate_inbox_insight` | 0.5 | Should sound human and fresh |

### The Priority Classification Prompt

```python
system = """You are an email priority classifier.
Return ONLY valid JSON with:
{
  "priority": "critical|high|medium|low",
  "needs_reply": true/false,
  "urgency_score": 1-10,
  "category": "meeting|task|info|social|marketing|support|other",
  "suggested_action": "reply|forward|archive|schedule|follow-up|none"
}
Critical = immediate action (deadline today, urgent from boss/client).
High = reply within 24h. Medium = this week. Low = informational."""
```

Key design: The enumeration constraints (`critical|high|medium|low`) prevent GPT-4o from inventing new categories like "urgent" or "moderate" that would break the color-coding in the UI.

### Meeting Brief — Most Complex Prompt

```python
system = """You are an executive assistant preparing a meeting brief.
Return ONLY valid JSON with:
{
  "executive_summary": "...",
  "key_context": ["..."],
  "talking_points": ["point 1", "point 2", "point 3"],
  "open_items": ["..."],
  "attendee_notes": [{"person": "email", "role": "...", "note": "..."}],
  "suggested_outcomes": ["..."],
  "prep_checklist": ["..."]
}"""
```

The user message includes the event title, attendees, description, AND up to 5 related emails found by matching attendee email addresses against recent emails. This gives the AI real relationship context.

---

## 6. Demo Mode — Testing Without Gmail

### Why Demo Mode Exists

OAuth requires a Google Cloud project, which takes time to set up. Demo mode lets anyone run and explore the full app in under 30 seconds.

### The Switch Pattern

```python
def use_demo() -> bool:
    return st.session_state.get("use_demo", True)  # On by default

def current_emails() -> list[dict]:
    if use_demo():
        return get_demo_emails()
    # Real Gmail path...
    emails = database.get_emails(limit=100)
    if not emails:
        raw = gmail_client.fetch_emails(max_results=50)
        database.upsert_emails(raw)
        return database.get_emails(limit=100)
    return emails
```

Every page calls `current_emails()` and `current_events()` — they transparently return demo or live data based on the toggle.

### Demo Data Design

Demo emails have pre-set `_ai_priority` and `_ai_category` fields so the triage page works immediately without API calls. Real emails get these fields from `agent.rank_priority_inbox()`.

---

## 7. UI Architecture — 9 Pages

### Page Routing

```python
PAGES = {"📬 Inbox": "inbox", "✨ AI Triage": "triage", ...}

if "page" not in st.session_state:
    st.session_state.page = "inbox"

# In sidebar:
if st.button(label, key=f"nav_{key}"):
    st.session_state.page = key
    st.rerun()

# Router:
page = st.session_state.page
if page == "inbox": ...
if page == "triage": ...
```

Single-file routing keeps deployment simple — no multi-page Streamlit configuration needed.

### The Inbox Two-Panel Layout

```python
col_list, col_viewer = st.columns([2, 3])

with col_list:
    # Email list (left panel)
    for email in filtered:
        if st.button(email["subject"], key=f"email_btn_{email['id']}"):
            st.session_state.selected_email = email
        # HTML card below button (rendered after)
        
with col_viewer:
    sel = st.session_state.get("selected_email")
    # Render email content
```

Clicking an email button stores it in session state. The viewer column reads from session state. This creates the classic email client two-panel UX without any JavaScript.

### CSS Metric Card Fix

Rather than returning HTML strings (which Streamlit can strip outer div tags from), metric cards call `st.markdown()` directly:

```python
def mc(value, label, sub=""):
    st.markdown(f"""
<div class="mc">
  <div class="mc-val">{value}</div>
  <div class="mc-lbl">{label}</div>
</div>""", unsafe_allow_html=True)
```

This guarantees the HTML renders correctly inside Streamlit columns.

---

## 8. Prompt Engineering Deep Dive

### Technique: Strict Enumeration Constraints

Bad:
```
"Classify the priority of this email."
```

Good:
```
"priority must be exactly one of: critical|high|medium|low
 category must be exactly one of: meeting|task|info|social|marketing|support|other"
```

Enumerations prevent creative variation that breaks downstream logic.

### Technique: Role-Specific Persona

```
"You are an executive assistant preparing a meeting brief."
vs.
"Summarize this meeting."
```

The persona activates GPT-4o's understanding of what an executive assistant knows and produces — structured, professional, context-aware output.

### Technique: Context Injection

The meeting prep function injects up to 5 real email snippets from the attendees:

```python
email_context = "\n\n".join([
    f"Email from {e['from']} ({e['date']}):\n{e['snippet']}"
    for e in related_emails[:5]
])
user = f"Meeting: {title}\nAttendees: {attendees}\n\nRelated emails:\n{email_context}"
```

This makes the AI's output specific and grounded — not generic meeting advice, but actual context from real past conversations.

### Technique: The _safe_json() Fallback

```python
def _safe_json(text):
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    try:
        return json.loads(cleaned)
    except:
        match = re.search(r"[\[{].*[\]}]", cleaned, re.DOTALL)
        if match: return json.loads(match.group())
        return {}  # Graceful degradation
```

GPT-4o occasionally wraps JSON in code fences or adds a leading sentence. The regex fallback finds the first valid JSON object/array in the response.

---

## 9. OAuth 2.0 Flow Explained

```
YOUR APP              GOOGLE
─────────             ───────
1. generate auth URL  →  google.com/o/oauth2/auth?client_id=...&scope=...
2. User visits URL
3.                    ←  User approves scopes
4.                    ←  Redirect to your URI with ?code=4/0AX...
5. Extract code
6. exchange_code()    →  oauth2.googleapis.com/token
7.                    ←  {access_token, refresh_token, expires_in}
8. Save tokens to disk
9. load_credentials() reads tokens
10. Tokens injected into API service objects
11. API calls work    →  gmail.googleapis.com/v1/users/me/messages
```

The `refresh_token` is the long-lived credential (never expires unless revoked). The `access_token` expires in 1 hour and is automatically refreshed by `creds.refresh(Request())`.

---

## 10. Extending the App

### Add a new AI feature

1. Add function to `modules/agent.py`:
```python
def your_new_feature(email_body: str) -> dict:
    system = "You are... Return ONLY valid JSON with: {...}"
    raw = _call(system, email_body, max_tokens=500)
    return _safe_json(raw)
```

2. Add a button in `app.py` to call it
3. Display the result in an `ai-card` HTML block

### Add Outlook support

1. Install `msal` (Microsoft Authentication Library)
2. Create `modules/outlook_client.py` with the same interface as `gmail_client.py`
3. In `current_emails()`, check `st.session_state.email_provider` and dispatch accordingly
4. Outlook Graph API endpoint: `https://graph.microsoft.com/v1.0/me/messages`

### Add email threading view

```python
# In gmail_client.py (already exists):
thread = fetch_thread(thread_id)  # Returns list of messages

# In app.py:
if st.button("View Thread"):
    thread = gmail_client.fetch_thread(sel["thread_id"])
    ctx = agent.generate_conversation_context(thread)
    # Display thread messages + AI context
```

### Add Slack notifications for critical emails

```python
import requests

def notify_slack(webhook_url: str, email: dict) -> None:
    payload = {"text": f"🔴 Critical email: *{email['subject']}* from {email['from']}"}
    requests.post(webhook_url, json=payload)

# In AI triage page, after classifying:
if classification["priority"] == "critical" and webhook_url:
    notify_slack(webhook_url, email)
```

---

## 11. Deployment Guide

### Streamlit Community Cloud

1. Push to GitHub (ensure `credentials/`, `data/`, `.env` are in `.gitignore`)
2. [share.streamlit.io](https://share.streamlit.io) → connect repo
3. Secrets:
```toml
OPENAI_API_KEY = "sk-..."
GOOGLE_CLIENT_ID = "..."
GOOGLE_CLIENT_SECRET = "..."
```
4. **Note:** File system is ephemeral — SQLite and OAuth tokens won't persist. Use a cloud DB (Supabase) and store tokens in Streamlit secrets for production.

### Persistent SQLite on Cloud (Fly.io)

```toml
# fly.toml
[mounts]
  source = "email_data"
  destination = "/app/data"
```

```bash
fly launch
fly secrets set OPENAI_API_KEY=sk-...
fly deploy
```

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

---

## 12. Troubleshooting

### Gmail API returns 403
Ensure you've enabled both **Gmail API** and **Google Calendar API** in your Google Cloud project.

### "Token has been expired or revoked"
Delete `credentials/google_token.json` and re-authenticate.

### OAuth redirect_uri mismatch
The redirect URI in Settings must exactly match what's configured in Google Cloud Console (including `http://` vs `https://` and trailing slash).

### AI features say "key not found"
Add your key in Settings → API Keys, or set `OPENAI_API_KEY` in `.env`.

### `_safe_json` returns empty dict
The AI returned malformed JSON. Check the raw response by adding `print(raw)` before `_safe_json(raw)`. Often happens when `max_tokens` is too low and the response is truncated.

### Streamlit widgets reset on each interaction
This is expected — Streamlit re-runs the entire script on any interaction. Use `st.session_state` to persist values across reruns.

---

*Built with ❤️ using Python, Streamlit, OpenAI GPT-4o, and Gmail API*
