"""
Newsletter Content Creation Agent — single-file build
======================================================
Everything (DB, NewsAPI research, OpenAI processing, Markdown assembly, UI) is
inlined into this one file so there are NO local package imports. This avoids
the `ModuleNotFoundError: modules` problem on Streamlit Cloud entirely.

Run:  streamlit run app.py
Deps: streamlit, openai, requests
"""

import os
import re
import json
import sqlite3
from datetime import datetime
from contextlib import contextmanager

import requests
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI, OpenAIError

# =========================================================================== #
# Constants
# =========================================================================== #
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "newsletter.db")
MODEL = "gpt-4o"
NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"

STYLES = ["Professional", "Casual", "Storytelling", "Technical", "Witty", "Inspirational"]
LENGTHS = ["Short", "Medium", "Long"]
LENGTH_GUIDE = {
    "Short": "around 250-350 words total, punchy and skimmable",
    "Medium": "around 500-650 words total, balanced detail",
    "Long": "around 900-1100 words total, in-depth and thorough",
}


class NewsAPIError(Exception):
    pass


class AIError(Exception):
    pass


# =========================================================================== #
# Database (SQLite)
# =========================================================================== #
@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _conn() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS newsletters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT, subject TEXT, topic TEXT, audience TEXT,
                style TEXT, length TEXT, content_md TEXT, sources TEXT, created_at TEXT
            )
            """
        )


def set_setting(key, value):
    if not isinstance(value, str):
        value = json.dumps(value)
    with _conn() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def get_setting(key, default=None):
    with _conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if row is None:
        return default
    try:
        return json.loads(row["value"])
    except (json.JSONDecodeError, TypeError):
        return row["value"]


def save_settings(data: dict):
    for k, v in data.items():
        set_setting(k, v)


def save_newsletter(data: dict) -> int:
    with _conn() as conn:
        cur = conn.execute(
            """INSERT INTO newsletters
               (title, subject, topic, audience, style, length, content_md, sources, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data.get("title", ""), data.get("subject", ""), data.get("topic", ""),
                data.get("audience", ""), data.get("style", ""), data.get("length", ""),
                data.get("content_md", ""), json.dumps(data.get("sources", [])),
                datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )
        return cur.lastrowid


def list_newsletters(limit: int = 50) -> list:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM newsletters ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    out = []
    for row in rows:
        item = dict(row)
        try:
            item["sources"] = json.loads(item.get("sources") or "[]")
        except (json.JSONDecodeError, TypeError):
            item["sources"] = []
        out.append(item)
    return out


def delete_newsletter(newsletter_id: int):
    with _conn() as conn:
        conn.execute("DELETE FROM newsletters WHERE id = ?", (newsletter_id,))


def count_newsletters() -> int:
    with _conn() as conn:
        return conn.execute("SELECT COUNT(*) AS c FROM newsletters").fetchone()["c"]


# =========================================================================== #
# Content research (NewsAPI)
# =========================================================================== #
def _normalize_title(title: str) -> str:
    if not title:
        return ""
    title = re.sub(r"[^a-z0-9 ]+", "", title.lower())
    return re.sub(r"\s+", " ", title).strip()


def _clean_article(article: dict) -> dict:
    source = article.get("source") or {}
    return {
        "title": (article.get("title") or "").strip(),
        "description": (article.get("description") or "").strip(),
        "content": (article.get("content") or "").strip(),
        "url": article.get("url") or "",
        "source": source.get("name") or "Unknown",
        "published_at": article.get("publishedAt") or "",
        "image": article.get("urlToImage") or "",
    }


