"""
modules/agent.py
----------------
All AI-powered features: summarisation, sentiment, signal scoring,
duplicate detection, executive digest, topic classification.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
from datetime import datetime

from openai import OpenAI


def _client() -> OpenAI:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("OPENAI_API_KEY")
        except Exception:
            pass
    if not key:
        raise ValueError("OPENAI_API_KEY not set")
    return OpenAI(api_key=key)


def _call(system: str, user: str, max_tokens: int = 800, temp: float = 0.2) -> str:
    resp = _client().chat.completions.create(
        model="gpt-4o",
        max_tokens=max_tokens,
        temperature=temp,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return resp.choices[0].message.content.strip()


def _safe_json(text: str) -> dict | list:
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        m = re.search(r"[\[{].*[\]}]", cleaned, re.DOTALL)
        if m:
            return json.loads(m.group())
        return {}


def _cache_key(prefix: str, content: str) -> str:
    return f"{prefix}:{hashlib.md5(content.encode()).hexdigest()[:10]}"


# ── 1. Batch Article Analysis ─────────────────────────────────────────────────

def analyse_article(title: str, summary: str, source: str) -> dict:
    """
    Analyse a single article: summary, sentiment, signal score, topics.
    Returns {summary, sentiment, signal_score, topics}.
    """
    from modules import database
    key = _cache_key("analysis", title + summary[:100])
    cached = database.get_cached(key) if hasattr(database, "get_cached") else None

    system = """You are an expert news analyst for a senior executive briefing.
Analyse this article and return ONLY valid JSON (no markdown) with:
{
  "summary": "2-sentence summary of what this story means and why it matters",
  "sentiment": "positive|negative|neutral",
  "signal_score": 7.5,
  "topics": ["Technology", "AI"],
  "is_high_signal": true,
  "why_matters": "One sentence on strategic significance"
}
signal_score: 0-10 where 10 = major global story, 1 = minor/routine.
High signal (>=7): market-moving, policy-changing, breakthrough, major company news.
topics: use standard categories: Technology, AI, Business, Finance, Science, Health, Politics, World, Energy, Crypto."""

    user = f"Title: {title}\nSource: {source}\nContent: {summary[:600]}"
    raw = _call(system, user, max_tokens=300, temp=0.1)
    result = _safe_json(raw)
    if not isinstance(result, dict):
        return {"summary": summary[:200], "sentiment": "neutral", "signal_score": 3.0,
                "topics": [], "is_high_signal": False, "why_matters": ""}
    return result


def batch_analyse(articles: list[dict], max_batch: int = 5) -> list[dict]:
    """
    Batch-analyse multiple articles in one GPT call for efficiency.
    Returns articles with AI fields populated.
    """
    if not articles:
        return []

    # Build compact batch
    batch_text = "\n\n".join([
        f"[{i+1}] Title: {a['title']}\nSource: {a['source']}\nSnippet: {a.get('summary','')[:200]}"
        for i, a in enumerate(articles[:max_batch])
    ])

    system = """You are a senior news analyst. Analyse each article and return ONLY a JSON array.
Each element must have: index (1-based), summary (2 sentences), sentiment (positive|negative|neutral),
signal_score (0-10), topics (array of strings from: Technology AI Business Finance Science Health
Politics World Energy Crypto Sports), is_high_signal (bool), why_matters (1 sentence).
Return ONLY the JSON array, no other text."""

    raw = _call(system, batch_text, max_tokens=1500, temp=0.1)
    results = _safe_json(raw)

    if not isinstance(results, list):
        return articles

    result_map = {r.get("index", 0): r for r in results}
    enriched = []
    for i, article in enumerate(articles[:max_batch], 1):
        ai = result_map.get(i, {})
        article["summary"] = ai.get("summary", article.get("summary", ""))[:500]
        article["sentiment"] = ai.get("sentiment", "neutral")
        article["signal_score"] = float(ai.get("signal_score", 3.0))
        article["topics"] = ai.get("topics", article.get("topics", []))
        article["why_matters"] = ai.get("why_matters", "")
        article["is_high_signal"] = ai.get("is_high_signal", False)
        enriched.append(article)
    return enriched


# ── 2. Duplicate Detection ────────────────────────────────────────────────────

def detect_duplicates(articles: list[dict]) -> list[dict]:
    """
    Detect near-duplicate articles (same story from different sources).
    Marks duplicates with is_duplicate=True, keeping the highest-signal version.
    Uses title similarity heuristic first, then GPT for ambiguous cases.
    """
    if len(articles) <= 1:
        return articles

    # Step 1: Fast dedup by title similarity (no API call)
    def _normalise(title: str) -> str:
        return re.sub(r"[^a-z0-9 ]", "", title.lower())

    seen_titles: dict[str, int] = {}  # normalised title -> first index
    for i, a in enumerate(articles):
        norm = _normalise(a["title"])
        # Check if any existing title shares >60% of words
        words = set(norm.split())
        duplicate = False
        for existing_norm, existing_idx in seen_titles.items():
            existing_words = set(existing_norm.split())
            if not words or not existing_words:
                continue
            overlap = len(words & existing_words) / max(len(words | existing_words), 1)
            if overlap > 0.6:
                # Mark the lower-signal one as duplicate
                if articles[i].get("signal_score", 0) >= articles[existing_idx].get("signal_score", 0):
                    articles[existing_idx]["is_duplicate"] = True
                    seen_titles[norm] = i  # replace with better version
                else:
                    articles[i]["is_duplicate"] = True
                duplicate = True
                break
        if not duplicate:
            seen_titles[norm] = i

    return articles


# ── 3. Executive Digest ───────────────────────────────────────────────────────

def generate_executive_digest(articles: list[dict], prefs: dict) -> dict:
    """
    Generate a complete executive news digest from a list of articles.
    Returns {title, date, overview, sections, key_themes, action_items, full_text}.
    """
    # Take top high-signal articles
    top = sorted(articles, key=lambda x: x.get("signal_score", 0), reverse=True)[:15]

    articles_text = "\n\n".join([
        f"• [{a['source']}] {a['title']}\n  Summary: {a.get('summary','')[:200]}\n  Signal: {a.get('signal_score',0):.1f}"
        for a in top
    ])

    topics_pref = ", ".join(prefs.get("topics", []))

    system = """You are an elite business intelligence analyst writing a C-suite morning briefing.
