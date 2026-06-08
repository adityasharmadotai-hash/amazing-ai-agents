> ⭐ **Star the repo:** https://github.com/adityasharmadotai-hash/amazing-ai-agents
> 💼 **Follow on LinkedIn:** https://www.linkedin.com/in/aditya-hicounselor/
> 📺 **Subscribe on YouTube:** https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ
> 🚀 **Looking for jobs at top AI companies in the U.S.? Apply here:** https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform

---

# 🧑‍🏫 Tutorial: Build a Competitor Intelligence Agent with Python, Streamlit & OpenAI

A complete, beginner‑friendly walkthrough. By the end, you'll have a working AI app that monitors competitors and explains what changed — and you'll understand **every file** that makes it work.

---

## 📑 Table of Contents

1. [What We're Building (and Why)](#1-what-were-building-and-why)
2. [How It Works](#2-how-it-works)
3. [Prerequisites Checklist](#3-prerequisites-checklist)
4. [Project Setup](#4-project-setup)
5. [The Files, Explained](#5-the-files-explained)
   - [5.1 `requirements.txt`](#51-requirementstxt)
   - [5.2 `.env.example`](#52-envexample)
   - [5.3 `database.py`](#53-databasepy--the-memory)
   - [5.4 `scraper.py`](#54-scraperpy--the-data-collector)
   - [5.5 `ai_analysis.py`](#55-ai_analysispy--the-brain)
   - [5.6 `alerts.py`](#56-alertspy--the-notifier)
   - [5.7 `app.py`](#57-apppy--the-user-interface)
   - [5.8 `generate_test_data.py`](#58-generate_test_datapy--sample-data)
6. [Running Locally](#6-running-locally)
7. [Deploying to Streamlit Cloud](#7-deploying-to-streamlit-cloud)
8. [Common Errors & Fixes](#8-common-errors--fixes)
9. [What You Learned](#9-what-you-learned)
10. [What's Next](#10-whats-next)

---

## 1. What We're Building (and Why)

We're building a **Competitor Intelligence Agent** — a web app where you add a competitor's name and website, and the app automatically:

- scrapes their website, pricing page, and job listings,
- saves everything to a small local database,
- asks **OpenAI** to explain *what changed and why it matters*,
- shows it all on a clean dashboard with charts and downloadable reports.

**Why build it?** Tracking competitors by hand is slow and easy to forget. This app turns a repetitive research chore into a one‑click workflow — a perfect, real‑world project for learning how to combine **web scraping + a database + an LLM + a web UI**.

---

## 2. How It Works

The app has four moving parts behind one Streamlit interface:

```
                ┌──────────────────────────────────────────┐
                │            Streamlit UI (app.py)          │
                │   Sidebar navigation · Pages · Settings   │
                └───────────────┬───────────────────────────┘
                                │  (you click a button)
            ┌───────────────────┼─────────────────────┐
            ▼                   ▼                     ▼
     ┌────────────┐      ┌──────────────┐      ┌────────────┐
     │  Scraper   │ ───► │  AI Analysis │      │   Alerts   │
     │ (requests, │      │   (OpenAI)   │      │   (email)  │
     │   bs4)     │      │              │      │            │
     └─────┬──────┘      └──────┬───────┘      └─────┬──────┘
           │                    │                    │
           └────────────────────┼────────────────────┘
                                ▼
                        ┌───────────────┐
                        │   Database    │
                        │   (SQLite)    │
                        └───────────────┘
```

1. You click a button (e.g. **Scan Now**).
2. `scraper.py` fetches the competitor's web data.
3. `ai_analysis.py` sends that data to OpenAI for a plain‑English summary.
4. `database.py` saves the result.
5. The dashboard renders charts, alerts, and insights; `alerts.py` can email a digest.

---

## 3. Prerequisites Checklist

Before you start, make sure you have:

- [ ] **Python 3.10 or newer** — check with `python --version`
- [ ] **pip** (comes with Python)
- [ ] A code editor (VS Code recommended)
- [ ] An **OpenAI API key** — create one at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- [ ] A terminal (Command Prompt / PowerShell / Terminal)
- [ ] *(Optional)* A Gmail **App Password** if you want email alerts
- [ ] *(Optional)* A free **GitHub** account for deployment

No prior AI or web‑scraping experience needed — we'll explain each piece.

---

## 4. Project Setup

Create a folder and a virtual environment (an isolated space for this project's packages):

```bash
# 1. Make a project folder
mkdir competitor-intelligence-agent
cd competitor-intelligence-agent

# 2. Create and activate a virtual environment
python -m venv venv

# macOS / Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

You'll add the files below one by one. (If you cloned the repo, they already exist — read along to understand them.)

---

## 5. The Files, Explained

### 5.1 `requirements.txt`

This lists every Python package the project needs.

```txt
streamlit>=1.39.0
openai>=1.40.0
pandas>=2.2.0
plotly>=5.20.0
requests>=2.31.0
beautifulsoup4>=4.12.0
python-dotenv>=1.0.0
jinja2>=3.1.0
lxml>=5.1.0
pytz>=2024.1
schedule>=1.2.0
sqlalchemy>=2.0.0
httpx>=0.27.0
```

**Plain English:** `streamlit` is the web UI, `openai` talks to the AI, `requests`/`beautifulsoup4`/`lxml` scrape websites, `pandas`/`plotly` make tables and charts, and `jinja2` builds HTML emails. We use `>=` (not `==`) so the packages install cleanly on whatever Python version your machine or Streamlit Cloud is running.

Install everything with:

```bash
pip install -r requirements.txt
```

---

### 5.2 `.env.example`

A template for your secret settings. Copy it to `.env` and fill in real values.

```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o

# Email Alert Configuration (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
ALERT_EMAIL=your-email@example.com

# Database
DATABASE_PATH=competitors.db
```

**Plain English:** Never hard‑code secrets in your code. We keep them in `.env`, which is read at runtime. The only required value is `OPENAI_API_KEY`.

---

### 5.3 `database.py` — the memory

This file gives the app a **persistent memory** using SQLite, a tiny database that lives in a single file (`competitors.db`). No server to install.

**Key idea #1 — a safe connection helper.** Every database operation borrows a connection and always closes it:

```python
from contextlib import contextmanager
import sqlite3

class Database:
    def __init__(self, db_path="competitors.db"):
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row   # lets us read rows like dictionaries
        try:
            yield conn
        finally:
            conn.close()
```

**Key idea #2 — the schema.** `init_db()` creates the tables the first time it runs (`CREATE TABLE IF NOT EXISTS`). The main tables are:

| Table              | What it stores                                        |
| ------------------ | ----------------------------------------------------- |
| `competitors`      | Name, website, LinkedIn, Twitter for each competitor  |
| `changes`          | Detected website/product changes + severity           |
| `price_changes`    | Snapshots of pricing data (stored as JSON text)       |
| `job_openings`     | Discovered jobs with title + department               |
| `product_launches` | New products/features                                 |
| `alerts`           | Notifications, with a `sent` flag                     |
| `website_snapshots`| Raw page content + hash for change detection          |

For example, the competitors table:

```python
cursor.execute('''
    CREATE TABLE IF NOT EXISTS competitors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        website_url TEXT,
        linkedin_url TEXT,
        twitter_handle TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_scanned TIMESTAMP
    )
''')
```

**Key idea #3 — simple read/write methods.** Each piece of data has an `add_*` and `get_*` method. They use **parameterized queries** (`?` placeholders) which prevent SQL‑injection bugs:

```python
def add_competitor(self, name, website_url, linkedin_url=None, twitter_handle=None):
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO competitors (name, website_url, linkedin_url, twitter_handle)
            VALUES (?, ?, ?, ?)
        ''', (name, website_url, linkedin_url, twitter_handle))
        conn.commit()
        return cursor.lastrowid

def get_competitors(self):
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM competitors ORDER BY added_at DESC')
        return [dict(row) for row in cursor.fetchall()]
```

The file also has helpers like `get_recent_changes(days=7)`, `get_competitor_price_history()`, `get_all_alerts()`, and `get_database_stats()` — all following the same pattern. **The full file is in the repo;** the takeaway is: *each app feature has a tiny, predictable function to read or write its data.*

---

### 5.4 `scraper.py` — the data collector

This file fetches data from the web. It has several classes; here are the two most important.

**`WebScraper`** downloads a page and extracts its structure:

```python
import requests
from bs4 import BeautifulSoup
import hashlib
from urllib.parse import urljoin
from datetime import datetime

class WebScraper:
    def __init__(self, timeout=10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_website(self, url):
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            return {
                'url': url,
                'title': soup.title.string if soup.title else 'N/A',
                'meta_description': self._get_meta_description(soup),
                'headings': self._extract_headings(soup),
                'links': self._extract_links(soup, url),
                'content_hash': self._hash_content(response.content),
                'scraped_at': datetime.now().isoformat(),
                'text_length': len(soup.get_text()),
            }
        except Exception as e:
            return None
```

**Plain English:**
- A `User-Agent` header makes our request look like a normal browser.
- `BeautifulSoup` parses the HTML so we can pull out the title, headings, and links.
- `_hash_content()` makes an MD5 fingerprint of the page. If the fingerprint changes next time, the page changed — that's how we **detect changes cheaply** without storing the whole page.

**`detect_changes()`** compares a new scrape to the previous one and reports what's new:

```python
def detect_changes(self, current_data, previous_data):
    if not previous_data:
        return {'status': 'first_scan', 'changes': []}

    changes = []
    if current_data['content_hash'] != previous_data['content_hash']:
        changes.append({'type': 'content_modified', 'severity': 'high',
                        'description': 'Website content has been updated'})

    new_links = set(current_data['links']) - set(previous_data.get('links', []))
    if new_links:
        changes.append({'type': 'new_links', 'severity': 'medium',
                        'description': f'Found {len(new_links)} new links'})
    return {'status': 'changes_detected' if changes else 'no_changes', 'changes': changes}
```

The file also includes **`PricingScraper`** (tries `/pricing`, `/plans`, etc. and pulls out prices/plan names) and **`HiringTracker`** (returns sample job postings — a placeholder you can later wire to a real jobs API). The pattern is the same everywhere: *fetch → parse → return a clean Python dictionary.*

---

### 5.5 `ai_analysis.py` — the brain

This is where OpenAI turns raw data into insight. It exposes a `CompetitorAnalyzer` class.

**Setup — build the client only if a key exists** (so the app still runs without one):

```python
import os
from openai import OpenAI

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

class CompetitorAnalyzer:
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or DEFAULT_MODEL
        self.client = self._build_client()

    def _build_client(self):
        if not self.api_key:
            return None
        try:
            return OpenAI(api_key=self.api_key)
        except Exception:
            return None

    def configure(self, api_key=None, model=None):
        """Update the key/model at runtime (used by the Settings page)."""
        if api_key is not None:
            self.api_key = api_key
        if model is not None:
            self.model = model
        self.client = self._build_client()
        return self.client is not None
```

> ⚠️ **Important:** we use the modern OpenAI SDK (v1+). The call is `client.chat.completions.create(...)`. The old `openai.ChatCompletion.create(...)` style was **removed** in v1 and will crash — don't use it.

**One helper to talk to the model:**

```python
def _complete(self, system, prompt, max_tokens=300, temperature=0.7):
    if not self.client:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    response = self.client.chat.completions.create(
        model=self.model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return (response.choices[0].message.content or "").strip()
```

**Plain English:** the `system` message sets the AI's role ("you are a competitive intelligence analyst"), the `user` message is the actual question, and we read the answer from `response.choices[0].message.content`.

Every feature is a thin wrapper around `_complete()`. For example:

```python
def analyze_website_changes(self, website_data, competitor_name):
    if not website_data:
        return "Unable to analyze website"
    prompt = f"""
    Analyze these website changes for competitor '{competitor_name}':
    Title: {website_data.get('title')}
    New Sections: {', '.join(website_data.get('headings', [])[:5])}
    Provide a concise 1-2 sentence analysis of what's changed and why it matters.
    """
    try:
        return self._complete(
            "You are a competitive intelligence analyst. Provide concise, actionable insights.",
            prompt, max_tokens=150,
        )
    except Exception:
        return self._fallback_analysis(website_data)   # graceful degradation
```

Notice the **fallback**: if the API call fails (e.g. no key, rate limit), the app doesn't crash — it returns a basic rule‑based summary instead. There are similar methods for pricing, hiring, threats, and a `detect_product_launches()` that asks the model to return JSON. The file also has a `ReportGenerator` class that assembles executive/market reports from the database.

---

### 5.6 `alerts.py` — the notifier

This file sends **HTML email digests** using Python's built‑in `smtplib` and `jinja2` templates.

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from jinja2 import Template

class AlertManager:
    def __init__(self, db):
        self.db = db
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')

    def send_alert(self, recipient_email, subject, body, html=False):
        if not self.sender_email or not self.sender_password:
            return False   # no credentials → skip silently
        msg = MIMEMultipart('alternative')
        msg['Subject'], msg['From'], msg['To'] = subject, self.sender_email, recipient_email
        msg.attach(MIMEText(body, 'html' if html else 'plain'))
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()                                  # encrypt the connection
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
        return True
```

`send_daily_digest()` gathers unsent alerts, groups them by competitor, renders an HTML email with a Jinja2 template, sends it, and marks those alerts as sent. **Plain English:** email is optional — if you don't set SMTP credentials, the app simply skips sending and keeps working.

---

### 5.7 `app.py` — the user interface

This is the file you run. It ties everything together with Streamlit. It's the longest file, so we'll walk through it in sections. (The complete file is in the repo.)

**(a) Imports and one‑time initialization.** We cache the heavy objects so they're created once per session:

```python
import os, json
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import pytz

from database import Database
from ai_analysis import CompetitorAnalyzer, ReportGenerator
from scraper import WebScraper, PricingScraper, HiringTracker
from alerts import AlertManager

st.set_page_config(page_title="Competitor Intelligence Agent", page_icon="🔍", layout="wide")

@st.cache_resource
def init_components():
    db = Database("competitors.db")
    analyzer = CompetitorAnalyzer()
    scraper = WebScraper()
    pricing_scraper = PricingScraper()
    hiring_tracker = HiringTracker()
    alert_manager = AlertManager(db)
    return db, analyzer, scraper, pricing_scraper, hiring_tracker, alert_manager

db, analyzer, scraper, pricing_scraper, hiring_tracker, alert_manager = init_components()
report_generator = ReportGenerator(db, analyzer)
```

> `@st.cache_resource` is important: Streamlit re‑runs your whole script on every click, and caching stops it from rebuilding the database connection each time.

**(b) Resolving the API key from three places.** The app looks for your key in this order — the Settings page, Streamlit Secrets, then an environment variable:

```python
def resolve_openai_key():
    if st.session_state.get("openai_api_key"):
        return st.session_state["openai_api_key"]
    try:
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass
    return os.getenv("OPENAI_API_KEY", "")

# Apply it to the analyzer on every run
if analyzer is not None:
    key, model = resolve_openai_key(), resolve_openai_model()
    if key != (analyzer.api_key or "") or model != analyzer.model:
        analyzer.configure(api_key=key or None, model=model)
```

**(c) The sidebar = navigation.** Instead of tabs, we use a radio menu to switch "pages", plus a quick **Add Competitor** form:

```python
PAGES = ["📊 Dashboard", "🌐 Website Monitoring", "💰 Pricing Intelligence",
         "👥 Hiring Activity", "🚀 Product Launches", "📧 Alerts & Reports", "⚙️ Settings"]

with st.sidebar:
    st.markdown("## 🔍 Competitor IQ")
    page = st.radio("Navigate", PAGES, key="nav")

    with st.expander("➕ Add Competitor"):
        with st.form("add_competitor"):
            comp_name = st.text_input("Competitor Name")
            comp_website = st.text_input("Website URL")
            if st.form_submit_button("Add Competitor"):
                if comp_name and comp_website:
                    db.add_competitor(comp_name, comp_website, "", "")
                    st.rerun()

    if analyzer and analyzer.client:
        st.success(f"🔑 OpenAI connected\n\n`{analyzer.model}`")
    else:
        st.warning("🔑 OpenAI not configured")
```

> **Why `key=` matters:** every interactive widget (button, selectbox, etc.) needs a unique identity. If two buttons share the same label with no `key`, Streamlit raises `StreamlitDuplicateElementId`. Giving each widget a unique `key="..."` avoids that.

**(d) Each "page" is an `if/elif` block.** Because only one page renders at a time, the code stays simple. Here's the **Website Monitoring** page — the others (Pricing, Hiring, Products) follow the exact same shape:

```python
elif page == PAGES[1]:
    render_header("Track website changes, new features, and content updates")
    competitors = get_competitors()

    selected = st.selectbox("Select Competitor", [c['name'] for c in competitors], key="website_select")
    if st.button("🔄 Scan Now", key="website_scan"):
        comp = next((c for c in competitors if c['name'] == selected), None)
        data = scraper.scrape_website(comp['website_url'])          # 1) scrape
        analysis = analyzer.analyze_website_changes(data, comp['name'])  # 2) AI summary
        db.add_change(comp['id'], 'website_update', analysis)       # 3) save
        st.success("✅ Website scan complete")
```

That's the core loop of the whole app: **scrape → analyze → save → show.**

**(e) The Settings page — all configuration in one place.** API key, model, alert defaults, and monitoring toggles all live here, stored in `st.session_state`:

```python
elif page == PAGES[6]:
    render_header("All configuration and default settings in one place")

    with st.form("openai_settings"):
        key_input = st.text_input("OpenAI API Key", type="password",
                                  value=st.session_state.get("openai_api_key", ""))
        model_input = st.selectbox("Model", ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"])
        if st.form_submit_button("💾 Save & Connect"):
            st.session_state["openai_api_key"] = key_input.strip()
            st.session_state["openai_model"] = model_input
            analyzer.configure(api_key=key_input.strip() or None, model=model_input)
            st.success("✅ Settings saved and OpenAI connected.")
```

The dashboard page renders gradient **KPI cards** and a **Plotly** bar chart of competitor activity. The full styling lives in a `<style>` block near the top of the file.

---

### 5.8 `generate_test_data.py` — sample data

So you can explore the app without scraping real sites first, this script seeds the database with realistic fake data:

```python
class TestDataGenerator:
    SAMPLE_COMPETITORS = [
        {'name': 'Segment',  'website': 'https://segment.com',  ...},
        {'name': 'Mixpanel', 'website': 'https://mixpanel.com', ...},
        # ...
    ]

    def generate_all_data(self, num_competitors=5, days=30):
        for comp in self.SAMPLE_COMPETITORS[:num_competitors]:
            comp_id = self.db.add_competitor(comp['name'], comp['website'], comp['linkedin'], comp['twitter'])
            self._generate_website_changes(comp_id, days)
            self._generate_pricing_changes(comp_id, days)
            self._generate_job_openings(comp_id)
            self._generate_product_launches(comp_id, days)
            self._generate_alerts(comp_id, days)
```

Run it from the terminal:

```bash
python generate_test_data.py --competitors 5 --days 30
```

---

## 6. Running Locally

With your virtual environment active and dependencies installed:

```bash
# 1. Set your key (or paste it in the Settings page later)
cp .env.example .env        # then edit .env and add OPENAI_API_KEY

# 2. (Optional) add sample data
python generate_test_data.py --competitors 5 --days 30

# 3. Launch
streamlit run app.py
```

Your browser opens at **http://localhost:8501**. Add a competitor in the sidebar, then explore the Dashboard, run a scan, and open the **⚙️ Settings** page to confirm OpenAI is connected.

---

## 7. Deploying to Streamlit Cloud

Streamlit Community Cloud hosts the app for free.

1. **Push your code to a public GitHub repo.**
2. Go to **[share.streamlit.io](https://share.streamlit.io)** → **New app**.
3. Pick your repo and branch. Set **Main file path** to `app.py` (or the full path if it's in a subfolder).
4. Under **Advanced settings → Secrets**, add your key in TOML format:
   ```toml
   OPENAI_API_KEY = "sk-your-api-key-here"
   OPENAI_MODEL = "gpt-4o"
   ```
5. Click **Deploy**. Streamlit reads `requirements.txt`, installs everything, and gives you a public URL.

> Whenever you push new commits to the deployed branch, Streamlit auto‑redeploys.

---

## 8. Common Errors & Fixes

| Error / Symptom | Cause | Fix |
| --------------- | ----- | --- |
| `ModuleNotFoundError: No module named 'streamlit'` | Dependencies not installed / wrong venv | Activate your venv, then `pip install -r requirements.txt` |
| App won't deploy; build fails installing packages | Pinned versions have no wheels for the host's Python | Use flexible pins (`>=`) as in this project's `requirements.txt` |
| `AttributeError: module 'openai' has no attribute 'ChatCompletion'` | Old SDK syntax on OpenAI v1+ | Use `OpenAI()` client + `client.chat.completions.create(...)` |
| `StreamlitDuplicateElementId` | Two widgets share a label with no `key` | Give every button/selectbox a unique `key="..."` |
| `SyntaxError: unexpected character after line continuation` | Stray `\n` or escaped quotes pasted into a file | Re‑paste the code cleanly; make sure quotes are `"""` not `\"\"\"` |
| AI features return generic text | No API key configured | Add `OPENAI_API_KEY` in `.env`, Streamlit Secrets, or the Settings page |
| Emails never send | SMTP not configured | Set `SENDER_EMAIL` + a Gmail **App Password** (not your login password) |
| Data disappears after redeploy | Cloud filesystem is ephemeral | Expected for a demo; use a hosted DB (e.g. Postgres) for persistence |

---

## 9. What You Learned

By building this project, you now know how to:

- 🧱 **Structure a multi‑file Python app** with clear separation of concerns (UI, data, AI, scraping, alerts).
- 🗄️ **Use SQLite** with safe, parameterized queries and a connection context manager.
- 🌐 **Scrape websites** with Requests + BeautifulSoup, and detect changes with content hashing.
- 🤖 **Call the OpenAI API** correctly (v1 SDK) with system/user messages and graceful fallbacks.
- 🖥️ **Build an interactive UI** in Streamlit with sidebar navigation, forms, charts, and `session_state`.
- 🔑 **Manage secrets** properly via `.env`, Streamlit Secrets, and a runtime Settings page.
- ☁️ **Deploy** a Python app to the cloud.

---

## 10. What's Next

Ideas to extend the project:

- 🔁 **Real scheduling** — wire up the `schedule` library (or Streamlit Cloud cron) to scan automatically.
- 🗃️ **Persistent database** — swap SQLite for Postgres so data survives redeploys.
- 🐦 **Real social/news data** — connect the `SocialMediaMonitor` / `NewsMonitor` stubs to live APIs.
- 📄 **PDF/Excel reports** — render the JSON reports into branded PDFs (e.g. with `reportlab`).
- 🔔 **Slack/Discord alerts** — add webhook notifications alongside email.
- 🧪 **Tests** — add `pytest` tests for the database and scraper layers.

---

<div align="center">

🎉 **Congratulations — you built an AI competitor‑intelligence agent!**

⭐ **Star the repo:** https://github.com/adityasharmadotai-hash/amazing-ai-agents
💼 **LinkedIn:** https://www.linkedin.com/in/aditya-hicounselor/
📺 **YouTube:** https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ

</div>