def fetch_articles(topic, api_key, page_size=30, language="en", sort_by="publishedAt"):
    if not api_key:
        raise NewsAPIError("Missing NewsAPI key. Add it in Settings.")
    if not topic or not topic.strip():
        raise NewsAPIError("Please provide a newsletter topic.")

    params = {
        "q": topic.strip(), "language": language, "sortBy": sort_by,
        "pageSize": min(max(page_size, 1), 100), "apiKey": api_key,
    }
    try:
        resp = requests.get(NEWSAPI_ENDPOINT, params=params, timeout=20)
    except requests.RequestException as exc:
        raise NewsAPIError(f"Could not reach NewsAPI: {exc}") from exc

    if resp.status_code == 401:
        raise NewsAPIError("NewsAPI rejected the key (401). Check it in Settings.")
    if resp.status_code == 429:
        raise NewsAPIError("NewsAPI rate limit reached (429). Try again later.")

    try:
        data = resp.json()
    except ValueError as exc:
        raise NewsAPIError("NewsAPI returned an invalid response.") from exc
    if data.get("status") != "ok":
        raise NewsAPIError(data.get("message", "Unknown NewsAPI error."))

    articles = [_clean_article(a) for a in data.get("articles", [])]
    return [a for a in articles if a["title"] and a["title"].lower() != "[removed]"]


def deduplicate(articles: list) -> list:
    seen_titles, seen_urls, unique = set(), set(), []
    for art in articles:
        norm = _normalize_title(art["title"])
        url = art["url"]
        if norm in seen_titles or (url and url in seen_urls):
            continue
        seen_titles.add(norm)
        if url:
            seen_urls.add(url)
        unique.append(art)
    return unique


def _published_key(article: dict):
    raw = article.get("published_at") or ""
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return datetime.min


def select_top(articles: list, count: int = 5) -> list:
    unique = deduplicate(articles)
    with_body = [a for a in unique if a["description"] or a["content"]]
    without_body = [a for a in unique if not (a["description"] or a["content"])]
    with_body.sort(key=_published_key, reverse=True)
    without_body.sort(key=_published_key, reverse=True)
    return (with_body + without_body)[:count]


def research(topic, api_key, count=5):
    return select_top(fetch_articles(topic, api_key), count=count)


# =========================================================================== #
# AI processing (OpenAI GPT-4o)
# =========================================================================== #
def _client(api_key):
    if not api_key:
        raise AIError("Missing OpenAI API key. Add it in Settings.")
    return OpenAI(api_key=api_key)


def _parse_json(text: str):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        parts = cleaned.split("```", 2)
        cleaned = parts[1] if len(parts) > 1 else text
        if cleaned.lstrip().startswith("json"):
            cleaned = cleaned.lstrip()[4:]
    cleaned = cleaned.strip().strip("`").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AIError(f"Model returned unparseable JSON: {exc}") from exc


def summarize_articles(articles, api_key):
    if not articles:
        raise AIError("No articles to summarize.")
    client = _client(api_key)

    blocks = []
    for i, art in enumerate(articles, 1):
        body = art.get("description") or ""
        extra = art.get("content") or ""
        blocks.append(
            f"[{i}] TITLE: {art['title']}\nSOURCE: {art.get('source','')}\n"
            f"TEXT: {body} {extra}".strip()
        )
    sources_text = "\n\n".join(blocks)

    system = (
        "You are a sharp editorial research assistant. You read raw news snippets "
        "and distill them into clean, factual summaries. Never invent facts that "
        "are not present in the provided text."
    )
    user = (
        "Summarize each numbered article below. For every article produce: a 2-3 "
        "sentence neutral summary, and one standout key takeaway (a single "
        "sentence).\n\nReturn ONLY valid JSON in this exact shape, with no extra "
        'commentary:\n{ "articles": [ { "index": 1, "summary": "...", '
        '"key_point": "..." } ] }\n\n'
        f"ARTICLES:\n{sources_text}"
    )
    try:
        resp = client.chat.completions.create(
            model=MODEL, temperature=0.3,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
        )
    except OpenAIError as exc:
        raise AIError(f"OpenAI summarization failed: {exc}") from exc

    parsed = _parse_json(resp.choices[0].message.content)
    items = parsed.get("articles", []) if isinstance(parsed, dict) else []
    by_index = {it.get("index"): it for it in items if isinstance(it, dict)}

    summaries = []
    for i, art in enumerate(articles, 1):
        it = by_index.get(i, {})
        summaries.append({
            "title": art["title"],
            "summary": it.get("summary", art.get("description", "")),
            "key_point": it.get("key_point", ""),
            "source": art.get("source", ""),
            "url": art.get("url", ""),
        })
    return summaries


