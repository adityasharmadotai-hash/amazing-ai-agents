# ✉️ Personal Email Assistant Agent

> **Your AI-powered personal email intelligence platform.**
> Triage your inbox, prepare for meetings, draft replies, track follow-ups, and never miss an important email — all powered by GPT-4o and Gmail API.

**👉 STEP-BY-STEP TUTORIAL: [Tutorial.md](./Tutorial.md)**

---

## Overview

Personal Email Assistant Agent is a production-ready Streamlit application that brings AI-powered email intelligence to your daily workflow. Connect your Gmail, let AI rank your inbox by priority, generate smart replies, prepare you for meetings with full conversation context, and track every follow-up — all in a beautiful dark-mode dashboard.

Built on OpenAI GPT-4o + Gmail API + Google Calendar API, with SQLite storage and full demo mode (no Gmail needed to explore).

---

## Features

- 📬 **Smart Inbox** — Email viewer with search, filter, unread/starred/important flags
- ✨ **AI Triage** — Priority inbox ranked by GPT-4o (critical/high/medium/low)
- 🤖 **Email Summarization** — 2-3 sentence summaries of any email
- 💬 **Smart Reply Suggestions** — 3 reply options (professional/friendly/brief)
- 🧵 **Thread Context** — Full conversation analysis with action items and status
- 📅 **Calendar Integration** — Today's meetings, upcoming 7-day view
- 🧠 **Meeting Prep Briefs** — AI-generated talking points, context, attendee notes
- 👥 **Contact Intelligence** — AI profiles of frequent contacts based on email history
- ✍️ **AI Email Drafting** — Draft any email from a purpose + tone
- 🔄 **Tone Rewriting** — Rewrite emails in 6 different tones
- ⏰ **Reminder System** — Create, track, and complete email-linked reminders
- 🔁 **Follow-up Tracking** — Never lose track of awaited replies
- 📊 **Analytics Dashboard** — Priority distribution, category pie, top senders
- 🎭 **Demo Mode** — Fully functional without connecting real Gmail

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Core language |
| Streamlit | Web UI framework |
| OpenAI GPT-4o | AI features (12 prompts) |
| Gmail API | Email read/send |
| Google Calendar API | Meeting data |
| SQLite | Local persistence |
| Plotly | Charts and analytics |
| google-auth-oauthlib | OAuth 2.0 flow |

---

## Project Structure

```
email-assistant/
├── app.py                    # Main Streamlit app (9 pages, 1500+ lines)
├── modules/
│   ├── __init__.py
│   ├── agent.py              # 12 GPT-4o AI functions
│   ├── gmail_client.py       # Gmail API + Calendar API + OAuth
│   ├── database.py           # SQLite (7 tables)
│   └── demo_data.py          # Realistic demo emails/contacts/events
├── credentials/              # Auto-created; holds OAuth tokens
├── data/                     # Auto-created; holds SQLite DB
├── .streamlit/
│   ├── config.toml           # Dark indigo theme
│   └── secrets.toml.example
├── requirements.txt
├── .env.example
├── README.md
└── Tutorial.md
```

---

## Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your OpenAI key (optional for demo mode)

```bash
cp .env.example .env
# Add: OPENAI_API_KEY=sk-...
```

### 3. Run

```bash
streamlit run app.py
```

Open http://localhost:8501 — **Demo Mode is on by default**, no Gmail needed.

---

## Gmail Connection (Optional)

To use real Gmail data:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project → Enable **Gmail API** + **Google Calendar API**
3. Create OAuth 2.0 credentials (Web application type)
4. Add `http://localhost:8501` as an authorized redirect URI
5. Copy Client ID and Secret → paste in **Settings → Gmail / OAuth**
6. Click "Connect Gmail" → authorize → paste the auth code
7. Toggle off Demo Mode in the sidebar

---

## Pages

| Page | Features |
|------|---------|
| 📬 Inbox | Read, search, filter, reply, AI analysis per email |
| ✨ AI Triage | Priority-ranked inbox, needs-reply detection |
| 📅 Calendar | Today's events, 7-day view, related emails per meeting |
| 🧠 Meeting Prep | AI brief: talking points, context, attendee notes, checklist |
| ✍️ AI Compose | Draft from purpose, tone rewriting, saved drafts |
| 👥 Contacts | Contact profiles, email history, AI summaries |
| ⏰ Reminders | Create reminders, track follow-ups |
| 📊 Dashboard | Analytics, charts, action items summary |
| ⚙️ Settings | API keys, OAuth setup, preferences, DB management |

---

## AI Functions

| Function | What it does |
|----------|-------------|
| `summarize_email()` | 2-3 sentence email summary |
| `suggest_replies()` | 3 reply options with different tones |
| `classify_priority()` | critical/high/medium/low + category + action |
| `detect_unanswered()` | Find important unread emails needing reply |
| `prepare_meeting_brief()` | Full meeting prep with talking points |
| `generate_conversation_context()` | Thread analysis with action items |
| `summarize_contact()` | AI profile from email history |
| `draft_email()` | Full email from purpose + tone |
| `rewrite_tone()` | Rewrite in 6 tones |
| `rank_priority_inbox()` | Batch-rank 20 emails |
| `detect_follow_up_needed()` | Identify awaited replies |
| `generate_inbox_insight()` | Productivity insight + recommendation |

---

## License

MIT — free to use, modify, and deploy.
