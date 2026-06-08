"""outreach.py — AI Outreach Assistant: draft connection requests, messages,
follow-ups and intros for any opportunity."""

import streamlit as st

from modules import config, database as db, outreach, ui

ui.hero("Outreach Assistant", "Generate personalised, value-first messages for any opportunity.")

opps = db.list_opportunities(order="score")
if not opps:
    st.info("No opportunities yet — run a scan from the Home page first.")
    st.stop()

# ── Pick an opportunity ──────────────────────────────────────────────────────────
labels = {
    f"[{o['score_value']}] {o['person_name']} · {o['opp_type']} · {o.get('company','')}": o["id"]
    for o in opps
}
choice = st.selectbox("Choose an opportunity", list(labels.keys()))
opp = db.get_opportunity(labels[choice])

left, right = st.columns([1, 1])
with left:
    ui.opportunity_card(opp)
with right:
    st.markdown("<div class='section-title'>Your details</div>", unsafe_allow_html=True)
    sender_name = st.text_input("Your name", st.session_state.get("sender_name", ""))
    sender_role = st.text_input("Your role / company", st.session_state.get("sender_role", ""))
    kind = st.radio(
        "Message type",
        list(outreach.MESSAGE_KINDS.keys()),
        format_func=lambda k: outreach.MESSAGE_KINDS[k],
        horizontal=False,
    )
    engine = "Claude" if config.ai_enabled() else "smart templates"
    if st.button(f"✨ Generate with {engine}", type="primary", use_container_width=True):
        with st.spinner("Drafting…"):
            msg = outreach.generate_message(opp, kind, sender_name, sender_role)
        st.session_state[f"draft_{opp['id']}_{kind}"] = msg

# ── Draft editor ─────────────────────────────────────────────────────────────────
draft_key = f"draft_{opp['id']}_{kind}"
if draft_key in st.session_state:
    st.markdown("<div class='section-title'>Draft</div>", unsafe_allow_html=True)
    edited = st.text_area("Edit before sending", st.session_state[draft_key], height=180)
    s1, s2 = st.columns([1, 4])
    with s1:
        if st.button("💾 Save draft"):
            db.add_message(opp["id"], kind, edited)
            st.success("Saved to history.")
    with s2:
        st.caption("Copy into LinkedIn. Tip: send the connection request first, then the message after they accept.")

# ── One-click: generate the full sequence ────────────────────────────────────────
st.divider()
if st.button("⚡ Generate full sequence (connection → message → follow-up)"):
    with st.spinner("Drafting the sequence…"):
        for k in ["connection", "message", "followup"]:
            m = outreach.generate_message(opp, k, sender_name, sender_role)
            db.add_message(opp["id"], k, m)
    st.success("Saved a 3-message sequence to history below.", icon="⚡")

# ── History ──────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>Saved messages for this opportunity</div>",
            unsafe_allow_html=True)
history = db.list_messages(opp["id"])
if not history:
    st.caption("No saved messages yet.")
for m in history:
    with st.expander(f"{outreach.MESSAGE_KINDS.get(m['kind'], m['kind'])} · {m['created_at'][:16]}"):
        st.code(m["content"], language=None)