Return ONLY valid JSON with:
{
  "title": "Morning Intelligence Brief — [Date]",
  "overview": "2-3 sentence executive overview of today's most important developments",
  "key_themes": ["theme 1", "theme 2", "theme 3"],
  "sections": [
    {
      "category": "Technology & AI",
      "headline": "One bold headline for this section",
      "stories": [{"title": "...", "insight": "1-sentence strategic insight"}],
      "takeaway": "What executives should note"
    }
  ],
  "market_signals": ["signal 1", "signal 2"],
  "action_items": ["Consider... 1", "Monitor... 2"],
  "sentiment_overview": "positive|mixed|negative",
  "word_of_day": "One word that defines today's news cycle"
}
Group into 3-4 logical sections by topic. Be precise, strategic, actionable."""

    user = f"""Focus areas: {topics_pref}
Date: {datetime.now().strftime('%A, %B %d, %Y')}

Top stories:
{articles_text}"""

    raw = _call(system, user, max_tokens=1500, temp=0.3)
    result = _safe_json(raw)
    if not isinstance(result, dict):
        return {"title": "Daily Brief", "overview": raw, "sections": [], "key_themes": []}

    # Build plain-text version for email
    result["full_text"] = _digest_to_text(result)
    return result


def _digest_to_text(digest: dict) -> str:
    lines = [
        f"{'='*60}",
        digest.get("title", "Daily News Brief").upper(),
        f"{'='*60}",
        "",
        "OVERVIEW",
        "-"*40,
        digest.get("overview", ""),
        "",
        f"Word of the Day: {digest.get('word_of_day', '')}",
        f"Overall Sentiment: {digest.get('sentiment_overview', '')}",
        "",
    ]
    for section in digest.get("sections", []):
        lines += [
            section.get("category", "").upper(),
            "-"*40,
            f"▶ {section.get('headline', '')}",
        ]
        for story in section.get("stories", []):
            lines.append(f"  • {story.get('title', '')}: {story.get('insight', '')}")
        lines += [f"TAKEAWAY: {section.get('takeaway', '')}", ""]

    if digest.get("action_items"):
        lines += ["ACTION ITEMS", "-"*40]
        for item in digest["action_items"]:
            lines.append(f"→ {item}")
    return "\n".join(lines)


# ── 4. Sentiment Analysis ─────────────────────────────────────────────────────

def analyse_sentiment_batch(articles: list[dict]) -> list[dict]:
    """Quick sentiment pass on up to 20 articles."""
    if not articles:
        return articles

    titles = "\n".join([f"{i+1}. {a['title']}" for i, a in enumerate(articles[:20])])

    system = """Analyse news sentiment. Return ONLY a JSON array of objects, one per headline:
[{"index": 1, "sentiment": "positive|negative|neutral", "score": 0.8}]
score: -1.0 (very negative) to 1.0 (very positive). 0 = neutral."""

    raw = _call(system, titles, max_tokens=600, temp=0.1)
    results = _safe_json(raw)

    if not isinstance(results, list):
        return articles

    for r in results:
        idx = r.get("index", 0) - 1
        if 0 <= idx < len(articles):
            articles[idx]["sentiment"] = r.get("sentiment", "neutral")
            articles[idx]["sentiment_score"] = r.get("score", 0.0)
    return articles


# ── 5. High-Signal Story Detection ───────────────────────────────────────────

def detect_high_signal(articles: list[dict]) -> list[dict]:
    """
    Identify the 5-10 highest-signal stories from a batch.
    Returns them sorted by signal_score descending.
    """
    high = [a for a in articles if float(a.get("signal_score", 0)) >= 7.0]
    high.sort(key=lambda x: float(x.get("signal_score", 0)), reverse=True)
    return high[:10]


# ── 6. Topic Classification ───────────────────────────────────────────────────

def classify_topics(articles: list[dict]) -> list[dict]:
    """Classify articles into topics using keyword matching + optional AI."""
    TOPIC_KEYWORDS = {
        "AI": ["ai", "artificial intelligence", "machine learning", "gpt", "llm", "openai",
               "deepmind", "neural", "chatgpt", "gemini", "claude"],
        "Technology": ["tech", "software", "hardware", "app", "startup", "silicon valley",
                       "smartphone", "cloud", "cybersecurity", "hack"],
        "Finance": ["stock", "market", "ipo", "investment", "fund", "bank", "interest rate",
                    "inflation", "fed", "nasdaq", "wall street", "gdp"],
        "Business": ["merger", "acquisition", "ceo", "revenue", "profit", "earnings",
                     "company", "corporate", "industry"],
        "Science": ["research", "study", "discovery", "climate", "space", "nasa",
                    "biology", "physics", "quantum"],
        "Health": ["health", "medical", "drug", "vaccine", "hospital", "disease",
                   "fda", "cancer", "mental health"],
        "Politics": ["election", "government", "president", "policy", "congress",
                     "senate", "law", "regulation", "trump", "biden"],
        "Energy": ["oil", "gas", "solar", "renewable", "electric", "battery",
                   "climate change", "carbon", "energy"],
        "Crypto": ["bitcoin", "ethereum", "crypto", "blockchain", "defi", "nft", "web3"],
    }

    for article in articles:
        if article.get("topics"):
            continue  # Already has topics
        text = (article.get("title", "") + " " + article.get("summary", "")).lower()
        found = []
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                found.append(topic)
        article["topics"] = found or ["General"]
    return articles


# ── 7. Story Trend Detection ──────────────────────────────────────────────────

def detect_trending_themes(articles: list[dict]) -> list[dict]:
    """
    Identify 5 emerging themes or narratives from the article batch.
    Returns [{theme, count, articles, momentum}].
    """
    if not articles:
        return []

    sample = articles[:30]
    titles_text = "\n".join([f"- {a['title']}" for a in sample])

    system = """Identify emerging themes from these news headlines.
Return ONLY valid JSON array with 5 objects:
[{
  "theme": "Theme name (2-4 words)",
  "count": 3,
  "momentum": "rising|stable|fading",
  "summary": "One sentence on why this theme is trending",
  "impact": "high|medium|low"
}]
Sort by importance (high impact first)."""

    raw = _call(system, titles_text, max_tokens=600, temp=0.2)
    result = _safe_json(raw)
    return result if isinstance(result, list) else []


# ── 8. Article Q&A ────────────────────────────────────────────────────────────

def ask_about_news(question: str, articles: list[dict]) -> str:
    """Answer a question about the current news feed."""
    context = "\n\n".join([
        f"[{a['source']}] {a['title']}: {a.get('summary','')[:200]}"
        for a in sorted(articles, key=lambda x: x.get("signal_score", 0), reverse=True)[:15]
    ])

    system = """You are a news analyst assistant. Answer questions about today's news.
Be precise, cite sources, and highlight what matters most. If you don't have info, say so."""

    return _call(system, f"Question: {question}\n\nToday's news:\n{context}",
                 max_tokens=500, temp=0.4)


# ── Add cache to database ─────────────────────────────────────────────────────

def _add_cache_to_db():
    """Monkey-patch get_cached/set_cache into database module if missing."""
    from modules import database
    if not hasattr(database, "get_cached"):
        import sqlite3
        def get_cached(key):
            try:
                c = database._conn()
                c.execute("""CREATE TABLE IF NOT EXISTS ai_cache
                    (cache_key TEXT PRIMARY KEY, result TEXT, created_at TEXT)""")
                row = c.execute("SELECT result FROM ai_cache WHERE cache_key=?", (key,)).fetchone()
                c.close()
                return row[0] if row else None
            except Exception:
                return None

        def set_cache(key, result):
            try:
                c = database._conn()
                c.execute("""CREATE TABLE IF NOT EXISTS ai_cache
                    (cache_key TEXT PRIMARY KEY, result TEXT, created_at TEXT)""")
                c.execute("INSERT OR REPLACE INTO ai_cache (cache_key, result, created_at) VALUES (?,?,?)",
                          (key, result, datetime.now().isoformat()))
                c.commit()
                c.close()
            except Exception:
                pass

        database.get_cached = get_cached
        database.set_cache = set_cache

_add_cache_to_db()
