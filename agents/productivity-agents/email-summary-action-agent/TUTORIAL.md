> ⭐ **Star the repo:** https://github.com/adityasharmadotai-hash/amazing-ai-agents
> 💼 **Follow on LinkedIn:** https://www.linkedin.com/in/aditya-hicounselor/
> 📺 **Subscribe on YouTube:** https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ
> 🚀 **Looking for jobs at top AI companies in the U.S.? [Apply here](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

---

# 🧑‍🏫 Tutorial — Build an Email Summary & Action Items Agent

A complete, beginner-friendly, copy-along guide to building an AI agent that reads your Gmail, summarizes it, extracts action items, prioritizes them, and writes everything to a Google Sheet + a beautiful Streamlit dashboard.

> No prior AI experience needed. If you can run `python` and copy-paste, you can build this.

---

## 📑 Table of Contents

1. [What We Are Building (and Why)](#1-what-we-are-building-and-why)
2. [How It Works (Flow Diagram)](#2-how-it-works-flow-diagram)
3. [Prerequisites Checklist](#3-prerequisites-checklist)
4. [Project Setup](#4-project-setup)
5. [Each File Explained (with full code)](#5-each-file-explained-with-full-code)
   - [requirements.txt](#51-requirementstxt)
   - [.env.example](#52-envexample)
   - [modules/database.py](#53-modulesdatabasepy)
   - [modules/gmail_client.py](#54-modulesgmail_clientpy)
   - [modules/analyzer.py](#55-modulesanalyzerpy)
   - [modules/sheets_client.py](#56-modulessheets_clientpy)
   - [modules/insights.py](#57-modulesinsightspy)
   - [modules/exporter.py](#58-modulesexporterpy)
   - [modules/scheduler.py](#59-modulesschedulerpy)
   - [app.py](#510-apppy)
6. [How to Run Locally](#6-how-to-run-locally)
7. [How to Deploy on Streamlit Cloud](#7-how-to-deploy-on-streamlit-cloud)
8. [Common Errors and Fixes](#8-common-errors-and-fixes)
9. [What You Learned](#9-what-you-learned)
10. [What's Next](#10-whats-next)

---

## 1. What We Are Building (and Why)

**The problem:** Your inbox is noisy. Important asks are buried between newsletters and notifications. You re-read emails, forget follow-ups, and lose time every single morning.

**The solution:** An agent that does the triage *for* you. Every morning it:

- Reads your new Gmail messages,
- Asks an AI model to **summarize**, **extract the action**, and **assign a priority**,
- Detects **due dates** and the **sender**,
- Writes a clean row per email into a **Google Sheet** and a local **SQLite** database,
- Surfaces it all in a **Streamlit dashboard** with metrics, charts, AI insights, and export buttons.

**Why it's a great learning project:** You'll touch OAuth, third-party APIs (Gmail + Sheets), LLM prompting with structured JSON output, a local database, scheduling, and a real UI — the full shape of a production agent, in one repo.

---

## 2. How It Works (Flow Diagram)

```
        ┌──────────────┐
        │   Gmail API  │  inbox / unread / last 24h / labels
        └──────┬───────┘
               │  raw emails
               ▼
        ┌──────────────┐
        │  Email Fetch │  gmail_client.py
        └──────┬───────┘
               │  cleaned messages
               ▼
        ┌──────────────┐      ┌──────────────────┐
        │  AI Analyzer │─────▶│   OpenAI (LLM)   │
        │  analyzer.py │◀─────│  summary +       │
        └──────┬───────┘      │  action +        │
               │              │  priority + dates│
               │              └──────────────────┘
               ▼
   ┌───────────┴────────────┐
   ▼                        ▼
┌────────────┐      ┌────────────────┐
│   SQLite   │      │  Google Sheet  │
│ (history)  │      │  (live output) │
└─────┬──────┘      └────────────────┘
      │
      ▼
┌──────────────────────────────────────┐
│   Streamlit Dashboard                 │
│   cards · charts · filters · insights │
│   export CSV / Excel / PDF            │
└──────────────────────────────────────┘
```

---

## 3. Prerequisites Checklist

Before writing any code, make sure you have:

- [ ] **Python 3.10+** installed → check with `python --version`
- [ ] A **Google account** with Gmail
- [ ] A **Google Cloud project** (free)
- [ ] **Gmail API** and **Google Sheets API** enabled in that project
- [ ] An **OAuth 2.0 Client ID** (Desktop app) → downloaded as `credentials.json`
- [ ] An **OpenAI API key** → from https://platform.openai.com/api-keys
- [ ] A code editor (VS Code recommended)
- [ ] Basic comfort with the terminal

> 💡 You only pay for what you use on OpenAI. Summarizing a few dozen emails costs a few cents.

---

## 4. Project Setup

Create the folder and files:

```bash
mkdir -p email-summary-action-agent/modules
cd email-summary-action-agent
touch app.py requirements.txt .env.example
touch modules/__init__.py modules/database.py modules/gmail_client.py \
      modules/analyzer.py modules/sheets_client.py modules/insights.py \
      modules/exporter.py modules/scheduler.py
```

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

Now let's fill in each file. We'll go **bottom-up**: small helpers first, then the UI that ties them together.

---

## 5. Each File Explained (with full code)

### 5.1 `requirements.txt`

These are all the libraries the project needs.

```txt
streamlit==1.39.0
openai==1.51.0
google-api-python-client==2.147.0
google-auth==2.35.0
google-auth-oauthlib==1.2.1
gspread==6.1.2
pandas==2.2.3
plotly==5.24.1
python-dotenv==1.0.1
APScheduler==3.10.4
openpyxl==3.1.5
reportlab==4.2.5
```

**Plain English:**
- `streamlit` → the web dashboard.
- `openai` → talks to the AI model.
- `google-*` and `gspread` → Gmail + Google Sheets access.
- `pandas` / `plotly` → tables and charts.
- `python-dotenv` → loads secrets from `.env`.
- `APScheduler` → runs the daily job.
- `openpyxl` / `reportlab` → Excel and PDF export.

Install:

```bash
pip install -r requirements.txt
```

---

### 5.2 `.env.example`

A template for your secrets. Copy it to `.env` and fill in real values. **Never commit `.env`.**

```env
# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# Google
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=token.json
GOOGLE_SHEET_NAME=Email Action Items

# App
DB_PATH=email_agent.db
```

**Plain English:** Code reads these names with `os.getenv(...)`. Keeping secrets here (instead of hard-coded) is the #1 rule of a safe project.

---

### 5.3 `modules/database.py`

The local memory of the agent. SQLite is a zero-setup database stored in a single file. We use it to store every analyzed email, track `Pending`/`Completed` status, and — importantly — avoid analyzing the same email twice.

```python
"""SQLite storage for analyzed emails."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime

DB_PATH = "email_agent.db"


@contextmanager
def _conn(db_path: str = DB_PATH):
    """Open a connection and always close it, even on error."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: str = DB_PATH) -> None:
    """Create the table on first run."""
    with _conn(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS emails (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id    TEXT UNIQUE,          -- Gmail message id (dedupe key)
                date        TEXT,
                sender      TEXT,
                subject     TEXT,
                summary     TEXT,
                action_item TEXT,
                priority    TEXT,                 -- High / Medium / Low
                due_date    TEXT,
                status      TEXT DEFAULT 'Pending',
                created_at  TEXT
            )
            """
        )


def already_processed(email_id: str, db_path: str = DB_PATH) -> bool:
    """True if we have already analyzed this Gmail message."""
    with _conn(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM emails WHERE email_id = ?", (email_id,)
        ).fetchone()
        return row is not None


def save_email(record: dict, db_path: str = DB_PATH) -> None:
    """Insert one analyzed email. Ignores duplicates."""
    with _conn(db_path) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO emails
            (email_id, date, sender, subject, summary, action_item,
             priority, due_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.get("email_id"),
                record.get("date"),
                record.get("sender"),
                record.get("subject"),
                record.get("summary"),
                record.get("action_item"),
                record.get("priority"),
                record.get("due_date"),
                record.get("status", "Pending"),
                datetime.utcnow().isoformat(),
            ),
        )


def get_all_emails(db_path: str = DB_PATH) -> list[dict]:
    """Return every stored email, newest first."""
    with _conn(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM emails ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def update_status(row_id: int, status: str, db_path: str = DB_PATH) -> None:
    """Flip an email between Pending and Completed."""
    with _conn(db_path) as conn:
        conn.execute(
            "UPDATE emails SET status = ? WHERE id = ?", (status, row_id)
        )
```

**Key sections explained:**
- `@contextmanager _conn` → guarantees the database connection is committed and closed, so you never leak file handles.
- `email_id TEXT UNIQUE` + `INSERT OR IGNORE` → the dedupe trick. Even if you re-run the agent, the same Gmail message is never stored twice.
- `already_processed()` → lets us skip the (paid) AI call for emails we've seen.

---

### 5.4 `modules/gmail_client.py`

This handles **OAuth login** and **fetching emails**. The first time you run it, a browser opens asking you to approve access; after that, a `token.json` is cached so you don't log in every time.

```python
"""Gmail OAuth + email fetching."""
import base64
import os
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Read-only Gmail access is all we need.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service(
    credentials_file: str = "credentials.json",
    token_file: str = "token.json",
):
    """Authenticate and return a Gmail API client."""
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    # Refresh or run the browser login flow if needed.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _header(headers: list[dict], name: str) -> str:
    """Pull a single header value (e.g. 'From', 'Subject')."""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _extract_body(payload: dict) -> str:
    """Walk the MIME tree and return plain-text body."""
    if payload.get("body", {}).get("data"):
        data = payload["body"]["data"]
        return base64.urlsafe_b64decode(data).decode("utf-8", "ignore")

    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and part["body"].get("data"):
            data = part["body"]["data"]
            return base64.urlsafe_b64decode(data).decode("utf-8", "ignore")
        # Nested multipart
        nested = _extract_body(part)
        if nested:
            return nested
    return ""


def build_query(mode: str = "inbox", label: str | None = None) -> str:
    """Translate a friendly mode into a Gmail search query."""
    if mode == "unread":
        q = "is:unread"
    elif mode == "last_24h":
        after = int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp())
        q = f"after:{after}"
    else:  # inbox
        q = "in:inbox"
    if label:
        q += f" label:{label}"
    return q


def fetch_emails(service, mode: str = "inbox",
                 label: str | None = None, max_results: int = 25) -> list[dict]:
    """Return a list of cleaned email dicts."""
    query = build_query(mode, label)
    resp = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()

    emails = []
    for meta in resp.get("messages", []):
        msg = service.users().messages().get(
            userId="me", id=meta["id"], format="full"
        ).execute()

        headers = msg["payload"]["headers"]
        raw_date = _header(headers, "Date")
        try:
            date = parsedate_to_datetime(raw_date).strftime("%Y-%m-%d %H:%M")
        except Exception:
            date = datetime.utcnow().strftime("%Y-%m-%d %H:%M")

        emails.append({
            "email_id": meta["id"],
            "date": date,
            "sender": _header(headers, "From"),
            "subject": _header(headers, "Subject") or "(no subject)",
            "body": _extract_body(msg["payload"])[:4000],  # cap for the LLM
        })
    return emails


def list_labels(service) -> list[str]:
    """Return the user's Gmail label names."""
    resp = service.users().labels().list(userId="me").execute()
    return [l["name"] for l in resp.get("labels", [])]
```

**Key sections explained:**
- `SCOPES = [...gmail.readonly]` → we only request **read** access. Smallest permission = safest.
- `run_local_server(port=0)` → opens the consent screen in your browser, then caches `token.json`.
- `build_query()` → converts the dropdown choice (`inbox` / `unread` / `last_24h`) into Gmail's search syntax.
- `_extract_body()` → emails are MIME trees; this recursively digs out the plain-text part and decodes the base64.
- `[:4000]` → we truncate the body so we don't send a giant (expensive) prompt to the AI.

---

### 5.5 `modules/analyzer.py`

The brain. It sends each email to OpenAI and asks for **structured JSON** back: summary, action item, priority, and due date. Forcing JSON output makes the result easy to store and display.

```python
"""AI analysis of a single email using OpenAI."""
import asyncio
import json
import os

from openai import AsyncOpenAI, OpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """You are an executive email assistant.
For the email you receive, return STRICT JSON with these keys:
- "summary": one or two sentences, plain and concise.
- "action_item": the single required action for the user, or "No action needed".
- "priority": exactly one of "High", "Medium", "Low".
- "due_date": an ISO date (YYYY-MM-DD) if a deadline is mentioned, else "".

Priority rules:
- High  = requires immediate response or action.
- Medium = can be addressed within a few days.
- Low   = promotions, newsletters, notifications, FYI emails.
Return ONLY the JSON object, nothing else.
"""


def _user_prompt(email: dict) -> str:
    return (
        f"From: {email.get('sender')}\n"
        f"Subject: {email.get('subject')}\n"
        f"Date: {email.get('date')}\n\n"
        f"Body:\n{email.get('body', '')}"
    )


def _safe_parse(content: str) -> dict:
    """Parse the model's JSON, falling back gracefully on failure."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return {
            "summary": content[:200],
            "action_item": "Review manually",
            "priority": "Medium",
            "due_date": "",
        }
    priority = str(data.get("priority", "Medium")).title()
    if priority not in {"High", "Medium", "Low"}:
        priority = "Medium"
    return {
        "summary": data.get("summary", "").strip(),
        "action_item": data.get("action_item", "").strip(),
        "priority": priority,
        "due_date": data.get("due_date", "").strip(),
    }


def analyze_email(email: dict) -> dict:
    """Synchronous analysis of one email."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _user_prompt(email)},
        ],
        temperature=0.2,
    )
    result = _safe_parse(resp.choices[0].message.content)
    return {**email, **result, "status": "Pending"}


async def _analyze_one(client: AsyncOpenAI, email: dict) -> dict:
    resp = await client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _user_prompt(email)},
        ],
        temperature=0.2,
    )
    result = _safe_parse(resp.choices[0].message.content)
    return {**email, **result, "status": "Pending"}


async def analyze_batch(emails: list[dict]) -> list[dict]:
    """Analyze many emails concurrently — much faster for a full inbox."""
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    tasks = [_analyze_one(client, e) for e in emails]
    return await asyncio.gather(*tasks)
```

**Key sections explained:**
- `response_format={"type": "json_object"}` → tells OpenAI to *guarantee* valid JSON, which is the single biggest reliability win.
- `_safe_parse()` → defensive coding. If the model ever returns junk, we still produce a usable row instead of crashing.
- `temperature=0.2` → low randomness, because we want consistent, factual summaries.
- `analyze_batch()` with `asyncio.gather` → this is the **async support** requirement: instead of analyzing emails one-by-one, we fire all requests at once. A 30-email inbox finishes in seconds instead of a minute.

---

### 5.6 `modules/sheets_client.py`

Writes results to a real Google Sheet so non-technical teammates can read them anywhere.

```python
"""Google Sheets output."""
import os

import gspread
from google.oauth2.credentials import Credentials

HEADERS = [
    "Date", "Sender", "Subject", "Email Summary",
    "Action Item", "Priority", "Status",
]
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_sheet(sheet_name: str, token_file: str = "token.json"):
    """Open the sheet by name, creating it (with headers) if missing."""
    creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    client = gspread.authorize(creds)
    try:
        sh = client.open(sheet_name)
    except gspread.SpreadsheetNotFound:
        sh = client.create(sheet_name)
    ws = sh.sheet1
    # Ensure header row exists.
    if ws.row_values(1) != HEADERS:
        ws.update("A1", [HEADERS])
    return ws


def append_rows(ws, records: list[dict]) -> None:
    """Append analyzed emails to the sheet."""
    rows = [
        [
            r.get("date", ""),
            r.get("sender", ""),
            r.get("subject", ""),
            r.get("summary", ""),
            r.get("action_item", ""),
            r.get("priority", ""),
            r.get("status", "Pending"),
        ]
        for r in records
    ]
    if rows:
        ws.append_rows(rows, value_input_option="USER_ENTERED")
```

**Key sections explained:**
- We reuse the same `token.json` from Gmail login, but the **Sheets scope** must also be enabled (we'll add it to the SCOPES used at login — see note in [Common Errors](#8-common-errors-and-fixes)).
- `SpreadsheetNotFound` → first run creates the sheet automatically; later runs reuse it.
- `append_rows(..., USER_ENTERED)` → Google parses dates/numbers as if you typed them, so they format nicely.

---

### 5.7 `modules/insights.py`

Turns the raw rows into **AI insights**: a daily inbox summary, top urgent emails, missed follow-ups, and recommended next actions.

```python
"""High-level AI insights across all analyzed emails."""
import os

from openai import OpenAI


def quick_stats(emails: list[dict]) -> dict:
    """Pure-Python counts for the dashboard cards (no AI cost)."""
    return {
        "total": len(emails),
        "high": sum(e["priority"] == "High" for e in emails),
        "medium": sum(e["priority"] == "Medium" for e in emails),
        "low": sum(e["priority"] == "Low" for e in emails),
        "pending": sum(e["status"] == "Pending" for e in emails),
        "completed": sum(e["status"] == "Completed" for e in emails),
    }


def top_urgent(emails: list[dict], limit: int = 5) -> list[dict]:
    """The most urgent open items."""
    return [
        e for e in emails
        if e["priority"] == "High" and e["status"] == "Pending"
    ][:limit]


def daily_summary(emails: list[dict]) -> str:
    """One paragraph AI overview of the whole inbox."""
    if not emails:
        return "No emails analyzed yet."

    lines = [
        f"- [{e['priority']}] {e['subject']} — {e['action_item']}"
        for e in emails[:40]
    ]
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content":
             "You are a chief-of-staff. Write a short, motivating morning "
             "briefing (4-6 sentences) covering the most urgent items, any "
             "likely missed follow-ups, and recommended next actions."},
            {"role": "user", "content": "\n".join(lines)},
        ],
        temperature=0.4,
    )
    return resp.choices[0].message.content.strip()
```

**Key sections explained:**
- `quick_stats()` is plain Python — instant and free. Use AI only where it adds value.
- `daily_summary()` feeds the model a compact bullet list (not full bodies) to keep it cheap and fast, then asks for a human "morning briefing."

---

### 5.8 `modules/exporter.py`

One function per format: CSV, Excel, PDF. Each returns raw bytes so Streamlit's download button can serve them directly.

```python
"""Export analyzed emails to CSV / Excel / PDF."""
import io

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

COLUMNS = ["date", "sender", "subject", "summary",
           "action_item", "priority", "status"]


def _frame(emails: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(emails)
    cols = [c for c in COLUMNS if c in df.columns]
    return df[cols] if cols else df


def to_csv(emails: list[dict]) -> bytes:
    return _frame(emails).to_csv(index=False).encode("utf-8")


def to_excel(emails: list[dict]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        _frame(emails).to_excel(writer, index=False, sheet_name="Emails")
    return buf.getvalue()


def to_pdf(emails: list[dict]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(letter))
    df = _frame(emails)
    data = [list(df.columns)] + df.astype(str).values.tolist()
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    doc.build([table])
    return buf.getvalue()
```

**Key sections explained:**
- Everything goes through `io.BytesIO()` (an in-memory file) so we never write temp files to disk — perfect for a web app.
- `_frame()` keeps only the columns we care about, in a fixed order.

---

### 5.9 `modules/scheduler.py`

Runs the whole pipeline automatically every morning.

```python
"""Daily automation with APScheduler."""
import asyncio

from apscheduler.schedulers.background import BackgroundScheduler

from . import analyzer, database, gmail_client, sheets_client


def run_pipeline(mode: str = "last_24h", sheet_name: str = "Email Action Items"):
    """Fetch -> skip seen -> analyze -> store -> push to Sheet."""
    database.init_db()
    service = gmail_client.get_gmail_service()
    emails = gmail_client.fetch_emails(service, mode=mode)

    fresh = [e for e in emails if not database.already_processed(e["email_id"])]
    if not fresh:
        return []

    analyzed = asyncio.run(analyzer.analyze_batch(fresh))
    for record in analyzed:
        database.save_email(record)

    ws = sheets_client.get_sheet(sheet_name)
    sheets_client.append_rows(ws, analyzed)
    return analyzed


def start_daily(hour: int = 7, minute: int = 0):
    """Start a background job that runs every morning at HH:MM."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_pipeline, "cron", hour=hour, minute=minute)
    scheduler.start()
    return scheduler
```

**Key sections explained:**
- `run_pipeline()` is the single source of truth — the dashboard's "Analyze" button and the scheduler both call it.
- `already_processed()` filter → only **new** emails cost AI time/money.
- `cron` trigger at 07:00 → that's the "run every morning" requirement.

---

### 5.10 `app.py`

The Streamlit dashboard that ties it all together: connect, analyze, filter, view charts, read AI insights, toggle status, and export.

```python
"""Email Summary & Action Items Agent — Streamlit dashboard."""
import asyncio

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from modules import (analyzer, database, exporter, gmail_client,
                     insights, sheets_client)

load_dotenv()
database.init_db()

st.set_page_config(page_title="Email Action Agent",
                   page_icon="📧", layout="wide")

# ---------- Sidebar: connection & controls ----------
st.sidebar.title("📧 Email Action Agent")
mode = st.sidebar.selectbox("Fetch mode", ["last_24h", "unread", "inbox"])
max_results = st.sidebar.slider("Max emails", 5, 50, 20)

if "service" not in st.session_state:
    st.session_state.service = None

if st.sidebar.button("🔐 Connect Gmail"):
    try:
        st.session_state.service = gmail_client.get_gmail_service()
        st.sidebar.success("Connected!")
    except Exception as e:
        st.sidebar.error(f"Auth failed: {e}")

label = None
if st.session_state.service:
    labels = gmail_client.list_labels(st.session_state.service)
    label = st.sidebar.selectbox("Label (optional)", ["(none)"] + labels)
    label = None if label == "(none)" else label

if st.sidebar.button("⚡ Analyze Emails") and st.session_state.service:
    with st.spinner("Fetching and analyzing..."):
        raw = gmail_client.fetch_emails(
            st.session_state.service, mode=mode,
            label=label, max_results=max_results)
        fresh = [e for e in raw
                 if not database.already_processed(e["email_id"])]
        if fresh:
            analyzed = asyncio.run(analyzer.analyze_batch(fresh))
            for r in analyzed:
                database.save_email(r)
            try:
                ws = sheets_client.get_sheet(
                    st.secrets.get("GOOGLE_SHEET_NAME", "Email Action Items"))
                sheets_client.append_rows(ws, analyzed)
            except Exception as e:
                st.warning(f"Saved locally; Sheets sync skipped: {e}")
        st.success(f"Analyzed {len(fresh)} new emails.")

# ---------- Load data ----------
emails = database.get_all_emails()

st.title("📧 Email Summary & Action Items")

if not emails:
    st.info("Connect Gmail and click **Analyze Emails** to get started.")
    st.stop()

# ---------- Metric cards ----------
stats = insights.quick_stats(emails)
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total", stats["total"])
c2.metric("🔴 High", stats["high"])
c3.metric("🟡 Medium", stats["medium"])
c4.metric("🟢 Low", stats["low"])
c5.metric("⏳ Pending", stats["pending"])
c6.metric("✅ Completed", stats["completed"])

# ---------- AI insights ----------
with st.expander("🧠 Daily AI Briefing", expanded=True):
    if st.button("Generate briefing"):
        st.write(insights.daily_summary(emails))
    st.subheader("🔥 Top urgent")
    for e in insights.top_urgent(emails):
        st.markdown(f"- **{e['subject']}** — {e['action_item']}")

# ---------- Charts ----------
df = pd.DataFrame(emails)
g1, g2 = st.columns(2)
with g1:
    fig = px.pie(df, names="priority", title="Priority distribution",
                 color="priority",
                 color_discrete_map={"High": "#EF4444",
                                     "Medium": "#F59E0B",
                                     "Low": "#10B981"})
    st.plotly_chart(fig, use_container_width=True)
with g2:
    fig2 = px.histogram(df, x="status", title="Status overview", color="status")
    st.plotly_chart(fig2, use_container_width=True)

# ---------- Filters + table ----------
st.subheader("📋 Action Items")
f1, f2 = st.columns(2)
prio = f1.multiselect("Priority", ["High", "Medium", "Low"],
                      default=["High", "Medium", "Low"])
stat = f2.multiselect("Status", ["Pending", "Completed"],
                      default=["Pending", "Completed"])
view = df[df["priority"].isin(prio) & df["status"].isin(stat)]
st.dataframe(view[["date", "sender", "subject", "summary",
                   "action_item", "priority", "status"]],
             use_container_width=True, hide_index=True)

# ---------- Mark complete ----------
with st.expander("✅ Update status"):
    row_id = st.number_input("Email id", min_value=1, step=1)
    new_status = st.selectbox("Status", ["Completed", "Pending"])
    if st.button("Update"):
        database.update_status(int(row_id), new_status)
        st.success("Updated — refresh to see changes.")

# ---------- Export ----------
st.subheader("⬇️ Export")
e1, e2, e3 = st.columns(3)
e1.download_button("CSV", exporter.to_csv(emails), "emails.csv", "text/csv")
e2.download_button("Excel", exporter.to_excel(emails), "emails.xlsx")
e3.download_button("PDF", exporter.to_pdf(emails), "emails.pdf",
                   "application/pdf")
```

**Key sections explained:**
- `st.session_state.service` → keeps your Gmail connection alive across button clicks (Streamlit re-runs the whole script on every interaction).
- The **Analyze** button mirrors `run_pipeline()`: fetch → filter new → `analyze_batch` → save → push to Sheets, with a graceful `try/except` so a Sheets hiccup never loses your local data.
- **Metric cards**, **Plotly charts**, **multiselect filters**, and **download buttons** give you the modern dashboard the spec asked for.

---

## 6. How to Run Locally

```bash
# 1. From the project folder, with venv active:
pip install -r requirements.txt

# 2. Add credentials.json (from Google Cloud) to this folder
# 3. Copy env template and fill it in
cp .env.example .env        # then edit .env

# 4. Launch
streamlit run app.py
```

Then in the browser (`http://localhost:8501`):
1. Click **🔐 Connect Gmail** → approve in the popup.
2. Pick a fetch mode and click **⚡ Analyze Emails**.
3. Watch the cards, charts, and table populate. Check your Google Sheet too!

To run the **daily automation** without the UI:

```python
from modules.scheduler import run_pipeline
run_pipeline(mode="last_24h")
```

---

## 7. How to Deploy on Streamlit Cloud

1. Push your code to a **public or private GitHub repo**.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Pick your repo/branch, set **Main file path** to `app.py`.
4. Under **Advanced settings → Secrets**, paste:

   ```toml
   OPENAI_API_KEY = "sk-..."
   OPENAI_MODEL = "gpt-4o-mini"
   GOOGLE_SHEET_NAME = "Email Action Items"
   ```

5. Click **Deploy**.

> ⚠️ **About Gmail OAuth in the cloud:** the interactive browser login (`run_local_server`) works on your laptop but **not** on a headless server. For production you have two clean options:
> - **Service Account (recommended):** create one in Google Cloud, share the target Google Sheet with its email, and store its JSON in Streamlit secrets. Use it for the **Sheets** side and run the **Gmail fetch + scheduler** on a small always-on machine (your laptop, a Raspberry Pi, or a cheap VM).
> - **Keep Gmail local:** run the analysis locally (where the OAuth popup works), and deploy only the **read-only dashboard** on Streamlit Cloud, pointed at the shared Google Sheet.

---

## 8. Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `FileNotFoundError: credentials.json` | OAuth file missing | Download it from Google Cloud Console → place in project folder |
| `access_denied` during login | App not verified / you're not a test user | Add your email under **OAuth consent screen → Test users** |
| `insufficient permissions` on Sheets | Gmail token lacks Sheets scope | Add the Sheets + Drive scopes to `SCOPES` in `gmail_client.py`, then delete `token.json` and re-login |
| `openai.AuthenticationError` | Bad/missing API key | Check `OPENAI_API_KEY` in `.env` |
| `RateLimitError` | Too many parallel requests | Lower `max_results`, or add a small `asyncio.sleep` between batches |
| Same emails analyzed again | Deleted `email_agent.db` | The DB is the dedupe memory — keep it |
| `JSONDecodeError` | Model returned non-JSON | Already handled by `_safe_parse`; ensure `response_format` is set |
| Streamlit "connection lost" on long runs | Big inbox blocking the UI | Lower `max_results`; async batch already speeds this up |

> 🔑 **The #1 gotcha:** Gmail and Sheets need **different scopes**. When you first log in, the `token.json` only stores the scopes you requested. If you add Sheets later, you must delete `token.json` and authorize again so the new scope is granted.

---

## 9. What You Learned

By finishing this tutorial you now know how to:

- ✅ Authenticate with **Google OAuth** and cache tokens safely
- ✅ Fetch and clean **Gmail messages** (inbox, unread, last 24h, labels)
- ✅ Prompt an **LLM for structured JSON** and parse it defensively
- ✅ Run AI calls **concurrently with `asyncio`** for speed
- ✅ Persist data in **SQLite** and deduplicate work
- ✅ Write results to a live **Google Sheet**
- ✅ Build a **modern Streamlit dashboard** with cards, charts, filters, and exports
- ✅ Schedule a **daily automation** job
- ✅ Generate **AI insights** (briefings, urgent items, next actions)
- ✅ Export to **CSV / Excel / PDF**

That's the complete anatomy of a production AI agent. 🎉

---

## 10. What's Next

Ideas to extend the project:

- 🔔 **Notifications:** post the daily briefing to Slack or Telegram.
- ✍️ **Draft replies:** add a button that drafts a response to each High-priority email.
- 🧩 **Multi-account:** support several Gmail accounts in one dashboard.
- 🗃️ **Vector search:** embed emails and let users ask "what did Finance ask me last week?"
- 📈 **Trends:** chart inbox volume and response time over weeks.
- ☁️ **Full cloud:** move to a Service Account + Cloud Run + Cloud Scheduler for true hands-off automation.
- 🔐 **Encryption:** encrypt the SQLite DB at rest for sensitive inboxes.

---

> ⭐ **Star the repo:** https://github.com/adityasharmadotai-hash/amazing-ai-agents
> 💼 **Follow on LinkedIn:** https://www.linkedin.com/in/aditya-hicounselor/
> 📺 **Subscribe on YouTube:** https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ
> 🚀 **Looking for jobs at top AI companies in the U.S.? [Apply here](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

Happy building! If this helped, please ⭐ the repo and share it.
