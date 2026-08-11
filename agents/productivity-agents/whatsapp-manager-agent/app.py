"""
app.py — the team dashboard (Streamlit).

Five tabs sharing the same SQLite DB as the webhook brain:
  • Overview      — live counts + open escalations at a glance
  • Simulator     — chat as a customer and watch the real agent respond (no
                    WhatsApp number needed) — the fastest way to test the brain
  • Conversations — every thread, with human takeover / manual reply
  • Escalations   — the hand-off inbox; mark cases resolved
  • Knowledge     — edit the business info, qualifying questions, and persona live

Run:  streamlit run app.py
"""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from modules import (
    agent,
    config,
    conversation,
    database,
    demo_seed,
    knowledge,
)

# Official Cloud API client (cloud_api/) is optional — only needed for that route.
try:
    from cloud_api import whatsapp_api
except Exception:  # pragma: no cover
    whatsapp_api = None

st.set_page_config(page_title=config.APP_NAME, page_icon="💬", layout="wide")

# One-time init per session.
if "initialized" not in st.session_state:
    database.init_db()
    knowledge.seed_defaults()
    st.session_state.initialized = True
    st.session_state.sim_wa_id = "15550001111"


# ── sidebar ───────────────────────────────────────────────────────────────────
def sidebar() -> str:
    st.sidebar.title("💬 " + config.APP_NAME)
    st.sidebar.caption(config.APP_TAGLINE)

    gem_ok = bool(config.get_secret("GEMINI_API_KEY"))
    wa_ok = bool(whatsapp_api and whatsapp_api.is_configured())
    team = config.team_numbers()

    st.sidebar.markdown("**Status**")
    st.sidebar.write(("🟢" if gem_ok else "🔴") + " Gemini brain")
    st.sidebar.write(("🟢" if wa_ok else "🟡") + " WhatsApp Cloud API")
    st.sidebar.write((f"🟢 {len(team)} number(s)" if team else "🟡 none") + " — team alerts")
    if not wa_ok:
        st.sidebar.info("WhatsApp not connected — use the **Simulator** to test the agent now.")

    page = st.sidebar.radio(
        "Go to",
        ["Overview", "Simulator", "Conversations", "Escalations", "Knowledge base"],
        label_visibility="collapsed",
    )

    st.sidebar.divider()
    if st.sidebar.button("Seed demo business", use_container_width=True):
        demo_seed.run()
        st.sidebar.success("Loaded 'BrightPath Careers' demo profile.")
    return page


