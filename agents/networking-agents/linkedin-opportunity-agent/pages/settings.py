"""settings.py — Configuration: API key, model, keywords, industries, monitored
profiles & companies, email digests, manual post ingestion, and data management."""

import streamlit as st

from modules import config, database as db, monitor, ui

ui.hero("Settings", "Configure the agent: API key, what to monitor, outreach identity, and alerts.")

# ── AI configuration ─────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>🔑 AI / Claude API</div>", unsafe_allow_html=True)
a1, a2 = st.columns([2, 1])
with a1:
    key = st.text_input(
        "Anthropic API key",
        value=st.session_state.get("api_key", ""),
        type="password",
        placeholder="sk-ant-…  (or set ANTHROPIC_API_KEY in Streamlit secrets)",
        help="Stored only in this session — never written to disk. On Streamlit Cloud, "
             "prefer Settings → Secrets.",
    )
    st.session_state.api_key = key
with a2:
    model = st.selectbox(
        "Model",
        list(config.MODELS.keys()),
        index=list(config.MODELS.keys()).index(config.get_model()),
        format_func=lambda m: config.MODELS[m],
    )
    st.session_state.model = model
    db.set_setting("model", model)

if config.ai_enabled():
    st.success(f"AI analysis enabled · {config.get_model()}", icon="✅")
else:
    st.info("No key set — the app runs on the deterministic keyword engine (fully functional, no cost).")

st.divider()

# ── Monitoring targets ───────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>🎯 What to monitor</div>", unsafe_allow_html=True)
m1, m2 = st.columns(2)
with m1:
    kw = st.text_area(
        "Keywords (one per line)",
        "\n".join(st.session_state.get("keywords", [])),
        height=140,
        help="Boost the score of posts mentioning these terms.",
    )
with m2:
    inds = st.text_area(
        "Target industries (one per line)",
        "\n".join(st.session_state.get("industries", [])),
        height=140,
    )
if st.button("💾 Save monitoring preferences", type="primary"):
    keywords = [k.strip() for k in kw.splitlines() if k.strip()]
    industries = [i.strip() for i in inds.splitlines() if i.strip()]
    st.session_state.keywords = keywords
    st.session_state.industries = industries
    db.set_setting("keywords", keywords)
    db.set_setting("industries", industries)
    st.success("Saved.")

# ── Monitored profiles & companies ───────────────────────────────────────────────
p1, p2 = st.columns(2)
with p1:
    st.markdown("<div class='section-title'>👤 Monitored profiles</div>", unsafe_allow_html=True)
    with st.form("add_profile", clear_on_submit=True):
        pn = st.text_input("Name")
        ph = st.text_input("Headline")
        pu = st.text_input("Profile URL")
        pc = st.text_input("Company")
        pi = st.text_input("Industry")
        if st.form_submit_button("➕ Add profile"):
            if pu:
                db.add_profile(pn, ph, pu, pc, pi)
                st.success(f"Added {pn or pu}")
            else:
                st.warning("Profile URL is required.")
    for prof in db.list_profiles():
        cols = st.columns([5, 1])
        cols[0].caption(f"**{prof['name']}** — {prof['headline']} ({prof.get('industry','')})")
        if cols[1].button("🗑", key=f"delp{prof['id']}"):
            db.delete_profile(prof["id"])
            st.rerun()

with p2:
    st.markdown("<div class='section-title'>🏢 Monitored companies</div>", unsafe_allow_html=True)
    with st.form("add_company", clear_on_submit=True):
        cn = st.text_input("Company name")
        cu = st.text_input("Company page URL")
        ci = st.text_input("Industry ")
        if st.form_submit_button("➕ Add company"):
            if cu:
                db.add_company(cn, cu, ci)
                st.success(f"Added {cn or cu}")
            else:
                st.warning("Company page URL is required.")
    for comp in db.list_companies():
        cols = st.columns([5, 1])
        cols[0].caption(f"**{comp['name']}** — {comp.get('industry','')}")
        if cols[1].button("🗑", key=f"delc{comp['id']}"):
            db.delete_company(comp["id"])
            st.rerun()

st.divider()

# ── Manual post ingestion ────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>📥 Add a post manually</div>", unsafe_allow_html=True)
st.caption(
    "Paste any LinkedIn post text to analyse it on the next scan. This is the compliant way "
    "to feed real content — LinkedIn has no public posts API, so the agent never scrapes."
)
with st.form("manual_post", clear_on_submit=True):
    mp_text = st.text_area("Post text", height=120)
    mc1, mc2, mc3 = st.columns(3)
    mp_author = mc1.text_input("Author name")
    mp_company = mc2.text_input("Company")
    mp_industry = mc3.text_input("Industry")
    if st.form_submit_button("Queue for analysis"):
        if mp_text.strip():
            added = monitor.ingest_manual_post(
                mp_text, mp_author, "", mp_company, mp_industry
            )
            if added:
                st.success("Queued. Run a scan on the Home page to analyse it.")
            else:
                st.info("That exact post is already in the queue.")
        else:
            st.warning("Post text is required.")

st.divider()

# ── Outreach identity ────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>✍️ Outreach identity</div>", unsafe_allow_html=True)
o1, o2 = st.columns(2)
sn = o1.text_input("Your name", st.session_state.get("sender_name", ""))
sr = o2.text_input("Your role / company", st.session_state.get("sender_role", ""))
if st.button("Save outreach identity"):
    st.session_state.sender_name = sn
    st.session_state.sender_role = sr
    db.set_setting("sender_name", sn)
    db.set_setting("sender_role", sr)
    st.success("Saved.")

st.divider()

# ── Email digest (SMTP) ──────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>📧 Email digests (SMTP)</div>", unsafe_allow_html=True)
e1, e2, e3 = st.columns(3)
st.session_state.smtp_host = e1.text_input("SMTP host", st.session_state.get("smtp_host", ""))
st.session_state.smtp_port = e2.text_input("SMTP port", st.session_state.get("smtp_port", "587"))
st.session_state.smtp_user = e3.text_input("SMTP user", st.session_state.get("smtp_user", ""))
e4, e5, e6 = st.columns(3)
st.session_state.smtp_password = e4.text_input(
    "SMTP password", st.session_state.get("smtp_password", ""), type="password"
)
st.session_state.alert_from = e5.text_input("From", st.session_state.get("alert_from", ""))
st.session_state.alert_to = e6.text_input("To", st.session_state.get("alert_to", ""))
if config.smtp_configured():
    st.success("Email configured — send digests from the Analytics page.", icon="✅")
else:
    st.caption("Leave blank to preview digests in-app without sending. Gmail users: use an App Password.")

st.divider()

# ── Data management ──────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>🗄 Data</div>", unsafe_allow_html=True)
st.caption("The SQLite database lives under data/. On Streamlit Cloud it resets when the "
           "container restarts — demo data is re-seeded automatically so the app is never empty.")
if st.button("⚠️ Reset all opportunities & posts"):
    db.delete_all_opportunities()
    st.session_state._booted = False  # re-seed demo on next load
    st.success("Cleared. Reloading…")
    st.rerun()