def generate_newsletter(topic, audience, style, length, summaries, api_key):
    if not summaries:
        raise AIError("No summaries available to build a newsletter.")
    client = _client(api_key)
    length_hint = LENGTH_GUIDE.get(length, LENGTH_GUIDE["Medium"])

    research_text = "\n\n".join(
        f"- {s['title']} ({s['source']})\n  Summary: {s['summary']}\n  Key point: {s['key_point']}"
        for s in summaries
    )
    system = (
        "You are an expert newsletter writer who turns research into engaging, "
        "well-structured editions. You match the requested tone precisely and "
        "write only from the provided research — no fabricated statistics."
    )
    user = (
        f"Write a newsletter edition.\n\nTOPIC: {topic}\nTARGET AUDIENCE: {audience}\n"
        f"WRITING STYLE: {style}\nLENGTH: {length_hint}\n\n"
        f"RESEARCH (use these as your sources):\n{research_text}\n\n"
        "Produce a newsletter with: a catchy title, an email subject line, a warm "
        "introduction, 3-5 key insights (each with a short heading and a "
        "paragraph), a concise conclusion, and a single clear call-to-action.\n\n"
        "Return ONLY valid JSON in exactly this shape:\n{\n  \"title\": \"...\",\n"
        "  \"subject_line\": \"...\",\n  \"introduction\": \"...\",\n"
        "  \"key_insights\": [ { \"heading\": \"...\", \"body\": \"...\" } ],\n"
        "  \"conclusion\": \"...\",\n  \"cta\": \"...\"\n}"
    )
    try:
        resp = client.chat.completions.create(
            model=MODEL, temperature=0.7,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
        )
    except OpenAIError as exc:
        raise AIError(f"OpenAI generation failed: {exc}") from exc

    data = _parse_json(resp.choices[0].message.content)
    if not isinstance(data, dict):
        raise AIError("Newsletter generation returned an unexpected shape.")

    norm = []
    for ins in (data.get("key_insights", []) or []):
        if isinstance(ins, dict):
            norm.append({"heading": ins.get("heading", "").strip(),
                         "body": ins.get("body", "").strip()})
        elif isinstance(ins, str):
            norm.append({"heading": "", "body": ins.strip()})
    data["key_insights"] = norm
    for field in ("title", "subject_line", "introduction", "conclusion", "cta"):
        data.setdefault(field, "")
    return data


