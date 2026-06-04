"""
Quill — Autonomous Newsletter Content Agent
===========================================

Main Streamlit entry point. Wires together content collection, AI research,
newsletter generation, automation, email delivery, export and analytics behind
a single dark-mode dashboard.

Run:
    streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from config import (
    APP_NAME, APP_TAGLINE, AppSettings, EMAIL_PROVIDERS, EXPORT_FORMATS,
    INDUSTRIES, NEWSLETTER_STYLES, SCHEDULE_FREQUENCIES, SOURCE_ICONS,
    SOURCE_TYPES, WRITING_MODES,
)
from modules import analytics, database as db
from modules import ai_features, email_integration, scheduler
from modules.ai_research import research, trending_topics
from modules.content_sources import collect_all
from modules.exporters import EXPORTERS, to_html, to_markdown
from modules.llm import LLMClient
from modules.newsletter_generator import generate_newsletter
from modules.seed_data import seed
from modules.styles import CUSTOM_CSS, stat_card

st.set_page_config(page_title=f"{APP_NAME} · Newsletter Agent", page_icon="🪶", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Bootstrap
# --------------------------------------------------------------------------- #
@st.cache_resource
def _bootstrap():
    db.init_db()
    seed()  # idempotent demo data
    return True


_bootstrap()


def get_settings() -> AppSettings:
    if "settings" not in st.session_state:
        st.session_state.settings = AppSettings()
    return st.session_state.settings


def get_llm() -> LLMClient:
    s = get_settings()
    return LLMClient(api_key=s.openai_api_key, model=s.model)


def get_creds() -> dict:
    return st.session_state.setdefault("email_creds", {})


# --------------------------------------------------------------------------- #
# Sidebar navigation
# --------------------------------------------------------------------------- #
PAGES = [
    ("Dashboard", "📊"),
    ("Content Sources", "🗂️"),
    ("Research & Collect", "🔍"),
    ("Generate Newsletter", "✨"),
    ("Drafts & Editor", "📝"),
    ("AI Studio", "🧪"),
    ("Automation", "⏰"),
    ("Deliver & Export", "📤"),
    ("Settings", "⚙️"),
]

with st.sidebar:
    st.markdown(f'<div class="brand">🪶 {APP_NAME}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="brand-sub">{APP_TAGLINE}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"
    for name, icon in PAGES:
        if st.button(f"{icon}  {name}", key=f"nav_{name}", use_container_width=True):
            st.session_state.page = name

    st.markdown("<br>", unsafe_allow_html=True)
    settings = get_settings()
    if settings.has_api_key:
        st.markdown('<span class="tag good">● OpenAI connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="tag warn">● Demo mode (no API key)</span>', unsafe_allow_html=True)
    st.caption("Add a key in Settings to enable live AI generation.")

page = st.session_state.page


# --------------------------------------------------------------------------- #
# Shared UI helpers
# --------------------------------------------------------------------------- #
def page_header(kicker: str, title: str, subtitle: str = ""):
    st.markdown(f'<div class="kicker">{kicker}</div>', unsafe_allow_html=True)
    st.markdown(f"# {title}")
    if subtitle:
        st.markdown(f'<p class="small-muted">{subtitle}</p>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


def render_newsletter_preview(news: dict):
    b = news.get("body_json", {})
    st.markdown(f"### {b.get('title', news.get('title',''))}")
    st.markdown(f'<span class="tag">{news.get("style","")}</span>'
                f'<span class="tag">{news.get("writing_mode","")}</span>'
                f'<span class="tag good">Engagement {news.get("engagement_score",0)}</span>',
                unsafe_allow_html=True)
    st.caption(f"📧 Subject: {b.get('subject_line','')}")
    st.write(b.get("introduction", ""))
    if b.get("key_insights"):
        st.markdown("#### Key Insights")
        for ins in b["key_insights"]:
            if isinstance(ins, dict):
                st.markdown(f"**{ins.get('heading','')}**")
                st.write(ins.get("body", ""))
            else:
                st.markdown(f"- {ins}")
    if b.get("industry_updates"):
        st.markdown("#### Industry Updates")
        for up in b["industry_updates"]:
            if isinstance(up, dict):
                title = up.get("headline", "")
                if up.get("url"):
                    st.markdown(f"**[{title}]({up['url']})**")
                else:
                    st.markdown(f"**{title}**")
                st.write(up.get("summary", ""))
    if b.get("actionable_takeaways"):
        st.markdown("#### Actionable Takeaways")
        for t in b["actionable_takeaways"]:
            st.markdown(f"- {t}")
    if b.get("closing"):
        st.markdown("#### Closing")
        st.write(b["closing"])
    if b.get("call_to_action"):
        st.success(f"📣 {b['call_to_action']}")


# =========================================================================== #
# PAGE: Dashboard
# =========================================================================== #
if page == "Dashboard":
    page_header("Overview", "Dashboard", "Your newsletter operation at a glance.")
    m = analytics.overview_metrics()
    cols = st.columns(4)
    cards = [
        (m["total_newsletters"], "Newsletters"),
        (m["active_sources"], "Active Sources"),
        (m["total_content"], "Content Items"),
        (f'{m["avg_engagement"]}', "Avg Engagement"),
    ]
    for col, (val, label) in zip(cols, cards):
        col.markdown(stat_card(val, label), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([3, 2])

    with left:
        st.markdown("#### Newsletters created (last 30 days)")
        series = analytics.newsletters_over_time(30)
        st.bar_chart({"newsletters": dict(series)}, height=240)

        st.markdown("#### Engagement by style")
        eng = analytics.engagement_by_style()
        if eng:
            st.bar_chart({s: v for s, v in eng}, height=220)
        else:
            st.caption("Generate newsletters to see engagement predictions.")

    with right:
        st.markdown("#### 🔥 Trending topics")
        for topic, count in analytics.trending()[:8]:
            st.markdown(f'<span class="tag">{topic}</span> '
                        f'<span class="small-muted">×{count}</span>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📡 Source usage")
        for stype, count in analytics.source_usage():
            icon = SOURCE_ICONS.get(stype, "🔗")
            st.markdown(f"{icon} **{stype}** — {count} items")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Recent newsletters")
    for n in db.list_newsletters()[:5]:
        status_cls = "good" if n["status"] == "sent" else ""
        st.markdown(
            f'<div class="item-row"><div class="item-title">{n["title"]}</div>'
            f'<div class="item-meta">{n["style"]} · {n["writing_mode"]} · '
            f'<span class="tag {status_cls}">{n["status"]}</span> '
            f'updated {n["updated_at"][:10]}</div></div>',
            unsafe_allow_html=True,
        )


# =========================================================================== #
# PAGE: Content Sources
# =========================================================================== #
elif page == "Content Sources":
    page_header("Inputs", "Content Sources", "Register where the agent collects content from.")

    with st.expander("➕ Add a new source", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            s_name = st.text_input("Source name", placeholder="e.g. Hacker News")
            s_type = st.selectbox("Type", SOURCE_TYPES,
                                  format_func=lambda t: f"{SOURCE_ICONS.get(t,'')} {t}")
            s_url = st.text_input("URL / handle / subreddit",
                                  placeholder="https://… or 'MachineLearning'")
        with c2:
            s_topic = st.text_input("Topic tag", placeholder="e.g. AI Tooling")
            s_industry = st.selectbox("Industry", INDUSTRIES)
        if st.button("Add source", type="primary"):
            if s_name:
                db.add_source(s_name, s_type, s_url, s_topic, s_industry)
                db.log_event("source_added", {"name": s_name, "type": s_type})
                st.success(f"Added {s_name}.")
                st.rerun()
            else:
                st.warning("Give the source a name.")

    sources = db.list_sources()
    st.markdown(f"#### Registered sources ({len(sources)})")
    if not sources:
        st.info("No sources yet. Add one above to get started.")
    for s in sources:
        icon = SOURCE_ICONS.get(s["source_type"], "🔗")
        c1, c2, c3, c4 = st.columns([5, 2, 1, 1])
        with c1:
            st.markdown(f"**{icon} {s['name']}**  \n"
                        f'<span class="small-muted">{s.get("url") or "—"}</span>',
                        unsafe_allow_html=True)
        with c2:
            st.markdown(f'<span class="tag">{s["source_type"]}</span>'
                        f'<span class="small-muted"> {s.get("industry","")}</span>',
                        unsafe_allow_html=True)
        with c3:
            new_active = st.toggle("On", value=bool(s["active"]), key=f"tog_{s['id']}")
            if new_active != bool(s["active"]):
                db.set_source_active(s["id"], new_active)
                st.rerun()
        with c4:
            if st.button("🗑", key=f"del_{s['id']}"):
                db.delete_source(s["id"])
                st.rerun()


# =========================================================================== #
# PAGE: Research & Collect
# =========================================================================== #
elif page == "Research & Collect":
    page_header("Pipeline", "Research & Collect",
                "Pull fresh content, deduplicate it, and surface the signal.")

    c1, c2, c3 = st.columns([2, 2, 1])
    topic = c1.text_input("Topic / theme", value=st.session_state.get("topic", "AI"))
    industry = c2.selectbox("Industry", INDUSTRIES)
    st.session_state.topic = topic

    sources = db.list_sources(active_only=True)
    chosen = st.multiselect(
        "Sources to collect from",
        options=[s["id"] for s in sources],
        default=[s["id"] for s in sources],
        format_func=lambda sid: next(
            (f"{SOURCE_ICONS.get(s['source_type'],'')} {s['name']}" for s in sources if s["id"] == sid), str(sid)
        ),
    )

    if st.button("🚀 Collect & analyze", type="primary"):
        selected = [s for s in sources if s["id"] in chosen]
        if not selected:
            st.warning("Select at least one source.")
        else:
            with st.spinner("Collecting from sources concurrently…"):
                items = collect_all(selected)
                new_count = sum(1 for it in items if db.upsert_content_item(it) is not None)
                for s in selected:
                    db.mark_source_fetched(s["id"])
            db.log_event("collect_run", {"collected": len(items), "new": new_count})
            st.success(f"Collected {len(items)} items ({new_count} new after dedup).")

            with st.spinner("Running AI research…"):
                rdata = research(items, topic, get_llm())
            st.session_state.research_data = rdata
            st.session_state.research_topic = topic
            st.session_state.research_industry = industry

    rdata = st.session_state.get("research_data")
    if rdata:
        st.markdown("---")
        st.markdown(f"#### 🧠 Research synthesis — *{st.session_state.get('research_topic','')}*")
        st.info(rdata.get("summary", ""))

        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown("**💡 Key insights**")
            for ins in rdata.get("insights", []):
                st.markdown(f"- {ins}")
        with cc2:
            st.markdown("**📈 Statistics & data points**")
            for stat in rdata.get("statistics", []) or ["No explicit statistics detected."]:
                st.markdown(f"- {stat}")

        if rdata.get("ranked_items"):
            st.markdown("**🔝 Top trending items**")
            for it in rdata["ranked_items"][:8]:
                st.markdown(
                    f'<div class="item-row"><div class="item-title">{it.get("title")}</div>'
                    f'<div class="item-meta">{SOURCE_ICONS.get(it.get("source_type"),"🔗")} '
                    f'{it.get("source_name")} · trend score {it.get("trend_score","-")}</div></div>',
                    unsafe_allow_html=True,
                )
        st.success("Research ready — head to **Generate Newsletter** to build the issue.")


# =========================================================================== #
# PAGE: Generate Newsletter
# =========================================================================== #
elif page == "Generate Newsletter":
    page_header("Create", "Generate Newsletter", "Turn research into a polished, structured issue.")

    rdata = st.session_state.get("research_data")
    if not rdata:
        st.warning("No research loaded. Run **Research & Collect** first, "
                   "or generate from existing stored content below.")

    c1, c2 = st.columns(2)
    topic = c1.text_input("Topic", value=st.session_state.get("research_topic", "AI"))
    industry = c2.selectbox("Industry", INDUSTRIES,
                            index=INDUSTRIES.index(st.session_state.get("research_industry", INDUSTRIES[0]))
                            if st.session_state.get("research_industry") in INDUSTRIES else 0)
    c3, c4 = st.columns(2)
    style = c3.selectbox("Newsletter style", list(NEWSLETTER_STYLES.keys()))
    mode = c4.selectbox("Writing mode", list(WRITING_MODES.keys()))
    st.caption(f"**{style}** → {NEWSLETTER_STYLES[style]['focus']}  |  "
               f"**{mode}** → {WRITING_MODES[mode]}")

    if st.button("✨ Generate newsletter", type="primary"):
        if not rdata:
            stored = db.query_content(topic=None, search=topic, limit=40) or db.query_content(limit=40)
            with st.spinner("Researching stored content…"):
                rdata = research(stored, topic, get_llm())
        with st.spinner("Writing your newsletter…"):
            news = generate_newsletter(
                topic=topic, industry=industry, style=style, writing_mode=mode,
                research_data=rdata, llm=get_llm(),
                references=rdata.get("ranked_items", [])[:12],
            )
            news_id = db.save_newsletter(news)
            news["id"] = news_id
            db.log_event("newsletter_generated", {"id": news_id, "style": style})
        st.session_state.current_newsletter_id = news_id
        st.success(f"Generated “{news['title']}” — saved as draft #{news_id}.")
        st.balloons()

    cur_id = st.session_state.get("current_newsletter_id")
    if cur_id:
        news = db.get_newsletter(cur_id)
        if news:
            st.markdown("---")
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            render_newsletter_preview(news)
            st.markdown("</div>", unsafe_allow_html=True)
            st.info("Refine it in **Drafts & Editor**, or send it via **Deliver & Export**.")


# =========================================================================== #
# PAGE: Drafts & Editor
# =========================================================================== #
elif page == "Drafts & Editor":
    page_header("Manage", "Drafts & Editor", "Search, edit and manage every newsletter.")

    f1, f2, f3 = st.columns([2, 1, 1])
    search = f1.text_input("🔎 Search", placeholder="title or topic…")
    status_filter = f2.selectbox("Status", ["All", "draft", "sent"])
    sort_recent = f3.selectbox("Sort", ["Most recent", "Engagement"])

    items = db.list_newsletters(
        status=None if status_filter == "All" else status_filter,
        search=search or None,
    )
    if sort_recent == "Engagement":
        items.sort(key=lambda n: n.get("engagement_score", 0), reverse=True)

    if not items:
        st.info("No newsletters match. Generate one to begin.")
    for n in items:
        with st.expander(f"{'📤' if n['status']=='sent' else '📝'}  {n['title']}  "
                         f"· {n['style']} · ★{n.get('engagement_score',0)}"):
            b = n["body_json"]
            nt = st.text_input("Title", value=b.get("title", ""), key=f"t_{n['id']}")
            ns = st.text_input("Subject line", value=b.get("subject_line", ""), key=f"s_{n['id']}")
            ni = st.text_area("Introduction", value=b.get("introduction", ""), key=f"i_{n['id']}", height=120)
            nc = st.text_area("Closing", value=b.get("closing", ""), key=f"c_{n['id']}", height=80)
            ncta = st.text_input("Call to action", value=b.get("call_to_action", ""), key=f"cta_{n['id']}")

            cc1, cc2, cc3, cc4 = st.columns(4)
            if cc1.button("💾 Save", key=f"save_{n['id']}"):
                b.update({"title": nt, "subject_line": ns, "introduction": ni,
                          "closing": nc, "call_to_action": ncta})
                db.update_newsletter(n["id"], {
                    "title": nt, "subject_line": ns, "body_json": b,
                })
                st.success("Saved.")
                st.rerun()
            if cc2.button("👁 Preview", key=f"prev_{n['id']}"):
                st.session_state[f"show_prev_{n['id']}"] = not st.session_state.get(f"show_prev_{n['id']}", False)
            if cc3.button("📤 Mark sent", key=f"sent_{n['id']}"):
                db.update_newsletter(n["id"], {"status": "sent"})
                st.rerun()
            if cc4.button("🗑 Delete", key=f"d_{n['id']}"):
                db.delete_newsletter(n["id"])
                st.rerun()

            if st.session_state.get(f"show_prev_{n['id']}"):
                st.markdown("---")
                render_newsletter_preview(n)


# =========================================================================== #
# PAGE: AI Studio
# =========================================================================== #
elif page == "AI Studio":
    page_header("Ideate", "AI Studio",
                "Subject lines, hooks, CTAs, gap analysis and a forward content calendar.")
    llm = get_llm()
    topic = st.text_input("Topic", value=st.session_state.get("research_topic", "AI"))
    style = st.selectbox("Style context", list(NEWSLETTER_STYLES.keys()))
    industry = st.selectbox("Industry", INDUSTRIES)

    tabs = st.tabs(["📧 Subject lines", "📣 CTAs", "🎣 Hooks",
                    "🧭 Content gaps", "🗓 Future ideas"])

    with tabs[0]:
        cur = st.text_input("Current subject (optional)", key="cur_subj")
        if st.button("Generate subject variations"):
            with st.spinner("Thinking up subject lines…"):
                for v in ai_features.subject_line_variations(topic, cur, style, llm):
                    st.markdown(f"- {v}")
    with tabs[1]:
        if st.button("Generate CTA suggestions"):
            with st.spinner("Drafting CTAs…"):
                for v in ai_features.cta_suggestions(topic, style, llm):
                    st.markdown(f"- {v}")
    with tabs[2]:
        if st.button("Generate hooks"):
            with st.spinner("Writing hooks…"):
                for v in ai_features.newsletter_hooks(topic, style, llm):
                    st.markdown(f"- {v}")
    with tabs[3]:
        if st.button("Find content gaps"):
            existing = [n["title"] for n in db.list_newsletters()]
            with st.spinner("Analyzing coverage…"):
                for v in ai_features.content_recommendations(topic, existing, llm):
                    st.markdown(f"- {v}")
    with tabs[4]:
        if st.button("Plan future issues"):
            with st.spinner("Building your content calendar…"):
                for v in ai_features.future_ideas(topic, industry, style, llm):
                    st.markdown(f"- {v}")


# =========================================================================== #
# PAGE: Automation
# =========================================================================== #
elif page == "Automation":
    page_header("Autopilot", "Automation",
                "Schedule recurring issues — the agent collects, writes and saves drafts for you.")

    with st.expander("➕ New schedule", expanded=False):
        c1, c2 = st.columns(2)
        sc_name = c1.text_input("Schedule name", placeholder="Weekly AI Brief")
        sc_freq = c2.selectbox("Frequency", SCHEDULE_FREQUENCIES)
        c3, c4 = st.columns(2)
        sc_topic = c3.text_input("Topic", value="AI")
        sc_industry = c4.selectbox("Industry", INDUSTRIES)
        c5, c6 = st.columns(2)
        sc_style = c5.selectbox("Style", list(NEWSLETTER_STYLES.keys()))
        sc_mode = c6.selectbox("Writing mode", list(WRITING_MODES.keys()))
        if st.button("Create schedule", type="primary"):
            if sc_name:
                db.add_schedule({
                    "name": sc_name, "frequency": sc_freq, "topic": sc_topic,
                    "industry": sc_industry, "style": sc_style, "writing_mode": sc_mode,
                    "next_run": scheduler.compute_next_run(sc_freq),
                })
                st.success("Schedule created.")
                st.rerun()
            else:
                st.warning("Name the schedule.")

    due = scheduler.due_schedules()
    cta_col1, cta_col2 = st.columns([3, 1])
    cta_col1.markdown(f"#### Schedules — {len(due)} due now" if due else "#### Schedules — none due")
    if cta_col2.button("▶ Run due now", type="primary"):
        with st.spinner("Running scheduled jobs…"):
            results = scheduler.run_due(get_llm())
        if results:
            for r in results:
                st.success(f"Built “{r['title']}” from {r['items']} items (draft #{r['newsletter_id']}).")
        else:
            st.info("Nothing was due.")

    for s in db.list_schedules():
        c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
        c1.markdown(f"**⏰ {s['name']}**  \n"
                    f'<span class="small-muted">{s["topic"]} · {s["style"]} · {s["writing_mode"]}</span>',
                    unsafe_allow_html=True)
        c2.markdown(f'<span class="tag">{s["frequency"]}</span>', unsafe_allow_html=True)
        c3.markdown(f'<span class="small-muted">next: {(s.get("next_run") or "—")[:16]}</span>',
                    unsafe_allow_html=True)
        if c4.button("🗑", key=f"dels_{s['id']}"):
            db.delete_schedule(s["id"])
            st.rerun()


# =========================================================================== #
# PAGE: Deliver & Export
# =========================================================================== #
elif page == "Deliver & Export":
    page_header("Ship", "Deliver & Export", "Push to your ESP or download in any format.")

    newsletters = db.list_newsletters()
    if not newsletters:
        st.info("No newsletters yet. Generate one first.")
        st.stop()

    sel = st.selectbox(
        "Newsletter", newsletters,
        format_func=lambda n: f"{n['title']} ({n['status']})",
    )

    tab_export, tab_email, tab_html = st.tabs(["📁 Export", "✉️ Send via ESP", "🖥 HTML preview"])

    with tab_export:
        st.markdown("Download the issue in any format:")
        cols = st.columns(len(EXPORT_FORMATS))
        for col, fmt in zip(cols, EXPORT_FORMATS):
            fn, mime, ext = EXPORTERS[fmt]
            data = fn(sel)
            if isinstance(data, str):
                data = data.encode("utf-8")
            col.download_button(
                f"⬇ {fmt}", data=data,
                file_name=f"{sel['title'][:40].replace(' ', '_')}.{ext}",
                mime=mime, key=f"dl_{fmt}", use_container_width=True,
            )
        st.markdown("---")
        st.markdown("**Markdown preview**")
        st.code(to_markdown(sel), language="markdown")

    with tab_email:
        provider = st.selectbox("Provider", EMAIL_PROVIDERS)
        creds = get_creds()
        st.caption("Credentials are entered in **Settings** and kept only in this session.")
        if st.button(f"Create draft / send via {provider}", type="primary"):
            with st.spinner(f"Talking to {provider}…"):
                res = email_integration.deliver(provider, sel, creds)
            (st.success if res["ok"] else st.warning)(res["message"])
            if res["payload"]:
                with st.expander("Provider payload / draft"):
                    st.json({k: (v[:1000] + "…" if isinstance(v, str) and len(v) > 1000 else v)
                             for k, v in res["payload"].items()})

    with tab_html:
        st.components.v1.html(to_html(sel), height=700, scrolling=True)


# =========================================================================== #
# PAGE: Settings
# =========================================================================== #
elif page == "Settings":
    page_header("Configure", "Settings", "API keys and email provider credentials (session-only).")
    s = get_settings()

    st.markdown("#### 🔑 OpenAI")
    key = st.text_input("OpenAI API key", value=s.openai_api_key, type="password",
                        placeholder="sk-…")
    model = st.selectbox("Model", ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
                         index=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"].index(s.model)
                         if s.model in ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"] else 0)
    if st.button("Save OpenAI settings", type="primary"):
        s.openai_api_key = key
        s.model = model
        st.success("Saved for this session." if key else "Cleared — running in demo mode.")

    st.markdown("---")
    st.markdown("#### ✉️ Email / ESP credentials")
    creds = get_creds()
    with st.expander("Gmail (SMTP App Password)"):
        creds["gmail_address"] = st.text_input("Gmail address", value=creds.get("gmail_address", ""),
                                               key="cred_gmail_addr")
        creds["gmail_app_password"] = st.text_input("App password", type="password",
                                                     value=creds.get("gmail_app_password", ""),
                                                     key="cred_gmail_pw")
        creds["recipient"] = st.text_input("Test recipient", value=creds.get("recipient", ""),
                                           key="cred_gmail_rcpt")
    with st.expander("Mailchimp"):
        creds["mailchimp_api_key"] = st.text_input("API key", type="password",
                                                   value=creds.get("mailchimp_api_key", ""),
                                                   key="cred_mc_key")
        creds["mailchimp_list_id"] = st.text_input("Audience/List ID", value=creds.get("mailchimp_list_id", ""),
                                                   key="cred_mc_list")
    with st.expander("ConvertKit"):
        creds["convertkit_api_secret"] = st.text_input("API secret", type="password",
                                                       value=creds.get("convertkit_api_secret", ""),
                                                       key="cred_ck_secret")
    with st.expander("Beehiiv"):
        creds["beehiiv_api_key"] = st.text_input("API key", type="password",
                                                 value=creds.get("beehiiv_api_key", ""),
                                                 key="cred_bh_key")
        creds["beehiiv_publication_id"] = st.text_input("Publication ID",
                                                        value=creds.get("beehiiv_publication_id", ""),
                                                        key="cred_bh_pub")
    if st.button("Save email credentials"):
        st.success("Email credentials stored for this session.")

    st.markdown("---")
    st.markdown("#### 🧹 Data")
    if st.button("Reset demo data"):
        seed(force=True)
        st.success("Demo data reseeded.")