# ── Overview ──────────────────────────────────────────────────────────────────
def page_overview() -> None:
    st.header("Overview")
    c = database.counts()
    cols = st.columns(5)
    cols[0].metric("Contacts", c["contacts"])
    cols[1].metric("Active chats", c["active"])
    cols[2].metric("Escalated", c["escalated"])
    cols[3].metric("Open escalations", c["open_escalations"])
    cols[4].metric("Messages", c["messages"])

    if not agent.is_configured():
        st.warning("Set `GEMINI_API_KEY` in your secrets to enable the agent.")

    st.subheader("Open escalations")
    esc = database.list_escalations(limit=50)
    open_esc = [e for e in esc if e["status"] != "resolved"]
    if not open_esc:
        st.success("Nothing waiting on the team. 🎉")
    else:
        df = pd.DataFrame(open_esc)[["id", "wa_id", "reason", "question", "status", "created_at"]]
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("Recent conversations")
    convs = database.list_conversations(limit=15)
    if not convs:
        st.info("No conversations yet. Try the **Simulator** tab.")
    else:
        rows = [
            {
                "id": cv["id"],
                "contact": cv.get("profile_name") or cv["wa_id"],
                "stage": cv["stage"],
                "status": cv["status"],
                "agent": "on" if cv["agent_enabled"] else "human",
                "last message": (cv.get("last_message") or "")[:60],
                "updated": cv["updated_at"],
            }
            for cv in convs
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ── Simulator ─────────────────────────────────────────────────────────────────
def page_simulator() -> None:
    st.header("Simulator")
    st.caption(
        "Chat exactly as a customer would on WhatsApp. This runs the **real** agent "
        "brain and stores the thread in the database — it just doesn't send over "
        "WhatsApp. The best way to tune your knowledge base before going live."
    )

    if not agent.is_configured():
        st.error("Set `GEMINI_API_KEY` in your secrets first — the simulator needs the Gemini brain.")
        return

    col1, col2 = st.columns([3, 1])
    wa_id = col1.text_input("Simulated customer number", value=st.session_state.sim_wa_id)
    st.session_state.sim_wa_id = wa_id
    if col2.button("🔄 New customer", use_container_width=True):
        # Bump the trailing digits to start a fresh thread.
        try:
            st.session_state.sim_wa_id = str(int(wa_id) + 1)
        except ValueError:
            st.session_state.sim_wa_id = "15550001111"
        st.rerun()

    conv = database.get_active_conversation(wa_id)
    if conv:
        for m in database.get_messages(conv["id"]):
            role = "user" if m["direction"] == "in" else "assistant"
            with st.chat_message(role):
                st.write(m["body"])
                if m["sender"] == "human":
                    st.caption("— sent by a human teammate")
    else:
        st.info("Send a message below to start the conversation (the agent will greet you).")

    prompt = st.chat_input("Type a message as the customer…")
    if prompt:
        with st.spinner("Agent is replying…"):
            result = conversation.handle_inbound(
                wa_id, prompt, profile_name="Simulated Lead", live=False
            )
        if result.get("escalated"):
            st.toast(f"🚨 Escalated: {result['escalation'].get('detail', '')}")
        st.rerun()

    if conv and st.button("End & close this conversation"):
        database.update_conversation(conv["id"], status="closed")
        st.rerun()


# ── Conversations ─────────────────────────────────────────────────────────────
def page_conversations() -> None:
    st.header("Conversations")
    status_filter = st.selectbox("Filter", ["all", "active", "escalated", "closed"])
    convs = database.list_conversations(
        status=None if status_filter == "all" else status_filter, limit=200
    )
    if not convs:
        st.info("No conversations yet.")
        return

    labels = {
        cv["id"]: f"#{cv['id']} · {cv.get('profile_name') or cv['wa_id']} · {cv['stage']}"
        + ("" if cv["agent_enabled"] else " · 👤 human")
        for cv in convs
    }
    chosen = st.selectbox("Thread", list(labels.keys()), format_func=lambda i: labels[i])
    conv = database.get_conversation(chosen)
    if not conv:
        return

    left, right = st.columns([2, 1])
    with left:
        for m in database.get_messages(conv["id"]):
            role = "user" if m["direction"] == "in" else "assistant"
            with st.chat_message(role):
                st.write(m["body"])
                tag = {"human": "human teammate", "agent": "AI agent",
                       "customer": "customer", "system": "system"}.get(m["sender"], m["sender"])
                st.caption(f"{tag} · {m['created_at']}")

        reply = st.chat_input("Reply as a human (takes over — pauses the agent)…")
        if reply:
            res = conversation.send_manual_reply(conv["id"], reply, live=True)
            st.toast(f"Reply {res.get('delivery')}")
            st.rerun()

    with right:
        st.subheader("Details")
        st.write(f"**Contact:** {conv.get('profile_name') or conv['wa_id']}")
        st.write(f"**Number:** {conv['wa_id']}")
        st.write(f"**Status:** {conv['status']}  ·  **Stage:** {conv['stage']}")
        st.write(f"**Agent:** {'🟢 auto-replying' if conv['agent_enabled'] else '👤 human handling'}")

        st.markdown("**Collected qualification**")
        st.json(conv.get("qualification") or {})

        if conv["agent_enabled"]:
            if st.button("Take over (pause agent)"):
                database.update_conversation(conv["id"], agent_enabled=False)
                st.rerun()
        else:
            if st.button("Hand back to agent"):
                database.update_conversation(conv["id"], agent_enabled=True, status="active")
                st.rerun()

        if conv["status"] != "closed" and st.button("Close conversation"):
            database.update_conversation(conv["id"], status="closed")
            st.rerun()


# ── Escalations ───────────────────────────────────────────────────────────────
def page_escalations() -> None:
    st.header("Escalations")
    st.caption("Cases the agent handed to the team. Notified on WhatsApp when live.")
    show = st.radio("Show", ["open", "all"], horizontal=True)
    esc = database.list_escalations(
        status=None if show == "all" else None, limit=200
    )
    if show == "open":
        esc = [e for e in esc if e["status"] != "resolved"]
    if not esc:
        st.success("No escalations. 🎉")
        return

    for e in esc:
        with st.container(border=True):
            top = st.columns([3, 1])
            top[0].markdown(
                f"**#{e['id']} · {e.get('profile_name') or e['wa_id']}**  \n"
                f"Reason: {e['reason'] or '—'}  \n"
                f"Message: “{e['question'] or ''}”"
            )
            top[1].write(f"Status: `{e['status']}`")
            top[1].caption(e["created_at"])
            cols = st.columns(3)
            if cols[0].button("Open thread", key=f"open_{e['id']}"):
                st.session_state["_jump_conv"] = e["conversation_id"]
                st.info(f"Go to Conversations → thread #{e['conversation_id']}")
            if e["status"] != "resolved" and cols[1].button("Mark resolved", key=f"res_{e['id']}"):
                database.mark_escalation(e["id"], "resolved")
                st.rerun()


# ── Knowledge base ────────────────────────────────────────────────────────────
def page_knowledge() -> None:
    st.header("Knowledge base")
    st.caption("Everything the agent knows and asks. Edits apply immediately — no redeploy.")

    tab_biz, tab_q, tab_ex, tab_persona = st.tabs(
        ["Business info", "Qualifying questions", "Style examples", "Persona & rules"]
    )

    with tab_biz:
        profile = knowledge.get_profile()
        st.write("Edit the business facts the agent may state. It will **never** claim anything not in here.")
        st.caption(
            "Useful keys: `jobs` (list of open roles), `knowledge_doc` (freeform reference text "
            "the agent can answer from), `scheduling_link` (a Calendly-style link it shares when "
            "leads want to book)."
        )
        text = st.text_area(
            "Business profile (JSON)", value=json.dumps(profile, indent=2, ensure_ascii=False),
            height=460,
        )
        if st.button("Save business info"):
            try:
                knowledge.save_profile(json.loads(text))
                st.success("Saved.")
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")

    with tab_ex:
        examples = knowledge.get_examples()
        st.write(
            "Past exchanges that teach the agent your **tone**. Each item is "
            "`{\"customer\": \"...\", \"reply\": \"...\"}`. These guide style — the agent won't copy them verbatim."
        )
        text = st.text_area(
            "Conversation examples (JSON list)",
            value=json.dumps(examples, indent=2, ensure_ascii=False), height=360,
        )
        if st.button("Save examples"):
            try:
                data = json.loads(text)
                assert isinstance(data, list)
                knowledge.save_examples(data)
                st.success("Saved.")
            except (json.JSONDecodeError, AssertionError) as e:
                st.error(f"Must be a JSON list: {e}")

    with tab_q:
        questions = knowledge.get_questions()
        st.write("The details the agent collects, one at a time. `key` is stored on the lead.")
        text = st.text_area(
            "Qualifying questions (JSON list)",
            value=json.dumps(questions, indent=2, ensure_ascii=False), height=360,
        )
        if st.button("Save questions"):
            try:
                data = json.loads(text)
                assert isinstance(data, list)
                knowledge.save_questions(data)
                st.success("Saved.")
            except (json.JSONDecodeError, AssertionError) as e:
                st.error(f"Must be a JSON list: {e}")

    with tab_persona:
        cfg = knowledge.get_config()
        cfg["assistant_name"] = st.text_input("Assistant name", cfg.get("assistant_name", "Ava"))
        cfg["tone"] = st.text_input("Tone", cfg.get("tone", ""))
        cfg["greeting_style"] = st.text_area("Greeting style", cfg.get("greeting_style", ""), height=100)
        cfg["escalation_confidence"] = st.slider(
            "Escalate below this confidence (%)", 0, 100, int(cfg.get("escalation_confidence", 55))
        )
        cfg["max_questions_before_handoff"] = st.number_input(
            "Max questions before wrapping up", 1, 10, int(cfg.get("max_questions_before_handoff", 5))
        )
        if st.button("Save persona & rules"):
            knowledge.save_config(cfg)
            st.success("Saved.")


# ── main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    page = sidebar()
    if page == "Overview":
        page_overview()
    elif page == "Simulator":
        page_simulator()
    elif page == "Conversations":
        page_conversations()
    elif page == "Escalations":
        page_escalations()
    elif page == "Knowledge base":
        page_knowledge()


if __name__ == "__main__":
    main()
