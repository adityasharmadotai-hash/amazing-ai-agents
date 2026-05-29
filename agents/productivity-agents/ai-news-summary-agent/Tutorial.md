# 📘 AI News Summary Agent — Complete Tutorial

---

## Table of Contents

1. [Architecture](#1-architecture)
2. [News Fetching — fetcher.py](#2-news-fetching--fetcherpy)
3. [Database Design — database.py](#3-database-design--databasepy)
4. [AI Features — agent.py](#4-ai-features--agentpy)
5. [Delivery — delivery.py](#5-delivery--deliverypy)
6. [Scheduler — scheduler.py](#6-scheduler--schedulerpy)
7. [UI Architecture — app.py](#7-ui-architecture--apppy)
8. [Prompt Engineering](#8-prompt-engineering)
9. [Extending the App](#9-extending-the-app)
10. [Deployment](#10-deployment)

---

## 1. Architecture

```
RSS FEEDS          GOOGLE NEWS        HACKER NEWS     REDDIT       NEWSAPI
    │                   │                  │              │             │
    └───────────────────┴──────────────────┴──────────────┴─────────────┘
                                    │
                              fetcher.py
                         fetch_all_news(prefs)
                                    │
                         ┌──────────┴──────────┐
                     agent.py              database.py
                 classify_topics()        upsert_articles()
                 detect_duplicates()      get_articles()
                 batch_analyse()          save_digest()
                 generate_executive_digest()
                                    │
                              app.py (Streamlit)
                         10 pages · dark theme · demo mode
                                    │
                    ┌───────────────┴──────────────┐
               delivery.py                  scheduler.py
           email + WhatsApp             background threading
```

---

## 2. News Fetching — fetcher.py

### Source Architecture

The fetcher has 7 source adapters, all returning the same normalised dict:

```python
def _article(title, url, source, published, summary, ...) -> dict:
    return {
        "id": hashlib.md5(f"{url}{title}".encode()).hexdigest()[:16],
        "title": _clean(title)[:200],
        "source": source,
        ...
        "signal_score": 0.0,  # filled by AI later
    }
```

Using MD5 of URL+title as ID means the same article from different fetches gets the same ID — enabling `INSERT OR IGNORE` deduplication at DB level.

### The `_clean()` Function

```python
def _clean(text: str) -> str:
    text = html.unescape(text)          # &amp; → &
    text = re.sub(r"<[^>]+>", " ", text) # strip HTML tags
    return re.sub(r"\s+", " ", text).strip()[:1000]
```

RSS feeds often contain HTML entities and tags in summaries. This strips everything to clean text.

### RSS vs Google News RSS

Both use `feedparser`, but Google News RSS URLs encode the topic:
```python
GOOGLE_NEWS_TOPICS = {
    "Technology": "https://news.google.com/rss/topics/CAAq...",
    # Each topic has a unique base64-encoded topic ID
}
```

For keyword search, Google News has a search endpoint:
```python
url = f"https://news.google.com/rss/search?q={quote(keyword)}&hl=en"
```

### Rate Limiting

```python
time.sleep(0.1)  # between RSS feeds
time.sleep(0.5)  # Reddit (stricter rate limits)
time.sleep(0.2)  # Google News per keyword
```

Reddit's API terms require polite crawling. The User-Agent header also matters:
```python
headers = {"User-Agent": "NewsAgent/1.0 (research tool)"}
```

---

## 3. Database Design — database.py

### Seven Tables

```sql
articles    -- All fetched articles with AI enrichment
preferences -- User topic/keyword/source preferences (single row, id=1)
digests     -- Generated executive briefs with article references
saved       -- Bookmarked articles with notes
analytics   -- Daily fetch statistics
schedule    -- Scheduler configuration (single row, id=1)
ai_cache    -- MD5-keyed cache for AI results (added dynamically)
```

### The Signal Score as a Column

```python
signal_score REAL DEFAULT 0
```

Stored as a real number (not in JSON) so we can:
```sql
ORDER BY signal_score DESC
WHERE signal_score >= 7.0
AVG(signal_score)
```

### Article Deduplication Strategy

Three levels:

1. **ID-level** (database): `INSERT OR IGNORE` based on MD5(url+title)
2. **Title similarity** (Python): Word overlap >60% → mark as duplicate
3. **Semantic** (GPT-4o): Available for ambiguous cases

```python
def detect_duplicates(articles):
    seen_titles = {}
    for i, a in enumerate(articles):
        norm = re.sub(r"[^a-z0-9 ]", "", a["title"].lower())
        words = set(norm.split())
        for existing_norm, existing_idx in seen_titles.items():
            existing_words = set(existing_norm.split())
            overlap = len(words & existing_words) / max(len(words | existing_words), 1)
            if overlap > 0.6:
                # Keep higher-signal version
                ...
```

Jaccard similarity on word sets is fast and surprisingly effective for news headline deduplication.

---

## 4. AI Features — agent.py

### The Signal Score Rubric

```
10: Historic event (moon landing, world war declaration)
9:  Major global story (central bank rate change, tech giant acquisition)
8:  Important industry news (product launch, major legislation)
7:  Notable development (company earnings beat, scientific study)
6:  Relevant but not urgent
1-5: Routine, informational, or low-impact
```

The score is prompted explicitly with examples so GPT-4o applies it consistently.

### Batch Analysis vs Single Analysis

Single: `analyse_article()` — 1 API call per article, used on-demand.

Batch: `batch_analyse()` — 1 API call for 5 articles, used for bulk processing:

```python
batch_text = "\n\n".join([
    f"[{i+1}] Title: {a['title']}\nSource: {a['source']}\nSnippet: {a['summary'][:200]}"
    for i, a in enumerate(articles[:5])
])
# System prompt asks for JSON array indexed by [1], [2]...
```

Cost comparison:
- 100 articles × single call = 100 API calls ≈ $0.15
- 100 articles × batch of 5 = 20 API calls ≈ $0.06

### The Executive Digest Structure

```python
{
    "title": "Morning Intelligence Brief — Monday, January 6, 2025",
    "overview": "2-3 sentence overview",
    "key_themes": ["AI Capability Leap", ...],
    "sections": [
        {
            "category": "Technology & AI",
            "headline": "Bold section headline",
            "stories": [{"title": "...", "insight": "1 sentence"}],
            "takeaway": "What executives should do"
        }
    ],
    "market_signals": ["S&P +1.8%", "BTC +12%"],
    "action_items": ["Review AI strategy", ...],
    "sentiment_overview": "positive|mixed|negative",
    "word_of_day": "Breakthrough"
}
```

The `word_of_day` field adds personality and is surprisingly effective at summarising the news cycle in one word.

### Title Similarity Deduplication

GPT-4o-based dedup would cost $0.001+ per pair and be too slow for 100+ articles. The word-overlap heuristic handles 95% of cases:

- "GPT-5 Launches with Record Capabilities" vs "OpenAI's GPT-5 Sets Records in Benchmarks" → 60% word overlap → duplicate detected ✓
- "Apple Announces Vision Pro 2" vs "Fed Cuts Interest Rates" → 0% overlap → correctly kept ✓

---

## 5. Delivery — delivery.py

### Gmail Setup

Gmail now requires App Passwords (not your account password):
1. Enable 2FA: [myaccount.google.com/security](https://myaccount.google.com/security)
2. Generate App Password: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Set `SMTP_PASS=<16-char-app-password>`

```python
with smtplib.SMTP(host, port) as server:
    server.ehlo()
    server.starttls()          # Upgrade to TLS
    server.login(user, pwd)    # App password here
    server.sendmail(...)
```

### WhatsApp via wa.me

WhatsApp doesn't have a free API for sending programmatically. The `wa.me` deep link approach works reliably:

```python
def get_whatsapp_link(phone: str, message: str) -> str:
    encoded = urllib.parse.quote(message)
    return f"https://wa.me/{clean_phone}?text={encoded}"
```

The user clicks the link → WhatsApp opens on their device with the message pre-filled → they tap Send. No API key needed.

### HTML Email Template

The HTML email uses inline styles (not CSS classes) for maximum email client compatibility. Gmail, Outlook, and Apple Mail all strip `<style>` tags.

---

## 6. Scheduler — scheduler.py

### Why `schedule` Library Over Cron

- No system cron required — runs inside the Python process
- Works on Windows, macOS, and Linux
- No file permissions or sudo needed
- Deployable to Streamlit Cloud

### Threading Pattern

```python
_stop_event = threading.Event()

def _run_scheduler():
    while not _stop_event.is_set():
        schedule.run_pending()
        time.sleep(30)  # check every 30 seconds

_scheduler_thread = threading.Thread(target=_run_scheduler, daemon=True)
_scheduler_thread.start()
```

`daemon=True` means the thread dies when the main process exits — no orphan processes.

### Streamlit + Threading Caveat

Streamlit re-runs the entire script on every user interaction. The scheduler thread persists across reruns because it's stored in `threading.Thread` (not in `st.session_state`). However, if the Streamlit server restarts, the thread is lost — the schedule config in the database re-initialises it on the next page load.

---

## 7. UI Architecture — app.py

### Page Routing

```python
PAGES = {"📰 News Feed": "feed", "✨ AI Digest": "digest", ...}

if "page" not in st.session_state:
    st.session_state.page = "feed"

# Each page is an `if page == "feed":` block
# No elif — each block is independent
```

Single file, no `st.Page` multipage setup. Simpler for deployment.

### Demo Mode Toggle

```python
def use_demo() -> bool:
    return st.session_state.get("demo_mode", True)

def current_articles(limit=100, ...) -> list[dict]:
    if use_demo():
        return get_demo_articles()  # pre-built data
    return database.get_articles(limit=limit, ...)
```

Every page calls `current_articles()` — transparently returns demo or live data.

### The News Card Pattern

The `news_card_html()` function builds a single HTML string for each article. This is faster than Streamlit's native components for lists of 50+ items:

```python
# 50 articles × st.metric() = 200+ widget renders
# 50 articles × st.markdown(html) = 50 markdown renders (much faster)
```

### Invisible Click Button Trick

```python
col_btn, col_card = st.columns([0.001, 1])
with col_card:
    if st.button(title[:35], key=f"art_{id}", use_container_width=True):
        st.session_state.selected_article = art
        st.rerun()
    st.markdown(news_card_html(art), ...)
    # CSS makes the button transparent, card appears on top
```

---

## 8. Prompt Engineering

### Signal Score Calibration

The system prompt includes explicit anchor examples:
```
10: Historic event (moon landing)
9:  Central bank rate change, tech acquisition
8:  Major product launch, legislation
7:  Earnings beat, scientific study
```

Without anchors, GPT-4o scores everything 7-8 (clustering bias). Anchors spread the distribution.

### Batch Indexing

```
[1] Title: OpenAI launches GPT-5...
[2] Title: Fed cuts rates...
```

The `[N]` index format is reliable for GPT-4o to reference articles. If you just use bullet points, the AI sometimes loses track of which article is which in the response.

### One-Shot JSON Format

Including a complete example in the system prompt (not just a schema) is the most reliable way to get consistent JSON:

```python
system = """Return ONLY a JSON array:
[{"index": 1, "summary": "2 sentences", "signal_score": 7.5, ...}]"""
```

The word "ONLY" is critical — without it, GPT-4o often adds "Here's the analysis:" before the JSON.

---

## 9. Extending the App

### Add a New Source

1. Add to `fetcher.py`:
```python
def fetch_new_source(config: dict) -> list[dict]:
    # fetch data
    return [_article(title, url, "New Source", ...)]
```

2. Call it in `fetch_all_news()`:
```python
new_articles = fetch_new_source(config)
all_articles.extend(new_articles)
```

### Add Twitter/X Trends

Twitter API v2 requires a developer account. Free tier allows reading trending topics:
```python
import tweepy
client = tweepy.Client(bearer_token=os.environ["TWITTER_BEARER"])
trends = client.get_place_trends(id=1)  # 1 = worldwide
```

Convert trends to articles and feed through the same pipeline.

### Add Telegram Delivery

```python
import requests
def send_telegram(bot_token, chat_id, message):
    requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage",
                  json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"})
```

### Add Slack Delivery

```python
import requests
def send_slack(webhook_url, digest):
    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": digest["overview"]}}]
    requests.post(webhook_url, json={"blocks": blocks})
```

### Switch from SQLite to PostgreSQL

```python
import psycopg2
def _conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])
```
Change `?` placeholders to `%s`. Everything else stays the same.

---

## 10. Deployment

### Streamlit Community Cloud

1. Push to GitHub (add `data/`, `.env` to `.gitignore`)
2. [share.streamlit.io](https://share.streamlit.io) → connect repo
3. Secrets:
```toml
OPENAI_API_KEY = "sk-..."
NEWS_API_KEY = "..."
```

**Note:** SQLite data is ephemeral on Cloud. Use a persistent DB (Supabase/Railway) for production.

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

### Persistent SQLite on Fly.io

```toml
# fly.toml
[mounts]
  source = "news_data"
  destination = "/app/data"
```

---

*Built with Python, Streamlit, feedparser, OpenAI GPT-4o*
