"""
Newsletter Content Creation Agent
=================================
A Streamlit app that researches recent news and generates a full newsletter
(title, subject line, intro, key insights, conclusion, CTA) with OpenAI GPT-4o.

Run:  streamlit run app.py
"""

import os
import sys

# When this app is launched from a nested path (e.g. Streamlit Cloud runs from
# the repo root, not the app folder), the directory containing `modules/` is not
# automatically on sys.path. Add it explicitly so local imports always resolve.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from modules import database as db
from modules import news, ai, newsletter, styles, seed

# --------------------------------------------------------------------------- #
# Setup
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Newsletter Agent",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()
seed.seed_if_empty()
styles.inject()

STYLES = ["Professional", "Casual", "Storytelling", "Technical", "Witty", "Inspirational"]
LENGTHS = ["Short", "Medium", "Long"]


def _has_keys():
    return bool(db.get_setting("openai_key")) and bool(db.get_setting("newsapi_key"))


# --------------------------------------------------------------------------- #
# Sidebar navigation
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.markdown('<div class="sidebar-brand">📰 Newsletter <span>Agent</span></div>',
                unsafe_allow_html=True)
    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "✍️ Create Newsletter", "🗂️ History", "⚙️ Settings"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    if _has_keys():
        st.success("API keys configured", icon="✅")
    else:
        st.warning("Add API keys in Settings", icon="⚠️")
    st.caption("Powered by OpenAI GPT-4o + NewsAPI")


# --------------------------------------------------------------------------- #
# Dashboard
# --------------------------------------------------------------------------- #
def render_dashboard():
    styles.hero("Newsletter Content Creation Agent",
                "Turn the latest news into a polished newsletter in one click.")

    total = db.count_newsletters()
    recent = db.list_newsletters(limit=3)
    last_topic = recent[0]["topic"] if recent else "—"

    c1, c2, c3 = st.columns(3)
    c1.markdown(styles.stat_card(total, "Newsletters Created"), unsafe_allow_html=True)
    c2.markdown(styles.stat_card("GPT-4o", "AI Engine"), unsafe_allow_html=True)
    c3.markdown(styles.stat_card(last_topic[:14] or "—", "Last Topic"), unsafe_allow_html=True)

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
        with st.container():
            st.markdown(
                f'<div class="article-chip"><div class="t">{nl["title"]}</div>'
                f'<div class="m">{nl["topic"]} · {nl["style"]} · {nl["created_at"]}</div></div>',
                unsafe_allow_html=True,
            )


# --------------------------------------------------------------------------- #
# Create Newsletter
# --------------------------------------------------------------------------- #
def render_create():
    styles.hero("Create a Newsletter", "Describe what you want, and the agent does the research + writing.")

    if not _has_keys():
        st.warning("⚠️ Add your OpenAI and NewsAPI keys in **Settings** before generating.")
        return

    prefs = db.get_setting("preferences", {}) or {}

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
    openai_key = db.get_setting("openai_key")
    newsapi_key = db.get_setting("newsapi_key")

    try:
        with st.status("Working on your newsletter…", expanded=True) as status:
            status.write("🔎 Researching the latest news…")
            articles = news.research(topic, newsapi_key, count=num_articles)
            if not articles:
                status.update(label="No articles found", state="error")
                st.error("NewsAPI returned no usable articles for that topic. "
                         "Try a broader or different topic.")
                return
            status.write(f"📰 Selected {len(articles)} unique articles.")

            status.write("🧠 Summarizing and extracting insights…")
            summaries = ai.summarize_articles(articles, openai_key)

            status.write("✍️ Writing the newsletter…")
            generated = ai.generate_newsletter(topic, audience, style, length,
                                                summaries, openai_key)

            md = newsletter.build_markdown(generated, summaries)
            status.update(label="Newsletter ready!", state="complete")

        record_id = db.save_newsletter({
            "title": generated.get("title", ""),
            "subject": generated.get("subject_line", ""),
            "topic": topic,
            "audience": audience,
            "style": style,
            "length": length,
            "content_md": md,
            "sources": [{"title": s["title"], "source": s["source"], "url": s["url"]}
                        for s in summaries],
        })
        db.set_setting("preferences", {
            "topic": topic, "audience": audience, "style": style, "length": length,
        })

        st.session_state["result"] = {
            "title": generated.get("title", ""),
            "subject": generated.get("subject_line", ""),
            "markdown": md,
            "articles": articles,
            "id": record_id,
        }
    except news.NewsAPIError as exc:
        st.error(f"News research failed: {exc}")
    except ai.AIError as exc:
        st.error(f"AI processing failed: {exc}")
    except Exception as exc:  # pragma: no cover - safety net
        st.error(f"Unexpected error: {exc}")


def _render_result():
    result = st.session_state.get("result")
    if not result:
        return

    st.success(f"✅ Generated: **{result['title']}**")
    if result.get("subject"):
        st.caption(f"Subject line: {result['subject']}")

    # Researched sources used
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
        styles.copy_button(result["markdown"])
    with col_dl:
        st.download_button(
            "⬇️ Download as Markdown",
            data=result["markdown"],
            file_name=f"{_slug(result['title'])}.md",
            mime="text/markdown",
            use_container_width=True,
        )


# --------------------------------------------------------------------------- #
# History
# --------------------------------------------------------------------------- #
def render_history():
    styles.hero("Newsletter History", "Everything the agent has generated, newest first.")
    items = db.list_newsletters(limit=50)
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
                st.download_button(
                    "⬇️ Download",
                    data=nl["content_md"],
                    file_name=f"{_slug(nl['title'])}.md",
                    mime="text/markdown",
                    key=f"dl_{nl['id']}",
                    use_container_width=True,
                )
            with c2:
                if st.button("🗑️ Delete", key=f"del_{nl['id']}", use_container_width=True):
                    db.delete_newsletter(nl["id"])
                    st.rerun()


# --------------------------------------------------------------------------- #
# Settings
# --------------------------------------------------------------------------- #
def render_settings():
    styles.hero("Settings", "Store your API keys and default preferences locally.")

    prefs = db.get_setting("preferences", {}) or {}

    with st.form("settings_form"):
        st.subheader("🔑 API Keys")
        openai_key = st.text_input("OpenAI API Key", type="password",
                                   value=db.get_setting("openai_key", ""),
                                   placeholder="sk-...")
        newsapi_key = st.text_input("NewsAPI Key", type="password",
                                    value=db.get_setting("newsapi_key", ""),
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
        db.save_settings({
            "openai_key": openai_key.strip(),
            "newsapi_key": newsapi_key.strip(),
            "preferences": {
                "topic": d_topic, "audience": d_audience,
                "style": d_style, "length": d_length,
            },
        })
        st.success("Settings saved locally. ✅")

    st.markdown("---")
    st.caption("Keys are stored in a local SQLite file (`newsletter.db`) on this "
               "machine only. Get an OpenAI key at platform.openai.com and a free "
               "NewsAPI key at newsapi.org.")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _safe_index(options, value, default=0):
    try:
        return options.index(value)
    except (ValueError, TypeError):
        return default


def _slug(text: str) -> str:
    import re
    text = (text or "newsletter").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "newsletter"


# --------------------------------------------------------------------------- #
# Router
# --------------------------------------------------------------------------- #
if page.startswith("📊"):
    render_dashboard()
elif page.startswith("✍️"):
    render_create()
elif page.startswith("🗂️"):
    render_history()
elif page.startswith("⚙️"):
    render_settings()