# =========================================================================== #
# Markdown assembly
# =========================================================================== #
def build_markdown(generated: dict, summaries=None, include_sources=True) -> str:
    summaries = summaries or []
    lines = []
    title = generated.get("title", "").strip() or "Untitled Newsletter"
    subject = generated.get("subject_line", "").strip()

    lines += [f"# {title}", ""]
    if subject:
        lines += [f"**Subject line:** {subject}", ""]
    lines += [f"*{datetime.utcnow().strftime('%B %d, %Y')}*", "", "---", ""]

    intro = generated.get("introduction", "").strip()
    if intro:
        lines += [intro, ""]

    insights = generated.get("key_insights", [])
    if insights:
        lines += ["## Key Insights", ""]
        for i, ins in enumerate(insights, 1):
            heading = ins.get("heading", "").strip()
            body = ins.get("body", "").strip()
            lines.append(f"### {i}. {heading}" if heading else f"### {i}.")
            lines.append("")
            if body:
                lines += [body, ""]

    conclusion = generated.get("conclusion", "").strip()
    if conclusion:
        lines += ["## Conclusion", "", conclusion, ""]

    cta = generated.get("cta", "").strip()
    if cta:
        lines += ["---", "", f"**{cta}**", ""]

    if include_sources and summaries:
        lines += ["---", "", "### Sources", ""]
        for s in summaries:
            label = s.get("title", "Source")
            if s.get("source"):
                label += f" — *{s['source']}*"
            lines.append(f"- [{label}]({s['url']})" if s.get("url") else f"- {label}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


# =========================================================================== #
# Demo seed
# =========================================================================== #
_DEMO = [
    {
        "title": "The Agent Era: 5 Signals Worth Your Attention",
        "subject": "🤖 AI agents just leveled up — here's what changed",
        "topic": "AI agents", "audience": "AI engineers and founders",
        "style": "Professional", "length": "Medium",
        "sources": [{"title": "Sample source", "source": "Demo Wire", "url": "https://example.com/a"}],
        "content_md": (
            "# The Agent Era: 5 Signals Worth Your Attention\n\n"
            "**Subject line:** 🤖 AI agents just leveled up — here's what changed\n\n"
            "*Demo edition*\n\n---\n\nThis is a seeded sample so you can see how a "
            "finished edition looks. Generate a real one from the **Create** page.\n\n"
            "## Key Insights\n\n### 1. Tooling is consolidating\n\nFrameworks are "
            "converging on a shared agent loop pattern.\n\n## Conclusion\n\nThe "
            "building blocks are stabilizing fast.\n\n---\n\n**Reply and tell me "
            "which agent you're building next.**\n"
        ),
    },
    {
        "title": "Healthcare AI Weekly: Where Models Still Stumble",
        "subject": "🩺 The clinical AI gap nobody is talking about",
        "topic": "AI in healthcare", "audience": "Clinicians and ML researchers",
        "style": "Storytelling", "length": "Short",
        "sources": [{"title": "Sample source", "source": "Demo Health", "url": "https://example.com/b"}],
        "content_md": (
            "# Healthcare AI Weekly: Where Models Still Stumble\n\n"
            "**Subject line:** 🩺 The clinical AI gap nobody is talking about\n\n"
            "*Demo edition*\n\n---\n\nA short seeded sample edition.\n\n"
            "## Key Insights\n\n### 1. Evaluation beats hype\n\nReal de-identified "
            "cases reveal failure modes benchmarks miss.\n\n## Conclusion\n\nTrust "
            "is earned one validated case at a time.\n\n---\n\n**Forward this to a "
            "colleague who works in clinical AI.**\n"
        ),
    },
]


def seed_if_empty():
    if count_newsletters() > 0:
        return
    for item in _DEMO:
        save_newsletter(item)


# =========================================================================== #
# Styling
# =========================================================================== #
CSS = """
<style>
    .block-container { padding-top: 2.2rem; max-width: 980px; }
    html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }
    h1, h2, h3 { letter-spacing: -0.01em; }
    .app-hero {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
        padding: 1.6rem 1.8rem; border-radius: 16px; margin-bottom: 1.4rem;
        box-shadow: 0 10px 30px rgba(99,102,241,0.25);
    }
    .app-hero h1 { color:#fff; margin:0; font-size:1.7rem; font-weight:750; }
    .app-hero p  { color:rgba(255,255,255,0.85); margin:0.3rem 0 0; font-size:0.95rem; }
    .stat-card {
        background:#1a1d28; border:1px solid #262a38; border-radius:14px;
        padding:1.1rem 1.2rem; text-align:center;
    }
    .stat-card .num   { font-size:1.9rem; font-weight:750; color:#818cf8; }
    .stat-card .label { font-size:0.8rem; color:#9ca3af; text-transform:uppercase; letter-spacing:0.05em; }
    .stButton > button { border-radius:10px; border:none; font-weight:600; padding:0.55rem 1.1rem; }
    .stButton > button[kind="primary"] { background:linear-gradient(135deg,#6366f1,#8b5cf6); color:#fff; }
    .article-chip {
        background:#14161f; border:1px solid #262a38; border-left:3px solid #6366f1;
        border-radius:10px; padding:0.7rem 0.9rem; margin-bottom:0.55rem;
    }
    .article-chip .t { font-weight:600; color:#e5e7eb; font-size:0.92rem; }
    .article-chip .m { color:#9ca3af; font-size:0.78rem; margin-top:0.2rem; }
    .preview-surface {
        background:#15171f; border:1px solid #262a38; border-radius:14px; padding:1.6rem 2rem;
    }
    section[data-testid="stSidebar"] { background:#14161f; }
    .sidebar-brand { font-size:1.15rem; font-weight:750; color:#e5e7eb; padding:0.2rem 0 0.6rem; }
    .sidebar-brand span { color:#818cf8; }
    #MainMenu, footer { visibility:hidden; }
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(title, subtitle=""):
    st.markdown(f'<div class="app-hero"><h1>{title}</h1><p>{subtitle}</p></div>',
                unsafe_allow_html=True)


def stat_card(num, label):
    return (f'<div class="stat-card"><div class="num">{num}</div>'
            f'<div class="label">{label}</div></div>')


def copy_button(text, label="📋 Copy to clipboard"):
    payload = json.dumps(text)
    components.html(
        f"""
        <button id="copybtn" style="background:linear-gradient(135deg,#6366f1,#8b5cf6);
            color:#fff;border:none;border-radius:10px;padding:0.6rem 1.1rem;
            font-weight:600;cursor:pointer;font-family:'Inter',sans-serif;
            font-size:0.9rem;width:100%;">{label}</button>
        <script>
            const btn = document.getElementById("copybtn");
            btn.addEventListener("click", async () => {{
                try {{
                    await navigator.clipboard.writeText({payload});
                    btn.innerText = "✅ Copied!";
                    setTimeout(() => btn.innerText = "{label}", 1800);
                }} catch (e) {{ btn.innerText = "⚠️ Press Ctrl/Cmd+C"; }}
            }});
        </script>
        """,
        height=56,
    )


# =========================================================================== #
# App setup
# =========================================================================== #
st.set_page_config(page_title="Newsletter Agent", page_icon="📰",
                   layout="wide", initial_sidebar_state="expanded")
init_db()
seed_if_empty()
inject_css()


def _has_keys():
    return bool(get_setting("openai_key")) and bool(get_setting("newsapi_key"))


def _safe_index(options, value, default=0):
    try:
        return options.index(value)
    except (ValueError, TypeError):
        return default


def _slug(text):
    text = re.sub(r"[^a-z0-9]+", "-", (text or "newsletter").lower()).strip("-")
    return text or "newsletter"


# =========================================================================== #
# Sidebar
# =========================================================================== #
with st.sidebar:
    st.markdown('<div class="sidebar-brand">📰 Newsletter <span>Agent</span></div>',
                unsafe_allow_html=True)
    page = st.radio("Navigation",
                    ["📊 Dashboard", "✍️ Create Newsletter", "🗂️ History", "⚙️ Settings"],
                    label_visibility="collapsed")
    st.markdown("---")
    if _has_keys():
        st.success("API keys configured", icon="✅")
    else:
        st.warning("Add API keys in Settings", icon="⚠️")
    st.caption("Powered by OpenAI GPT-4o + NewsAPI")


# =========================================================================== #
# Pages
# =========================================================================== #
def render_dashboard():
    hero("Newsletter Content Creation Agent",
         "Turn the latest news into a polished newsletter in one click.")
    total = count_newsletters()
    recent = list_newsletters(limit=3)
    last_topic = recent[0]["topic"] if recent else "—"

    c1, c2, c3 = st.columns(3)
    c1.markdown(stat_card(total, "Newsletters Created"), unsafe_allow_html=True)
    c2.markdown(stat_card("GPT-4o", "AI Engine"), unsafe_allow_html=True)
    c3.markdown(stat_card((last_topic[:14] or "—"), "Last Topic"), unsafe_allow_html=True)

    st.write("")
    if not _has_keys():
        st.info("👋 First time here? Add your **OpenAI** and **NewsAPI** keys in "
                "**Settings**, then head to **Create Newsletter**.")
    else:
        st.info("✅ You're set up. Go to **Create Newsletter** to generate your next edition.")

    st.subheader("Recent newsletters")
    if not recent:
        st.caption("Nothing yet — create your first newsletter.")
    for nl in recent:
        st.markdown(
            f'<div class="article-chip"><div class="t">{nl["title"]}</div>'
            f'<div class="m">{nl["topic"]} · {nl["style"]} · {nl["created_at"]}</div></div>',
            unsafe_allow_html=True,
        )


def render_create():
    hero("Create a Newsletter", "Describe what you want, and the agent does the research + writing.")
    if not _has_keys():
        st.warning("⚠️ Add your OpenAI and NewsAPI keys in **Settings** before generating.")
        return

    prefs = get_setting("preferences", {}) or {}
    with st.form("create_form"):
        col1, col2 = st.columns(2)
        with col1:
            topic = st.text_input("Newsletter topic", value=prefs.get("topic", ""),
                                  placeholder="e.g. AI agents, climate tech, fintech")
            audience = st.text_input("Target audience", value=prefs.get("audience", ""),
                                     placeholder="e.g. AI engineers and founders")
        with col2:
            style = st.selectbox("Writing style", STYLES,
                                 index=_safe_index(STYLES, prefs.get("style"), 0))
            length = st.select_slider("Content length", LENGTHS,
                                      value=prefs.get("length", "Medium"))
        num_articles = st.slider("Articles to research", 3, 5, 5)
        submitted = st.form_submit_button("✨ Generate Newsletter", type="primary",
                                          use_container_width=True)

    if submitted:
        if not topic.strip():
            st.error("Please enter a topic.")
            return
        _run_generation(topic, audience, style, length, num_articles)
    _render_result()


def _run_generation(topic, audience, style, length, num_articles):
    openai_key = get_setting("openai_key")
    newsapi_key = get_setting("newsapi_key")
    try:
        with st.status("Working on your newsletter…", expanded=True) as status:
            status.write("🔎 Researching the latest news…")
            articles = research(topic, newsapi_key, count=num_articles)
            if not articles:
                status.update(label="No articles found", state="error")
                st.error("NewsAPI returned no usable articles for that topic. "
                         "Try a broader or different topic.")
                return
            status.write(f"📰 Selected {len(articles)} unique articles.")

            status.write("🧠 Summarizing and extracting insights…")
            summaries = summarize_articles(articles, openai_key)

            status.write("✍️ Writing the newsletter…")
            generated = generate_newsletter(topic, audience, style, length, summaries, openai_key)

            md = build_markdown(generated, summaries)
            status.update(label="Newsletter ready!", state="complete")

        record_id = save_newsletter({
            "title": generated.get("title", ""), "subject": generated.get("subject_line", ""),
            "topic": topic, "audience": audience, "style": style, "length": length,
            "content_md": md,
            "sources": [{"title": s["title"], "source": s["source"], "url": s["url"]} for s in summaries],
        })
        save_settings({"preferences": {"topic": topic, "audience": audience,
                                       "style": style, "length": length}})
        st.session_state["result"] = {
            "title": generated.get("title", ""), "subject": generated.get("subject_line", ""),
            "markdown": md, "articles": articles, "id": record_id,
        }
    except NewsAPIError as exc:
        st.error(f"News research failed: {exc}")
    except AIError as exc:
        st.error(f"AI processing failed: {exc}")
    except Exception as exc:  # pragma: no cover
        st.error(f"Unexpected error: {exc}")


def _render_result():
    result = st.session_state.get("result")
    if not result:
        return
    st.success(f"✅ Generated: **{result['title']}**")
    if result.get("subject"):
        st.caption(f"Subject line: {result['subject']}")

    with st.expander(f"🔎 Sources researched ({len(result['articles'])})"):
        for art in result["articles"]:
            st.markdown(
                f'<div class="article-chip"><div class="t">{art["title"]}</div>'
                f'<div class="m">{art["source"]} · '
                f'<a href="{art["url"]}" target="_blank">open</a></div></div>',
                unsafe_allow_html=True,
            )

    tab_preview, tab_md = st.tabs(["👀 Preview", "🔤 Markdown"])
    with tab_preview:
        st.markdown('<div class="preview-surface">', unsafe_allow_html=True)
        st.markdown(result["markdown"])
        st.markdown("</div>", unsafe_allow_html=True)
    with tab_md:
        st.code(result["markdown"], language="markdown")

    col_copy, col_dl = st.columns(2)
    with col_copy:
        copy_button(result["markdown"])
    with col_dl:
        st.download_button("⬇️ Download as Markdown", data=result["markdown"],
                           file_name=f"{_slug(result['title'])}.md",
                           mime="text/markdown", use_container_width=True)


def render_history():
    hero("Newsletter History", "Everything the agent has generated, newest first.")
    items = list_newsletters(limit=50)
    if not items:
        st.caption("No newsletters saved yet.")
        return
    for nl in items:
        with st.expander(f"📰 {nl['title']}  ·  {nl['created_at']}"):
            st.caption(f"Topic: {nl['topic']} · Audience: {nl['audience']} · "
                       f"Style: {nl['style']} · Length: {nl['length']}")
            if nl.get("subject"):
                st.caption(f"Subject line: {nl['subject']}")
            st.markdown('<div class="preview-surface">', unsafe_allow_html=True)
            st.markdown(nl["content_md"])
            st.markdown("</div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("⬇️ Download", data=nl["content_md"],
                                   file_name=f"{_slug(nl['title'])}.md",
                                   mime="text/markdown", key=f"dl_{nl['id']}",
                                   use_container_width=True)
            with c2:
                if st.button("🗑️ Delete", key=f"del_{nl['id']}", use_container_width=True):
                    delete_newsletter(nl["id"])
                    st.rerun()


def render_settings():
    hero("Settings", "Store your API keys and default preferences locally.")
    prefs = get_setting("preferences", {}) or {}
    with st.form("settings_form"):
        st.subheader("🔑 API Keys")
        openai_key = st.text_input("OpenAI API Key", type="password",
                                   value=get_setting("openai_key", ""), placeholder="sk-...")
        newsapi_key = st.text_input("NewsAPI Key", type="password",
                                    value=get_setting("newsapi_key", ""),
                                    placeholder="Your newsapi.org key")
        st.subheader("🎯 Default Preferences")
        c1, c2 = st.columns(2)
        with c1:
            d_topic = st.text_input("Default topic", value=prefs.get("topic", ""))
            d_audience = st.text_input("Default audience", value=prefs.get("audience", ""))
        with c2:
            d_style = st.selectbox("Default style", STYLES,
                                   index=_safe_index(STYLES, prefs.get("style"), 0))
            d_length = st.select_slider("Default length", LENGTHS,
                                        value=prefs.get("length", "Medium"))
        saved = st.form_submit_button("💾 Save Settings", type="primary",
                                      use_container_width=True)
    if saved:
        save_settings({
            "openai_key": openai_key.strip(), "newsapi_key": newsapi_key.strip(),
            "preferences": {"topic": d_topic, "audience": d_audience,
                            "style": d_style, "length": d_length},
        })
        st.success("Settings saved locally. ✅")
    st.markdown("---")
    st.caption("Keys are stored in a local SQLite file (`newsletter.db`). Get an "
               "OpenAI key at platform.openai.com and a free NewsAPI key at newsapi.org.")


# =========================================================================== #
# Router
# =========================================================================== #
if page.startswith("📊"):
    render_dashboard()
elif page.startswith("✍️"):
    render_create()
elif page.startswith("🗂️"):
    render_history()
elif page.startswith("⚙️"):
    render_settings()
