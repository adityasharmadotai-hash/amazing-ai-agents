> ⭐ **Star the repo:** https://github.com/adityasharmadotai-hash/amazing-ai-agents
> 💼 **Follow on LinkedIn:** https://www.linkedin.com/in/aditya-hicounselor/
> 📺 **Subscribe on YouTube:** https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ
> 🚀 **Looking for jobs at top AI companies in the U.S.?** [Apply here](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)

---

# 📬 Build an Email Summary & Action Items Agent — Step by Step

A complete, beginner-friendly tutorial. By the end you'll have an AI agent that reads your Gmail, figures out what actually needs doing, and drops it all into a Google Sheet and a slick dashboard. No prior AI experience needed — just basic Python and a willingness to copy-paste carefully.

---

## Table of contents

1. [What we're building (and why)](#1-what-were-building-and-why)
2. [How it works](#2-how-it-works)
3. [Prerequisites checklist](#3-prerequisites-checklist)
4. [Project setup](#4-project-setup)
5. [The code, file by file](#5-the-code-file-by-file)
   - [5.1 `config.py` — one place for all settings](#51-configpy)
   - [5.2 `src/gmail_client.py` — reading your inbox](#52-srcgmail_clientpy)
   - [5.3 `src/ai_analyzer.py` — the AI brain](#53-srcai_analyzerpy)
   - [5.4 `src/database.py` — remembering everything](#54-srcdatabasepy)
   - [5.5 `src/sheets_client.py` — the shareable output](#55-srcsheets_clientpy)
   - [5.6 `src/insights.py` — the daily briefing](#56-srcinsightspy)
   - [5.7 `src/exporter.py` — CSV, Excel, PDF](#57-srcexporterpy)
   - [5.8 `src/pipeline.py` — tying it all together](#58-srcpipelinepy)
   - [5.9 `src/scheduler.py` — run it every morning](#59-srcschedulerpy)
   - [5.10 `app.py` — the dashboard](#510-apppy)
6. [Run it locally](#6-run-it-locally)
7. [Deploy on Streamlit Cloud](#7-deploy-on-streamlit-cloud)
8. [Common errors and fixes](#8-common-errors-and-fixes)
9. [What you learned](#9-what-you-learned)
10. [What's next](#10-whats-next)

---

## 1. What we're building (and why)

**The problem:** Email is a to-do list written by other people, scattered with junk. Finding the three things that actually need a reply means reading everything — and you still might miss a deadline buried in paragraph four.

**The fix:** an agent that does the triage for you. It reads each email and produces:

- a **one-line summary**,
- the **action item** (or "None"),
- a **priority** (High / Medium / Low),
- the **sender** and any **due date**.

Then it writes the results to a Google Sheet, stores them locally so nothing gets analyzed twice, and shows you a dashboard with charts and an AI briefing. You can run it on demand or schedule it every morning.

We're building it the *modular* way — each job lives in its own small file. That's how real production code is organized, and it makes the whole thing easy to understand one piece at a time.

---

## 2. How it works

```text
        ┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌───────────────┐
        │    Gmail    │ ──> │  AI Analyzer │ ──> │    SQLite    │ ──> │ Google Sheet  │
        │  fetch mail │     │  (OpenAI)    │     │  dedup +     │     │  shareable    │
        │             │     │  summarize,  │     │  source of   │     │  output       │
        │             │     │  prioritize  │     │  truth       │     │               │
        └─────────────┘     └──────────────┘     └──────┬───────┘     └───────────────┘
                                                        │
                                                        v
                                            ┌───────────────────────┐
                                            │  Streamlit Dashboard   │
                                            │  cards · charts ·      │
                                            │  insights · export     │
                                            └───────────────────────┘
```

Read it left to right: **Gmail → AI → database → sheet**, with the **dashboard** sitting on top of the database. The `pipeline.py` file is the conveyor belt that moves data through those first four boxes.

---

## 3. Prerequisites checklist

- [ ] **Python 3.10+** installed (`python --version` to check)
- [ ] A **Gmail account** you want to analyze
- [ ] An **OpenAI account** with an API key — [platform.openai.com](https://platform.openai.com/api-keys)
- [ ] A **Google Cloud** account (free) — [console.cloud.google.com](https://console.cloud.google.com/)
- [ ] A code editor (VS Code is great) and a terminal
- [ ] ~30 minutes

You do **not** need to know machine learning. We're *calling* an AI model, not training one.

---

## 4. Project setup

Create the folder structure first. Everything has a home before we write a line of logic.

```bash
mkdir email-action-agent && cd email-action-agent
mkdir src data .streamlit
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
```

Create `requirements.txt`:

```text
streamlit>=1.40.0
openai>=1.40.0
google-api-python-client>=2.140.0
google-auth>=2.34.0
google-auth-oauthlib>=1.2.1
pandas>=2.2.0
plotly>=5.24.0
openpyxl>=3.1.5
reportlab>=4.2.0
python-dotenv>=1.0.1
schedule>=1.2.2
```

Install everything:

```bash
pip install -r requirements.txt
```

Now create `.env.example` (and copy it to `.env`):

```text
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=data/token.json
SHEET_ID=
SHEET_TITLE=Email Action Items
MAX_EMAILS=25
DEFAULT_LABEL=INBOX
DAILY_RUN_TIME=08:00
DB_PATH=data/emails.db
```

```bash
cp .env.example .env   # then paste your real OpenAI key into .env
```

> 🔑 **Getting `credentials.json`:** In Google Cloud Console, create a project, enable the **Gmail API** and **Google Sheets API**, set up the OAuth consent screen (External, add yourself as a test user), then create an **OAuth client ID → Desktop app**. Download the JSON, rename it `credentials.json`, and put it in the project root. We'll use it in step 5.2.

Finally, a `.gitignore` so you never commit secrets:

```text
.env
credentials.json
data/token.json
data/*.db
__pycache__/
venv/
```

---

## 5. The code, file by file

We'll go in dependency order — the simplest, most-depended-on files first.

### 5.1 `config.py`

**Plain English:** This is the settings drawer. Instead of hardcoding the model name or file paths in ten different files, we put them *here* and read them everywhere. It also pulls secrets from your `.env` file so they never live in code.

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Project paths ---
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", str(BASE_DIR / "credentials.json"))
TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", str(DATA_DIR / "token.json"))
DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "emails.db"))

# --- Google API scopes (what we're allowed to touch) ---
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

# --- OpenAI ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# --- Google Sheet ---
SHEET_ID = os.getenv("SHEET_ID", "")
SHEET_TITLE = os.getenv("SHEET_TITLE", "Email Action Items")
SHEET_TAB = "Inbox Actions"
SHEET_HEADERS = ["Date", "Sender", "Subject", "Email Summary",
                 "Action Item", "Priority", "Due Date", "Status"]

# --- Fetching defaults ---
DEFAULT_MAX_EMAILS = int(os.getenv("MAX_EMAILS", "25"))
DEFAULT_LABEL = os.getenv("DEFAULT_LABEL", "INBOX")

PRIORITIES = ["High", "Medium", "Low"]
STATUSES = ["Pending", "Completed"]
```

**Key sections explained:**
- `load_dotenv()` reads your `.env` file into environment variables.
- `SCOPES` is the *permission list* — `gmail.readonly` means we can read but never send or delete mail. Always ask for the least access you need.
- Everything uses `os.getenv("NAME", "default")`, so the app still runs with sensible defaults even if you forget a setting.

---

### 5.2 `src/gmail_client.py`

**Plain English:** This file logs into Gmail and hands back clean email dictionaries. The Gmail API returns deeply nested, base64-encoded payloads — nobody wants to deal with that. This wrapper does the ugly parsing once so the rest of the app gets tidy `{sender, subject, body, date}` objects.

```python
from __future__ import annotations
import base64, os, time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import config


def get_credentials() -> Credentials:
    """Run OAuth (or refresh a saved token) and return credentials."""
    creds = None
    if os.path.exists(config.TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(config.TOKEN_FILE, config.SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config.CREDENTIALS_FILE, config.SCOPES)
            creds = flow.run_local_server(port=0)
        with open(config.TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds


class GmailClient:
    def __init__(self, creds: Optional[Credentials] = None):
        self.creds = creds or get_credentials()
        self.service = build("gmail", "v1", credentials=self.creds)

    def list_labels(self) -> list[dict]:
        return self.service.users().labels().list(userId="me").execute().get("labels", [])

    def fetch_emails(self, max_results=config.DEFAULT_MAX_EMAILS, label=config.DEFAULT_LABEL,
                     unread_only=False, last_hours=None) -> list[dict]:
        query_parts = []
        if unread_only:
            query_parts.append("is:unread")
        if last_hours:
            after = int(time.time()) - last_hours * 3600
            query_parts.append(f"after:{after}")
        query = " ".join(query_parts)

        listing = self.service.users().messages().list(
            userId="me", labelIds=[label] if label else None,
            q=query or None, maxResults=max_results).execute()

        emails = []
        for msg in listing.get("messages", []):
            try:
                emails.append(self._get_message(msg["id"]))
            except Exception as exc:
                print(f"[gmail] skipping {msg['id']}: {exc}")
        return emails

    def _get_message(self, message_id: str) -> dict:
        msg = self.service.users().messages().get(
            userId="me", id=message_id, format="full").execute()
        headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
        return {
            "id": message_id,
            "sender": headers.get("from", "Unknown"),
            "subject": headers.get("subject", "(no subject)"),
            "date": self._parse_date(headers.get("date")),
            "snippet": msg.get("snippet", ""),
            "body": self._extract_body(msg["payload"]),
        }

    @staticmethod
    def _parse_date(raw):
        if not raw:
            return datetime.now(timezone.utc).isoformat()
        try:
            return parsedate_to_datetime(raw).isoformat()
        except Exception:
            return datetime.now(timezone.utc).isoformat()

    def _extract_body(self, payload: dict) -> str:
        if payload.get("body", {}).get("data"):
            return self._decode(payload["body"]["data"])
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                return self._decode(part["body"]["data"])
            if part.get("parts"):
                nested = self._extract_body(part)
                if nested:
                    return nested
        return ""

    @staticmethod
    def _decode(data: str) -> str:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
```

**Key sections explained:**
- **`get_credentials()`** is the OAuth dance. The *first* run opens your browser and asks permission; it then saves a `token.json`. Every run after that just loads (and silently refreshes) that token — no more browser pop-ups.
- **`fetch_emails()`** builds a Gmail *search query*. `is:unread` and `after:<timestamp>` are the same operators you'd type in the Gmail search bar. That's how we support "unread only" and "last 24 hours" with one method.
- **`_extract_body()`** is recursive because emails are nested (an email can contain parts, which contain parts…). We walk the tree until we find the plain-text version.
- Notice the `try/except` around each message — **one broken email never crashes the whole scan.**

---

### 5.3 `src/ai_analyzer.py`

**Plain English:** This is the brain. It sends one email to OpenAI and asks for strict JSON back: summary, action item, priority, due date. The priority *rules* live in the system prompt, so the model knows that a newsletter is Low and a "need this by Friday" is High. It also analyzes emails **concurrently** so a 25-email inbox finishes in seconds.

```python
from __future__ import annotations
import asyncio, json
from typing import Optional
from openai import AsyncOpenAI, OpenAI
import config

SYSTEM_PROMPT = """You are an executive assistant that triages email.
For the email you are given, respond with ONLY a JSON object with exactly these keys:
  "summary":     a 1-2 sentence plain-English summary
  "action_item": the single concrete action required, or "None"
  "priority":    one of "High", "Medium", "Low"
  "due_date":    an ISO date (YYYY-MM-DD) if a deadline is mentioned, else ""

Priority rules (follow strictly):
  High   = requires an immediate response or action
  Medium = can be addressed within a few days
  Low    = promotions, newsletters, notifications, receipts, FYI emails
"""


def _build_user_prompt(email: dict) -> str:
    body = (email.get("body") or email.get("snippet") or "")[:6000]
    return (f"From: {email.get('sender','Unknown')}\n"
            f"Subject: {email.get('subject','')}\n"
            f"Date: {email.get('date','')}\n\nBody:\n{body}")


def _safe_parse(content: str) -> dict:
    """Parse model output defensively, stripping stray code fences."""
    cleaned = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return {"summary": cleaned[:300] or "Could not analyze.",
                "action_item": "None", "priority": "Low", "due_date": ""}
    priority = str(data.get("priority", "Low")).title()
    if priority not in config.PRIORITIES:
        priority = "Low"
    return {"summary": str(data.get("summary", "")).strip(),
            "action_item": str(data.get("action_item", "None")).strip() or "None",
            "priority": priority,
            "due_date": str(data.get("due_date", "")).strip()}


class AIAnalyzer:
    def __init__(self, api_key=None, model=None):
        key = api_key or config.OPENAI_API_KEY
        if not key:
            raise ValueError("OPENAI_API_KEY is not set. Add it to your .env file.")
        self.model = model or config.OPENAI_MODEL
        self.client = OpenAI(api_key=key)
        self.async_client = AsyncOpenAI(api_key=key)

    def analyze(self, email: dict) -> dict:
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": SYSTEM_PROMPT},
                          {"role": "user", "content": _build_user_prompt(email)}],
                temperature=0.2,
                response_format={"type": "json_object"})
            return _safe_parse(resp.choices[0].message.content)
        except Exception as exc:
            return {"summary": f"Analysis failed: {exc}", "action_item": "None",
                    "priority": "Low", "due_date": ""}

    async def _analyze_async(self, email, sem):
        async with sem:
            try:
                resp = await self.async_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT},
                              {"role": "user", "content": _build_user_prompt(email)}],
                    temperature=0.2,
                    response_format={"type": "json_object"})
                return _safe_parse(resp.choices[0].message.content)
            except Exception as exc:
                return {"summary": f"Analysis failed: {exc}", "action_item": "None",
                        "priority": "Low", "due_date": ""}

    async def analyze_many(self, emails, concurrency=5):
        sem = asyncio.Semaphore(concurrency)
        analyses = await asyncio.gather(*[self._analyze_async(e, sem) for e in emails])
        return [{**email, **analysis} for email, analysis in zip(emails, analyses)]
```

**Key sections explained:**
- **The system prompt is the product.** The quality of your triage depends almost entirely on how clearly you describe the rules here. Notice we *spell out* what High/Medium/Low mean rather than hoping the model guesses.
- **`response_format={"type": "json_object"}`** tells OpenAI to return valid JSON. We still call `_safe_parse()` as a seatbelt — if the model ever returns junk, we fall back to a safe "Low" instead of crashing.
- **`analyze_many()`** uses `asyncio.gather` with a `Semaphore(5)`. Translation: fire off up to 5 requests at once instead of waiting for each one in turn. That's the difference between a 5-second scan and a 60-second scan.
- **`{**email, **analysis}`** merges the original email fields with the AI fields into one combined record.

---

### 5.4 `src/database.py`

**Plain English:** SQLite is a tiny database that lives in a single file — no server to install. We use it for three things: (1) never analyze the same email twice, (2) power the dashboard counters with fast queries, (3) track which action items are done. The Google Sheet is the *shareable* copy; this is the *source of truth*.

```python
from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from typing import Iterator, Optional
import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS emails (
    id TEXT PRIMARY KEY, date TEXT, sender TEXT, subject TEXT,
    summary TEXT, action_item TEXT, priority TEXT, due_date TEXT,
    status TEXT DEFAULT 'Pending', created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS app_meta (key TEXT PRIMARY KEY, value TEXT);
"""

@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:
    con = sqlite3.connect(config.DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()

def init_db():
    with _conn() as con:
        con.executescript(SCHEMA)

def email_exists(email_id: str) -> bool:
    with _conn() as con:
        return con.execute("SELECT 1 FROM emails WHERE id = ?", (email_id,)).fetchone() is not None

def insert_email(record: dict) -> bool:
    if email_exists(record["id"]):
        return False
    with _conn() as con:
        con.execute("""INSERT INTO emails
            (id, date, sender, subject, summary, action_item, priority, due_date, status)
            VALUES (:id,:date,:sender,:subject,:summary,:action_item,:priority,:due_date,:status)""",
            {"id": record["id"], "date": record.get("date",""), "sender": record.get("sender",""),
             "subject": record.get("subject",""), "summary": record.get("summary",""),
             "action_item": record.get("action_item","None"), "priority": record.get("priority","Low"),
             "due_date": record.get("due_date",""), "status": record.get("status","Pending")})
    return True

def get_all_emails(priority=None, status=None) -> list[dict]:
    query, params = "SELECT * FROM emails WHERE 1=1", []
    if priority and priority != "All":
        query += " AND priority = ?"; params.append(priority)
    if status and status != "All":
        query += " AND status = ?"; params.append(status)
    query += " ORDER BY date DESC"
    with _conn() as con:
        return [dict(r) for r in con.execute(query, params).fetchall()]

def update_status(email_id: str, status: str):
    with _conn() as con:
        con.execute("UPDATE emails SET status = ? WHERE id = ?", (status, email_id))

def get_stats() -> dict:
    with _conn() as con:
        total = con.execute("SELECT COUNT(*) FROM emails").fetchone()[0]
        by_priority = {r["priority"]: r["n"] for r in con.execute(
            "SELECT priority, COUNT(*) n FROM emails GROUP BY priority").fetchall()}
        by_status = {r["status"]: r["n"] for r in con.execute(
            "SELECT status, COUNT(*) n FROM emails GROUP BY status").fetchall()}
    return {"total": total, "high": by_priority.get("High",0), "medium": by_priority.get("Medium",0),
            "low": by_priority.get("Low",0), "pending": by_status.get("Pending",0),
            "completed": by_status.get("Completed",0)}

def set_meta(key: str, value: str):
    with _conn() as con:
        con.execute("INSERT INTO app_meta (key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))

def get_meta(key: str) -> Optional[str]:
    with _conn() as con:
        row = con.execute("SELECT value FROM app_meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None
```

**Key sections explained:**
- **`id TEXT PRIMARY KEY`** uses Gmail's own message ID as the key. Because a primary key must be unique, the database itself guarantees we can't store the same email twice. `email_exists()` lets us check *before* spending an OpenAI call.
- **The `@contextmanager` `_conn()`** opens a connection, commits, and closes it automatically. You never leak a connection or forget to commit.
- **Parameterized queries** (`?` and `:name`) — never f-string user data into SQL. This is your defense against SQL injection.
- **`app_meta`** is a little key/value scratchpad where we stash the created Sheet's ID and the timestamp of the last run.

---

### 5.5 `src/sheets_client.py`

**Plain English:** This creates your Google Sheet the first time, writes the header row, remembers the Sheet's ID in the database, and then *appends* new rows every run after that. The Sheet is what you share with a teammate or open on your phone.

```python
from __future__ import annotations
from typing import Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import config
from src import database

class SheetsClient:
    def __init__(self, creds: Credentials):
        self.creds = creds
        self.service = build("sheets", "v4", credentials=creds)

    def get_or_create_sheet(self) -> str:
        sheet_id = config.SHEET_ID or database.get_meta("sheet_id")
        if sheet_id:
            return sheet_id
        spreadsheet = self.service.spreadsheets().create(
            body={"properties": {"title": config.SHEET_TITLE},
                  "sheets": [{"properties": {"title": config.SHEET_TAB}}]},
            fields="spreadsheetId").execute()
        sheet_id = spreadsheet["spreadsheetId"]
        database.set_meta("sheet_id", sheet_id)
        self._write_headers(sheet_id)
        return sheet_id

    def _write_headers(self, sheet_id: str):
        self.service.spreadsheets().values().update(
            spreadsheetId=sheet_id, range=f"{config.SHEET_TAB}!A1",
            valueInputOption="RAW", body={"values": [config.SHEET_HEADERS]}).execute()

    def append_rows(self, records: list[dict]) -> int:
        if not records:
            return 0
        sheet_id = self.get_or_create_sheet()
        rows = [[r.get("date",""), r.get("sender",""), r.get("subject",""), r.get("summary",""),
                 r.get("action_item","None"), r.get("priority","Low"),
                 r.get("due_date",""), r.get("status","Pending")] for r in records]
        self.service.spreadsheets().values().append(
            spreadsheetId=sheet_id, range=f"{config.SHEET_TAB}!A1",
            valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS",
            body={"values": rows}).execute()
        return len(rows)

    def sheet_url(self, sheet_id: Optional[str] = None) -> str:
        sheet_id = sheet_id or self.get_or_create_sheet()
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}"
```

**Key sections explained:**
- **`get_or_create_sheet()`** checks three places for an existing Sheet ID (your `.env`, then the database) before creating a new one. That's why running the app daily keeps appending to the *same* sheet instead of spawning dozens.
- **`append`** with `insertDataOption="INSERT_ROWS"` adds to the bottom without overwriting anything.
- **`valueInputOption="USER_ENTERED"`** means Google parses dates and numbers like a human typed them, so your Date column behaves like real dates.

---

### 5.6 `src/insights.py`

**Plain English:** Per-email analysis tells you about *one* email. This file zooms out and looks at the *whole* inbox at once — one OpenAI call that returns a daily briefing: a summary, the top urgent items, likely missed follow-ups, and recommended next actions.

```python
from __future__ import annotations
import json
from typing import Optional
from openai import OpenAI
import config
from src import database

INSIGHTS_PROMPT = """You are a chief-of-staff reviewing a person's analyzed inbox.
Given the JSON list of emails, respond with ONLY a JSON object with these keys:
  "daily_summary":      2-3 sentences on the state of the inbox today
  "top_urgent":         array of up to 5 strings, each "Sender — short reason"
  "missed_followups":   array of strings for items that look overdue or stale
  "recommended_actions": array of up to 5 short imperative next steps
Be specific and concise. If a section has nothing, return an empty array.
"""

class InsightsEngine:
    def __init__(self, api_key=None, model=None):
        self.client = OpenAI(api_key=api_key or config.OPENAI_API_KEY)
        self.model = model or config.OPENAI_MODEL

    def generate(self) -> dict:
        emails = database.get_all_emails()
        if not emails:
            return {"daily_summary": "No emails analyzed yet. Run a scan to get started.",
                    "top_urgent": [], "missed_followups": [], "recommended_actions": []}
        compact = [{"sender": e["sender"], "subject": e["subject"], "summary": e["summary"],
                    "action_item": e["action_item"], "priority": e["priority"],
                    "due_date": e["due_date"], "status": e["status"]} for e in emails[:60]]
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": INSIGHTS_PROMPT},
                          {"role": "user", "content": json.dumps(compact)}],
                temperature=0.3, response_format={"type": "json_object"})
            return json.loads(resp.choices[0].message.content)
        except Exception as exc:
            return {"daily_summary": f"Could not generate insights: {exc}",
                    "top_urgent": [], "missed_followups": [], "recommended_actions": []}
```

**Key sections explained:**
- We **read from SQLite, not Gmail** — the data's already analyzed, so insights cost exactly one API call no matter how big your inbox is.
- We send a **`compact`** version of each row and cap it at 60 emails to keep the prompt small and cheap.
- Same defensive pattern: empty inbox → a friendly message; an error → a safe empty result instead of a crash.

---

### 5.7 `src/exporter.py`

**Plain English:** Three functions that turn your data into a downloadable CSV, Excel file, or PDF. Each returns raw bytes so Streamlit's download button can serve them directly — no temp files on disk.

```python
from __future__ import annotations
import io
import pandas as pd
from src import database

EXPORT_COLUMNS = ["date","sender","subject","summary","action_item","priority","due_date","status"]
PRETTY = {"date":"Date","sender":"Sender","subject":"Subject","summary":"Email Summary",
          "action_item":"Action Item","priority":"Priority","due_date":"Due Date","status":"Status"}

def _frame() -> pd.DataFrame:
    df = pd.DataFrame(database.get_all_emails())
    if df.empty:
        df = pd.DataFrame(columns=EXPORT_COLUMNS)
    df = df[[c for c in EXPORT_COLUMNS if c in df.columns]]
    return df.rename(columns=PRETTY)

def to_csv() -> bytes:
    return _frame().to_csv(index=False).encode("utf-8")

def to_excel() -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        _frame().to_excel(writer, index=False, sheet_name="Action Items")
    return buf.getvalue()

def to_pdf() -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    df = _frame()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), title="Email Action Items")
    styles = getSampleStyleSheet()
    elements = [Paragraph("Email Summary & Action Items", styles["Title"]), Spacer(1, 12)]
    cols = [c for c in ["Date","Sender","Subject","Action Item","Priority","Status"] if c in df.columns]
    data = [cols] + [[str(row.get(c,""))[:60] for c in cols] for _, row in df.iterrows()]
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#4F46E5")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTSIZE",(0,0),(-1,-1),8),
        ("GRID",(0,0),(-1,-1),0.25,colors.grey),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#F3F4F6")]),
        ("VALIGN",(0,0),(-1,-1),"TOP")]))
    elements.append(table)
    doc.build(elements)
    return buf.getvalue()
```

**Key sections explained:**
- **`_frame()`** is shared by all three exporters — pull from the DB once, rename columns to pretty labels, done. (DRY: Don't Repeat Yourself.)
- **`io.BytesIO()`** is an in-memory file. We write the Excel/PDF into it and hand back the bytes — nothing touches your disk.
- The PDF trims long fields to 60 characters so the table stays readable on a landscape page.

---

### 5.8 `src/pipeline.py`

**Plain English:** The conductor. It runs the whole flow in order — fetch from Gmail, skip what we've seen, analyze the rest, save to SQLite, mirror to the Sheet — and returns a tiny report. Both the dashboard button *and* the daily scheduler call this exact function, so they can never behave differently.

```python
from __future__ import annotations
import asyncio
from typing import Optional
import config
from src import database
from src.ai_analyzer import AIAnalyzer
from src.gmail_client import GmailClient, get_credentials
from src.sheets_client import SheetsClient

def run_pipeline(max_emails=config.DEFAULT_MAX_EMAILS, label=config.DEFAULT_LABEL,
                 unread_only=False, last_hours=None, push_to_sheet=True) -> dict:
    database.init_db()
    creds = get_credentials()

    # 1. Fetch
    emails = GmailClient(creds).fetch_emails(
        max_results=max_emails, label=label, unread_only=unread_only, last_hours=last_hours)

    # 2. Skip anything already analyzed (cheap dedupe BEFORE paying OpenAI)
    fresh = [e for e in emails if not database.email_exists(e["id"])]
    if not fresh:
        return {"fetched": len(emails), "new": 0, "written_to_sheet": 0}

    # 3. Analyze concurrently
    analyzed = asyncio.run(AIAnalyzer().analyze_many(fresh))

    # 4. Persist locally
    saved = []
    for record in analyzed:
        record["status"] = "Pending"
        if database.insert_email(record):
            saved.append(record)

    # 5. Mirror to Google Sheet
    written = 0
    if push_to_sheet and saved:
        written = SheetsClient(creds).append_rows(saved)

    database.set_meta("last_run", _now())
    return {"fetched": len(emails), "new": len(saved), "written_to_sheet": written}

def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

if __name__ == "__main__":
    print(f"Daily run complete: {run_pipeline(last_hours=24)}")
```

**Key sections explained:**
- The **numbered comments** *are* the flow diagram in code form. Read them top to bottom and you understand the whole app.
- **Dedup happens at step 2, before step 3.** That ordering is deliberate — it means you only ever pay OpenAI for genuinely new emails.
- The **`if __name__ == "__main__"`** block lets you run `python -m src.pipeline` directly from cron. One file, two entry points.

---

### 5.9 `src/scheduler.py`

**Plain English:** Want it to run by itself every morning? This keeps a small process alive and triggers the pipeline at a set time. (For production, a system cron job calling `python -m src.pipeline` is usually more reliable — but this is the simplest thing that works.)

```python
from __future__ import annotations
import os, time
import schedule
from src.pipeline import run_pipeline

RUN_AT = os.getenv("DAILY_RUN_TIME", "08:00")  # 24h local time

def job():
    print("[scheduler] running daily pipeline...")
    print(f"[scheduler] done: {run_pipeline(last_hours=24)}")

def main():
    schedule.every().day.at(RUN_AT).do(job)
    print(f"[scheduler] started. Runs daily at {RUN_AT}. Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()
```

**Key sections explained:**
- `schedule.every().day.at("08:00")` reads almost like English.
- The `while True` loop checks every 30 seconds whether it's time to run. The OS keeps the process alive; the loop keeps it watching the clock.

---

### 5.10 `app.py`

**Plain English:** The dashboard you actually look at. Sidebar = controls (what to scan + export buttons). Main area = analytics cards, two charts, the AI briefing, and a filterable table where you can flip an item to "Completed." Run it with `streamlit run app.py`.

```python
from __future__ import annotations
import pandas as pd
import plotly.express as px
import streamlit as st
import config
from src import database, exporter
from src.insights import InsightsEngine
from src.pipeline import run_pipeline

st.set_page_config(page_title="Email Action Agent", page_icon="📬", layout="wide")
database.init_db()

st.markdown("""<style>
.metric-card{background:linear-gradient(135deg,#4F46E5,#7C3AED);padding:1.1rem 1.3rem;
border-radius:14px;color:white;} .metric-card h2{margin:0;font-size:2rem;}
.metric-card p{margin:0;opacity:.85;font-size:.85rem;}</style>""", unsafe_allow_html=True)

def card(label, value, gradient):
    return (f'<div class="metric-card" style="background:{gradient}">'
            f'<h2>{value}</h2><p>{label}</p></div>')

# --- sidebar: scan controls ---
st.sidebar.title("📬 Email Action Agent")
scope = st.sidebar.radio("What to scan", ["Last 24 hours", "Unread only", "Whole inbox"])
label = st.sidebar.text_input("Label / folder", value=config.DEFAULT_LABEL)
max_emails = st.sidebar.slider("Max emails", 5, 100, config.DEFAULT_MAX_EMAILS, step=5)
push_sheet = st.sidebar.checkbox("Also write to Google Sheet", value=True)

if st.sidebar.button("▶ Run scan", use_container_width=True, type="primary"):
    with st.spinner("Fetching and analyzing emails..."):
        try:
            report = run_pipeline(max_emails=max_emails, label=label.strip() or config.DEFAULT_LABEL,
                unread_only=(scope == "Unread only"),
                last_hours=24 if scope == "Last 24 hours" else None, push_to_sheet=push_sheet)
            st.sidebar.success(f"Fetched {report['fetched']} · {report['new']} new · "
                               f"{report['written_to_sheet']} → sheet")
        except FileNotFoundError:
            st.sidebar.error("credentials.json not found. See the README for OAuth setup.")
        except Exception as exc:
            st.sidebar.error(f"Scan failed: {exc}")

# --- sidebar: export ---
st.sidebar.subheader("Export")
c1, c2, c3 = st.sidebar.columns(3)
c1.download_button("CSV", exporter.to_csv(), "action_items.csv", "text/csv")
c2.download_button("Excel", exporter.to_excel(), "action_items.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
c3.download_button("PDF", exporter.to_pdf(), "action_items.pdf", "application/pdf")

# --- analytics cards ---
st.title("Inbox Action Dashboard")
stats = database.get_stats()
cols = st.columns(6)
gradients = ["linear-gradient(135deg,#4F46E5,#7C3AED)","linear-gradient(135deg,#DC2626,#F87171)",
    "linear-gradient(135deg,#D97706,#FBBF24)","linear-gradient(135deg,#059669,#34D399)",
    "linear-gradient(135deg,#2563EB,#60A5FA)","linear-gradient(135deg,#475569,#94A3B8)"]
labels = [("Total analyzed",stats["total"]),("High priority",stats["high"]),
    ("Medium priority",stats["medium"]),("Low priority",stats["low"]),
    ("Pending",stats["pending"]),("Completed",stats["completed"])]
for col,(lbl,val),grad in zip(cols,labels,gradients):
    col.markdown(card(lbl,val,grad), unsafe_allow_html=True)

# --- charts ---
left, right = st.columns(2)
if stats["total"]:
    prio_df = pd.DataFrame({"Priority":["High","Medium","Low"],
        "Count":[stats["high"],stats["medium"],stats["low"]]})
    fig1 = px.bar(prio_df, x="Priority", y="Count", color="Priority",
        color_discrete_map={"High":"#DC2626","Medium":"#D97706","Low":"#64748B"},
        title="Emails by priority")
    fig1.update_layout(showlegend=False, height=320)
    left.plotly_chart(fig1, use_container_width=True)
    status_df = pd.DataFrame({"Status":["Pending","Completed"],
        "Count":[stats["pending"],stats["completed"]]})
    fig2 = px.pie(status_df, names="Status", values="Count", hole=0.55,
        color="Status", color_discrete_map={"Pending":"#F59E0B","Completed":"#10B981"},
        title="Action status")
    right.plotly_chart(fig2, use_container_width=True)
else:
    st.info("No data yet — run a scan from the sidebar.")

# --- AI insights ---
st.subheader("🧠 AI insights")
if st.button("Generate daily briefing"):
    with st.spinner("Thinking..."):
        ins = InsightsEngine().generate()
        st.markdown(f"**Daily summary:** {ins['daily_summary']}")
        ic1, ic2 = st.columns(2)
        ic1.markdown("**🔥 Top urgent**")
        ic1.write("\n".join(f"- {x}" for x in ins["top_urgent"]) or "_None_")
        ic1.markdown("**⏰ Missed follow-ups**")
        ic1.write("\n".join(f"- {x}" for x in ins["missed_followups"]) or "_None_")
        ic2.markdown("**✅ Recommended next actions**")
        ic2.write("\n".join(f"- {x}" for x in ins["recommended_actions"]) or "_None_")

# --- filterable, editable table ---
st.subheader("📋 Action items")
f1, f2 = st.columns(2)
prio_filter = f1.selectbox("Priority", ["All"] + config.PRIORITIES)
status_filter = f2.selectbox("Status", ["All"] + config.STATUSES)
rows = database.get_all_emails(priority=prio_filter, status=status_filter)
if rows:
    df = pd.DataFrame(rows)[["date","sender","subject","summary","action_item",
                             "priority","due_date","status","id"]]
    edited = st.data_editor(df, hide_index=True, use_container_width=True,
        column_config={"id": None,
            "status": st.column_config.SelectboxColumn("Status", options=config.STATUSES)})
    if st.button("💾 Save status changes"):
        for _, row in edited.iterrows():
            database.update_status(row["id"], row["status"])
        st.success("Saved."); st.rerun()
else:
    st.caption("No emails match the current filters.")
```

**Key sections explained:**
- **`st.set_page_config(layout="wide")`** gives us the full screen for cards and charts.
- The **cards** are just styled HTML injected with `st.markdown(..., unsafe_allow_html=True)`. The `card()` helper keeps it tidy.
- **`st.data_editor`** is the magic widget — it renders the table *and* lets the user change the Status dropdown inline. We hide the `id` column (the user doesn't care) but keep it in the dataframe so we know which row to update.
- Clicking **Save** writes each row's status back to SQLite and calls `st.rerun()` to refresh the numbers.

---

## 6. Run it locally

```bash
# from the project root, with your venv active
streamlit run app.py
```

1. Your browser opens at `http://localhost:8501`.
2. In the sidebar, pick **Last 24 hours** and click **▶ Run scan**.
3. The *first* scan opens a Google consent screen — approve Gmail + Sheets access.
4. Watch the cards fill in, then click **Generate daily briefing** for the AI summary.
5. Check your Google Drive — there's a new **Email Action Items** sheet waiting.

To run the daily automation instead:

```bash
python -m src.scheduler        # keeps running, fires at DAILY_RUN_TIME
# or, one-shot for cron:
python -m src.pipeline
```

---

## 7. Deploy on Streamlit Cloud

1. Push your code to GitHub. (Your `.gitignore` keeps `.env`, `credentials.json`, and the DB out — double-check before pushing.)
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app** → pick your repo and set the main file to `app.py`.
3. Open **Settings → Secrets** and add:
   ```toml
   OPENAI_API_KEY = "sk-..."
   SHEET_TITLE = "Email Action Items"
   ```
4. **Google auth on a server:** the interactive desktop OAuth flow needs a browser, which a hosted app doesn't have. For deployment, switch to a **Google service account**: create one in Cloud Console, download its JSON key, store it as a Streamlit secret, and *share your target Google Sheet with the service account's email*. Then the app reads/writes that sheet headlessly. (Keep the desktop OAuth flow for local development — it's simpler there.)
5. Deploy. Streamlit gives you a public URL.

> 💡 For a fully automated cloud setup, pair a small always-on host (or a scheduled **GitHub Action**) running `python -m src.pipeline` daily with the Streamlit app as your read-only dashboard.

---

## 8. Common errors and fixes

| Error | Likely cause | Fix |
|-------|-------------|-----|
| `FileNotFoundError: credentials.json` | OAuth file not downloaded / wrong name | Download the **Desktop** OAuth client JSON and save it as `credentials.json` in the project root |
| `OPENAI_API_KEY is not set` | `.env` missing or key not pasted | `cp .env.example .env` and paste your real key |
| Browser doesn't open on first run / `redirect_uri_mismatch` | Wrong OAuth client type | Use OAuth client type **Desktop app**, not Web |
| `403 access_denied` during consent | Your email isn't a test user | Add yourself under **OAuth consent screen → Test users** |
| `insufficientPermissions` / scope error | Token cached with old scopes | Delete `data/token.json` and re-run to re-authorize |
| `HttpError 429` (OpenAI or Google) | Rate limit hit | Lower the **Max emails** slider; the async `concurrency` is already capped at 5 |
| Empty dashboard after a scan | All emails already in the DB | That's dedup working — try a wider scope or a label with new mail |
| Sheet not updating | "Also write to Google Sheet" unchecked, or wrong `SHEET_ID` | Tick the box; clear `SHEET_ID` in `.env` to auto-create a fresh sheet |
| `ModuleNotFoundError` | venv not active / deps not installed | Activate the venv and `pip install -r requirements.txt` |

---

## 9. What you learned

By building this, you picked up a stack of genuinely reusable skills:

- **Google OAuth** — authorizing an app to read Gmail and write Sheets, with scopes and token refresh.
- **Calling an LLM for structured output** — system prompts, JSON mode, and defensive parsing so bad output never crashes you.
- **Async Python** — `asyncio.gather` + a semaphore to run many API calls concurrently.
- **SQLite as a source of truth** — primary-key dedup, parameterized queries, and clean connection handling.
- **Modular architecture** — one job per file, with a single `pipeline.py` orchestrating them.
- **Streamlit dashboards** — cards, Plotly charts, an editable data table, and download buttons.
- **Automation** — turning a script into a daily job.

That's the real shape of a production AI agent: *fetch → reason → store → present → automate.*

---

## 10. What's next

Ideas to extend it (great portfolio additions):

- **Outlook / IMAP support** — add another client alongside `gmail_client.py`.
- **Auto-draft replies** — for High-priority emails, have the model draft a response you can approve.
- **Weekly digest** — email yourself a Friday summary using the insights engine.
- **Local model** — swap OpenAI for an open model via Ollama to cut costs to zero.
- **Smart labels** — write the assigned priority back to Gmail as a label.
- **Snooze + reminders** — add a "Snoozed" status and a follow-up nudge.

---

> ⭐ If this tutorial helped, **[star the repo](https://github.com/adityasharmadotai-hash/amazing-ai-agents)** and **[follow on LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)** — I share a new free AI agent build regularly.
>
> 🚀 **Looking for jobs at top AI companies in the U.S.?** [Apply here](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)
