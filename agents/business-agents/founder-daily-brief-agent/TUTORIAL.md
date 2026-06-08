<div align="center">

⭐ **[Star the repo](https://github.com/adityasharmadotai-hash/amazing-ai-agents)** &nbsp;·&nbsp;
💼 **[Follow on LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)** &nbsp;·&nbsp;
📺 **[Subscribe on YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)** &nbsp;·&nbsp;
🚀 **[AI Jobs in the U.S. — Apply here](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

</div>

---

# 📘 Tutorial — Build the Founder Daily Brief Agent

A complete, beginner-friendly walkthrough. By the end you'll have an AI dashboard that turns Gmail, Calendar, Notion, Slack, and revenue into one daily founder briefing — running locally and deployed to the web.

> No prior AI experience needed. If you can copy-paste and run a terminal command, you can build this.

---

## 📑 Table of Contents

1. [What We're Building (and Why)](#1-what-were-building-and-why)
2. [How It Works](#2-how-it-works)
3. [Prerequisites Checklist](#3-prerequisites-checklist)
4. [Project Setup](#4-project-setup)
5. [The Files, Explained](#5-the-files-explained)
   - [5.1 requirements.txt](#51-requirementstxt)
   - [5.2 modules/ai.py](#52-modulesaipy--the-openai-wrapper)
   - [5.3 modules/connectors.py](#53-modulesconnectorspy--the-data-layer)
   - [5.4 modules/brief.py](#54-modulesbriefpy--the-ai-brain)
   - [5.5 modules/storage.py](#55-modulesstoragepy--profile--settings)
   - [5.6 app.py](#56-apppy--the-dashboard)
   - [5.7 .streamlit/config.toml](#57-streamlitconfigtoml--the-theme)
6. [Run It Locally](#6-run-it-locally)
7. [Deploy on Streamlit Cloud](#7-deploy-on-streamlit-cloud)
8. [Common Errors & Fixes](#8-common-errors--fixes)
9. [What You Learned](#9-what-you-learned)
10. [What's Next](#10-whats-next)

---

## 1. What We're Building (and Why)

Founders start every day buried in tabs — Gmail, Google Calendar, Notion, Slack, Stripe. The first hour is spent *gathering context* instead of *acting on it*, and the one urgent customer issue is easy to miss.

We're building an **AI executive dashboard** that does the gathering for you. It pulls from every tool, uses AI to surface what matters, and shows a single brief:

```
Good Morning Aditya 👋

Meetings Today: 4   Important Emails: 4   Pending Follow-Ups: 7
Customer Issues: 2  Open Actions: 8       Revenue Yesterday: $1,349

🎯 Suggested Focus:
Finalise the ABC Corp proposal, follow up with Priya & Marcus, and
resolve Northwind's stale-dashboard issue before their board prep.
```

**Two design choices that make this beginner-friendly:**

- **Demo data is seeded automatically** — you see a realistic founder's morning the instant you run it, no API setup needed.
- **Every AI feature has a fallback** — the app works *without* an OpenAI key using simple rules; the key just upgrades the writing to GPT-4o quality.

---

## 2. How It Works

```
   ┌─────────┐  ┌──────────┐  ┌────────┐  ┌────────┐  ┌──────────────┐
   │  Gmail  │  │ Calendar │  │ Notion │  │ Slack  │  │ Stripe/Razor │
   └────┬────┘  └────┬─────┘  └───┬────┘  └───┬────┘  └──────┬───────┘
        │            │            │           │              │
        └────────────┴─────┬──────┴───────────┴──────────────┘
                           ▼
                ┌──────────────────────┐
                │   connectors.py      │  normalise sources + compute scores
                │   collect_context()  │
                └──────────┬───────────┘
                           ▼
                ┌──────────────────────┐
                │      brief.py        │  GPT-4o (or rule-based fallback):
                │  brief · insights ·  │  prioritise · summarise · advise
                │  assistant · prep    │
                └──────────┬───────────┘
                           ▼
                ┌──────────────────────┐
                │       app.py         │  10-page Streamlit dashboard
                └──────────────────────┘
```

**The flow in one sentence:** connectors produce data → `collect_context()` merges it into one snapshot → `brief.py` reasons over it → `app.py` displays it.

---

## 3. Prerequisites Checklist

- [ ] **Python 3.9 or newer** — check with `python --version`
- [ ] **pip** (comes with Python) — check with `pip --version`
- [ ] A code editor (VS Code recommended)
- [ ] A terminal (PowerShell, Terminal, or your editor's built-in)
- [ ] *(Optional)* an **OpenAI API key** from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- [ ] *(Optional, for deploy)* a free [GitHub](https://github.com) + [Streamlit Cloud](https://share.streamlit.io) account

> 🟢 You can complete sections 1–6 with **none** of the optional items.

---

## 4. Project Setup

Create the project folder and files:

```
founder-daily-brief-agent/
├── app.py
├── modules/
│   ├── __init__.py
│   ├── ai.py
│   ├── connectors.py
│   ├── brief.py
│   └── storage.py
├── requirements.txt
├── .env.example
└── .streamlit/
    └── config.toml
```

The `modules/__init__.py` just marks the folder as a Python package — its content can be a single comment:

```python
# modules package — Founder Daily Brief Agent
```

Now let's fill in each file.

---

## 5. The Files, Explained

### 5.1 `requirements.txt`

The Python packages we need.

```txt
streamlit>=1.35.0
openai>=1.30.0
plotly>=5.20.0
python-dotenv>=1.0.0
```

**Plain English:** `streamlit` builds the web UI, `openai` talks to GPT-4o, `plotly` draws charts, and `python-dotenv` reads your API key from a `.env` file.

---

### 5.2 `modules/ai.py` — the OpenAI wrapper

This is the single place that talks to OpenAI. Everything else calls these helpers.

```python
import json, os, re
import streamlit as st

try:
    from openai import OpenAI
except Exception:           # openai not installed yet
    OpenAI = None


def get_key() -> str:
    """Resolve the OpenAI key: user-entered (session) → secrets → env."""
    sk = st.session_state.get("user_api_key", "").strip()
    if sk:
        return sk
    try:
        return st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    except Exception:
        return os.environ.get("OPENAI_API_KEY", "")


def is_configured() -> bool:
    return bool(get_key()) and OpenAI is not None


def _client():
    return OpenAI(api_key=get_key())


def complete(system: str, user: str, tokens: int = 1200, temperature: float = 0.6) -> str:
    """Plain text completion. Raises on failure — callers handle fallback."""
    r = _client().chat.completions.create(
        model="gpt-4o", max_tokens=tokens, temperature=temperature,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
    )
    return r.choices[0].message.content.strip()


def parse_json(text: str):
    """Strip markdown fences and parse JSON."""
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    return json.loads(cleaned)


def complete_json(system: str, user: str, tokens: int = 1500, temperature: float = 0.5):
    return parse_json(complete(system, user, tokens=tokens, temperature=temperature))
```

**Key sections explained:**

- **`get_key()`** looks for your key in three places, in order: what you typed into the Settings page, Streamlit secrets (for deployment), then an environment variable. The first one found wins.
- **`is_configured()`** is the on/off switch the whole app uses — "do we have a working AI key?"
- **`complete()`** sends a *system prompt* (the AI's role) + *user prompt* (the task) to GPT-4o and returns the text.
- **`complete_json()` + `parse_json()`** are for when we want structured data back. GPT sometimes wraps JSON in ```` ```json ```` fences, so we strip those before parsing.

---

### 5.3 `modules/connectors.py` — the data layer

Each business tool is a "connector". For the tutorial, every connector returns realistic **demo data**, so the app works instantly. Later you swap each `_seed_*` function for a real API call.

Here's the structure (full file is in the repo — we show the important parts):

```python
import uuid
from datetime import datetime, timedelta
import streamlit as st


def _id() -> str:
    return str(uuid.uuid4())[:12]

def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _seed_emails(now: datetime) -> list:
    base = now.replace(hour=7, minute=0, second=0, microsecond=0)
    rows = [
        ("Priya Menon", "priya@abccorp.com", "Re: Proposal for ABC Corp — a few questions",
         "Thanks for sending this over. The team loves the direction...",
         True, "high", "Sales", True, False, 2.0),
        ("Daniel Okoye", "daniel@northwindlabs.io", "URGENT: Dashboard is showing stale data",
         "Hey — our analytics dashboard hasn't refreshed since yesterday...",
         True, "high", "Customer", True, True, 0.5),
        # ...more rows...
    ]
    out = []
    for name, email, subj, snip, unread, pri, cat, fu, issue, hrs_ago in rows:
        out.append({
            "id": _id(), "sender": name, "sender_email": email, "subject": subj,
            "snippet": snip, "received": _iso(base - timedelta(hours=hrs_ago)),
            "unread": unread, "priority": pri, "category": cat,
            "needs_followup": fu, "is_issue": issue,
        })
    return out
```

**Why this shape matters:** every email is a dictionary with the same keys. The rest of the app never cares *where* the data came from — only that it has `priority`, `needs_followup`, `is_issue`, etc. That's what makes swapping in real Gmail later painless.

The file has matching `_seed_meetings`, `_seed_tasks`, `_seed_slack`, and `_seed_revenue` functions, plus:

```python
def init_connectors():
    """Seed demo data once per session."""
    now = datetime.now()
    if "seeded" not in st.session_state:
        st.session_state.emails   = _seed_emails(now)
        st.session_state.meetings = _seed_meetings(now)
        st.session_state.tasks    = _seed_tasks(now)
        st.session_state.slack    = _seed_slack(now)
        st.session_state.revenue  = _seed_revenue(now)
        st.session_state.seeded   = True
```

**Plain English:** the first time the app loads, it fills `st.session_state` (Streamlit's per-user memory) with demo data. The `if "seeded" not in ...` guard means it only happens once, so your edits (completing a task, adding revenue) aren't wiped on every click.

Then come the **derived metrics** — small functions that turn raw data into numbers the brief uses:

```python
def revenue_yesterday() -> float:
    yday = (datetime.now() - timedelta(days=1)).date()
    return sum(r["amount"] for r in get_revenue()
               if _safe_dt(r["date"]) and _safe_dt(r["date"]).date() == yday)


def inbox_health_score() -> int:
    unread = len(unread_emails())
    fu     = len(pending_followups())
    issues = len(customer_issues())
    score = 100 - unread * 4 - fu * 5 - issues * 6
    return max(0, min(100, score))          # clamp to 0–100
```

**Plain English:** `inbox_health_score()` starts at 100 and subtracts points for every unread email, pending follow-up, and customer issue — then clamps the result between 0 and 100. Simple rules like this power the dashboard even with no AI key.

Finally, the single function the AI layer consumes:

```python
def collect_context() -> dict:
    """One snapshot of everything, used by the brief / insights / assistant."""
    return {
        "today_meetings":   get_today_meetings(),
        "important_emails": important_emails(),
        "pending_followups": pending_followups(),
        "customer_issues":  customer_issues(),
        "open_tasks":       get_open_tasks(),
        "unanswered_slack": unanswered_slack(),
        "revenue_yesterday": revenue_yesterday(),
        "mrr":              estimated_mrr(),
        "scores": {
            "inbox_health":   inbox_health_score(),
            "productivity":   productivity_score(),
            "task_completion": task_completion_rate(),
            "meeting_load_hours": meeting_load_hours(),
        },
        # ...etc
    }
```

**Why it's powerful:** `collect_context()` is the *one* bridge between "raw data" and "AI". The brief, insights, and assistant all call it — so they automatically stay in sync.

---

### 5.4 `modules/brief.py` — the AI brain

This turns the snapshot into a brief, insights, answers, and meeting prep. The pattern is identical for each: **try AI, fall back to rules.**

```python
import json
from datetime import datetime
from . import ai
from . import connectors as cx


def generate_brief(founder_name: str, ctx: dict) -> dict:
    metrics = {
        "meetings": len(ctx["today_meetings"]),
        "important_emails": len(ctx["important_emails"]),
        "followups": len(ctx["pending_followups"]),
        "customer_issues": len(ctx["customer_issues"]),
        "open_actions": len(ctx["open_tasks"]),
        "revenue_yesterday": ctx["revenue_yesterday"],
    }

    if ai.is_configured():                       # ── AI path ──
        try:
            system = ("You are an elite chief of staff to a startup founder. "
                      "You write crisp, high-signal daily briefings. Return ONLY valid JSON.")
            user = f"""Founder: {founder_name}
Today is {datetime.now().strftime('%A, %B %d, %Y')}.

Snapshot across Gmail, Calendar, Notion, Slack, and revenue:
{_context_for_ai(ctx)}

Return EXACTLY this JSON:
{{
  "summary": "2-3 sentence executive summary.",
  "suggested_focus": "The single most valuable focus today + 1-2 supporting actions.",
  "highlights": ["3-5 short bullets that matter today"],
  "watch_outs": ["1-3 time-sensitive risks"]
}}"""
            data = ai.complete_json(system, user, tokens=900, temperature=0.5)
            data["metrics"]  = metrics
            data["greeting"] = f"{_greeting_word()} {founder_name}"
            data["ai"]       = True
            return data
        except Exception:
            pass                                # fall through on any error

    return _fallback_brief(founder_name, ctx, metrics)   # ── rule-based path ──
```

**Key sections explained:**

- **The metrics dict** is computed in plain Python — these numbers are always correct, AI or not.
- **`if ai.is_configured()`** decides which path to take. If you have a key, it asks GPT-4o to write the narrative as JSON.
- **The prompt** gives GPT a *role* ("chief of staff"), the *data* (`_context_for_ai(ctx)`), and an *exact JSON shape* to return. Asking for a fixed shape is what makes the output reliable to display.
- **`try / except ... pass`** means if the AI call fails (bad key, no internet, rate limit), we silently fall back to rules instead of crashing.

The fallback builds the same fields with simple logic:

```python
def _fallback_brief(founder_name, ctx, metrics):
    hi_tasks = [t for t in ctx["open_tasks"] if t["priority"] == "high"]
    fu       = ctx["pending_followups"]
    focus_bits = []
    if hi_tasks: focus_bits.append(f'Knock out "{hi_tasks[0]["title"]}"')
    if fu:       focus_bits.append(f"follow up with {len(fu)} contacts")
    suggested = ". ".join(focus_bits) + "." if focus_bits else "Clear your inbox and prep for meetings."
    return {
        "greeting": f"{_greeting_word()} {founder_name}",
        "summary": f"You have {metrics['meetings']} meetings, "
                   f"{metrics['important_emails']} important emails...",
        "suggested_focus": suggested,
        "highlights": [...], "watch_outs": [...],
        "metrics": metrics, "ai": False,
    }
```

The same try-AI-then-fallback structure powers `generate_insights()` (priorities/risks/opportunities), `ask()` (the search assistant), and `meeting_prep()` (per-meeting briefings). The **search assistant** is worth a peek:

```python
def ask(question: str, ctx: dict) -> str:
    if ai.is_configured():
        try:
            system = ("You are the founder's executive assistant. Answer ONLY from the "
                      "provided snapshot. Be concise; use bullets when listing.")
            return ai.complete(system, f"Snapshot:\n{_context_for_ai(ctx)}\n\nQuestion: {question}")
        except Exception:
            pass
    return _fallback_answer(question, ctx)     # keyword matching when no key
```

**Plain English:** when you ask "which clients need follow-up?", the assistant is *grounded* — it's told to answer only from your real snapshot, so it won't invent meetings or revenue.

---

### 5.5 `modules/storage.py` — profile & settings

A tiny module holding the founder's identity and connection toggles in session memory.

```python
import streamlit as st


def init_profile():
    defaults = {
        "user_api_key": "",
        "profile": {"founder_name": "Aditya", "company": "Acme Inc.",
                    "role": "Founder & CEO", "currency": "$"},
        "connections": {"Gmail": True, "Google Calendar": True, "Notion": True,
                        "Slack": True, "Stripe": True, "Razorpay": False},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def get_profile() -> dict:
    init_profile()
    return st.session_state.profile


def update_profile(**kwargs):
    init_profile()
    for k, v in kwargs.items():
        if k in st.session_state.profile:
            st.session_state.profile[k] = v
```

**Plain English:** `init_profile()` sets sensible defaults once. `update_profile(founder_name="Sam")` lets the Settings page change them. Storing this in `session_state` means no database is required.

---

### 5.6 `app.py` — the dashboard

This is the UI. It does three things: **apply styles**, **render the sidebar/navigation**, then **render the current page**. Here's the skeleton:

```python
import os, sys
from datetime import datetime, timedelta
import streamlit as st
sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(page_title="Founder Daily Brief", page_icon="☀️", layout="wide")

st.markdown("""<style> ... custom CSS ... </style>""", unsafe_allow_html=True)

from modules import connectors as cx
from modules import brief as bf
from modules import ai
from modules.storage import init_profile, get_profile, update_profile, get_connections, toggle_connection

init_profile()
cx.init_connectors()

if "page" not in st.session_state:
    st.session_state.page = "☀️ Daily Brief"
```

**Key sections explained:**

- **`st.set_page_config(...)`** must be the first Streamlit call — it sets the tab title, icon, and wide layout.
- **The big `st.markdown("<style>...")`** injects CSS for the teal theme, cards, and badges. Streamlit renders raw HTML when `unsafe_allow_html=True`.
- **`init_profile()` + `cx.init_connectors()`** seed defaults and demo data on every run (guarded so they only do real work once).
- **`st.session_state.page`** remembers which page you're on between clicks.

**The sidebar navigation** loops over a list and re-runs the app when you click:

```python
NAV = [("☀️", "Daily Brief"), ("📧", "Inbox"), ("📅", "Calendar"), ("📝", "Notion"),
       ("💬", "Slack"), ("💰", "Revenue"), ("🧠", "AI Insights"), ("📊", "Analytics"),
       ("🔍", "Ask"), ("🔑", "Settings")]

with st.sidebar:
    for icon, label in NAV:
        if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
            st.session_state.page = f"{icon} {label}"
            st.rerun()
```

**Plain English:** Streamlit re-runs the whole script top-to-bottom on every interaction. Clicking a nav button stores the new page name and calls `st.rerun()`, so the matching page block renders.

**Each page** is an `if/elif` block. Here's the Daily Brief page:

```python
page = st.session_state.page

if page == "☀️ Daily Brief":
    prof = get_profile()
    ctx  = cx.collect_context()                      # gather everything

    if st.session_state.get("last_brief") is None:   # generate once, cache it
        st.session_state.last_brief = bf.generate_brief(prof["founder_name"], ctx)
    brief = st.session_state.last_brief
    m = brief["metrics"]

    # 6 headline metric cards
    cols = st.columns(6)
    cards = [("📅", m["meetings"], "Meetings Today", "#0ea5e9"),
             ("📧", m["important_emails"], "Important Emails", "#6366f1"),
             # ...four more...
            ]
    for col, (icon, val, lbl, color) in zip(cols, cards):
        with col:
            st.markdown(f'<div class="metric-card">...{val}...{lbl}...</div>',
                        unsafe_allow_html=True)

    # suggested focus panel
    st.markdown(f'<div>...{brief["suggested_focus"]}...</div>', unsafe_allow_html=True)
```

**Key sections explained:**

- **`ctx = cx.collect_context()`** pulls the unified snapshot.
- **The `last_brief` cache** means we don't call GPT-4o on every click — only the first time, or when you press **🔄 Regenerate** (which clears the cache).
- **`st.columns(6)`** lays out the six metric cards side by side.

The **Ask** page uses Streamlit's chat widgets:

```python
elif page == "🔍 Ask":
    ctx = cx.collect_context()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    question = st.chat_input("Ask anything about your day...")
    if question:
        st.session_state.chat_history.append(("user", question))
        answer = bf.ask(question, ctx)
        st.session_state.chat_history.append(("assistant", answer))

    for role, text in st.session_state.chat_history:
        with st.chat_message(role, avatar="🧑‍💼" if role == "user" else "☀️"):
            st.markdown(text)
```

**Plain English:** `st.chat_input` gives a chat box at the bottom. We store the conversation in `chat_history` and re-draw it on each run with `st.chat_message`.

The remaining pages (Inbox, Calendar, Notion, Slack, Revenue, Insights, Analytics, Settings) follow the same pattern: read from `connectors.py`, optionally call `brief.py`, and render with cards/charts.

---

### 5.7 `.streamlit/config.toml` — the theme

```toml
[theme]
primaryColor = "#0d9488"
backgroundColor = "#f8fafc"
secondaryBackgroundColor = "#ffffff"
textColor = "#0f172a"
font = "sans serif"

[server]
headless = true
```

**Plain English:** this sets the teal accent color and light background app-wide. `headless = true` stops Streamlit from trying to auto-open a browser on servers.

---

## 6. Run It Locally

From the project folder:

```bash
pip install -r requirements.txt
streamlit run app.py
```

A browser opens at `http://localhost:8501`. You'll immediately see the Daily Brief with demo data. Click through every page in the sidebar.

To enable real AI:
1. Get a key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys).
2. Open **🔑 Settings** → paste the key → **Save Key**.
3. Go back to **☀️ Daily Brief** → **🔄 Regenerate**. The brief is now written by GPT-4o.

---

## 7. Deploy on Streamlit Cloud

1. **Push to GitHub.** Create a repo and push your project (don't commit your `.env` — it's git-ignored).
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **New app**.
3. Pick your repo and branch. Set **Main file path** to:
   ```
   agents/business-agents/founder-daily-brief-agent/app.py
   ```
   (or just `app.py` if your repo root *is* the project).
4. Open **Advanced settings → Secrets** and add:
   ```toml
   OPENAI_API_KEY = "sk-your-key"
   ```
5. Click **Deploy**. In ~1 minute you'll get a public URL. 🎉

---

## 8. Common Errors & Fixes

| Error / Symptom | Cause | Fix |
|-----------------|-------|-----|
| `ModuleNotFoundError: No module named 'streamlit'` | Dependencies not installed | Run `pip install -r requirements.txt` |
| `command not found: streamlit` | Streamlit not on PATH | Use `python -m streamlit run app.py` |
| App shows "Running in rule-based mode" | No API key detected | Add your key in **🔑 Settings**, or set `OPENAI_API_KEY` |
| `openai.AuthenticationError` | Invalid/expired key | Generate a new key; ensure it starts with `sk-` |
| `RateLimitError` / quota errors | No OpenAI credits | Add billing at platform.openai.com, or use rule-based mode |
| Brief doesn't update after editing data | It's cached | Press **🔄 Regenerate** on the brief page |
| `OSError: [Errno 28] No space left on device` during install | Disk full | Free up space; Streamlit's deps (pandas/pyarrow) need ~150 MB |
| Edits reset on every click | Expected — data lives in session memory | Use **Reset demo data** in Settings to start fresh |
| Charts don't render | Plotly missing | `pip install plotly` |
| Key visible in code | Hard-coded secret | Never hard-code — use Settings, `.env`, or Streamlit secrets |

---

## 9. What You Learned

By building this you practiced:

- 🏗️ **Structuring a multi-file Python app** with a clean separation: data (`connectors.py`), logic (`brief.py`), UI (`app.py`).
- 🤖 **Calling the OpenAI API** with system/user prompts and getting **structured JSON** back.
- 🛡️ **Graceful degradation** — every AI feature has a deterministic fallback, so the app never hard-depends on a key.
- 🔌 **The connector pattern** — normalising many data sources into one shape so the rest of the app doesn't care where data came from.
- 🎨 **Building a polished Streamlit dashboard** with custom CSS, multi-page navigation, charts, and chat.
- 🔐 **Handling secrets safely** via session state, `.env`, and Streamlit secrets.
- ☁️ **Deploying** a real app to the web.

---

## 10. What's Next

Level it up:

- 🔗 **Wire a real integration.** Start with Gmail: replace `_seed_emails()` in `connectors.py` with the [Gmail API](https://developers.google.com/gmail/api). The rest of the app keeps working.
- 📅 **Add Google Calendar OAuth** so meetings are live.
- 💳 **Connect Stripe** ([Charges API](https://stripe.com/docs/api/charges)) and **Razorpay** for real revenue.
- 💾 **Persist data** in a database (SQLite, Supabase) so it survives restarts.
- 📨 **Email the brief** every morning with a scheduled job (cron / GitHub Actions) + an email API.
- 📱 **Add Slack OAuth** to read real mentions.
- 🧪 **Write tests** for the scoring functions in `connectors.py`.

---

<div align="center">

You built a real AI agent. ☀️ Now go ship it.

⭐ **[Star the repo](https://github.com/adityasharmadotai-hash/amazing-ai-agents)** &nbsp;·&nbsp;
💼 **[LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)** &nbsp;·&nbsp;
📺 **[YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)**

*Built with ❤️ by [Aditya Sharma](https://www.adityasharma.ai)*

</div>
