"""
views/dashboard.py
------------------
The main dashboard page (rendered by app.py's navigation router).

UX goals:
  * Tell a brand-new user exactly what to do first (onboarding banner).
  * Show clear connection status for OpenAI + Google before they hit an error.
  * Keep scan controls and exports tidy in the sidebar.
  * Give friendly empty states instead of blank panels.
"""

from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import streamlit as st

import config
from src import database, exporter, settings

GRADIENTS = [
    "linear-gradient(135deg,#4F46E5,#7C3AED)",
    "linear-gradient(135deg,#DC2626,#F87171)",
    "linear-gradient(135deg,#D97706,#FBBF24)",
    "linear-gradient(135deg,#059669,#34D399)",
    "linear-gradient(135deg,#2563EB,#60A5FA)",
    "linear-gradient(135deg,#475569,#94A3B8)",
]


def card(label: str, value, gradient: str) -> str:
    return (
        f'<div class="metric-card" style="background:{gradient}">'
        f"<h2>{value}</h2><p>{label}</p></div>"
    )


# --- connection status (computed once) ---------------------------------------
key_source = settings.get_openai_key_source()
key_ok = key_source != "missing"
google_ok = os.path.exists(config.CREDENTIALS_FILE)


# =============================================================================
# SIDEBAR — scan controls + status + export
# =============================================================================
with st.sidebar:
    st.subheader("Connection")
    st.markdown(
        f"{'✅' if key_ok else '⚠️'} **OpenAI key** — "
        + (f"set (via {'Settings' if key_source == 'settings' else '.env'})" if key_ok else "not set")
    )
    st.markdown(
        f"{'✅' if google_ok else '⚠️'} **Google** — "
        + (
            "authorized" if (google_ok and settings.google_token_present())
            else "credentials set" if google_ok
            else "no credentials"
        )
    )
    if not key_ok:
        if st.button("⚙️ Open Settings", use_container_width=True):
            st.switch_page("views/settings.py")

    st.divider()
    st.subheader("Run a scan")
    scope = st.radio("What to scan", ["Last 24 hours", "Unread only", "Whole inbox"], index=0)
    label = st.text_input("Label / folder", value=config.DEFAULT_LABEL)
    max_emails = st.slider("Max emails", 5, 100, config.DEFAULT_MAX_EMAILS, step=5)
    push_sheet = st.checkbox("Also write to Google Sheet", value=True)

    run_clicked = st.button(
        "▶ Run scan", use_container_width=True, type="primary", disabled=not key_ok
    )
    if not key_ok:
        st.caption("Add an OpenAI key in Settings to enable scanning.")

    last_run = database.get_meta("last_run")
    if last_run:
        st.caption(f"🕒 Last run: {last_run[:19].replace('T', ' ')} UTC")

    st.divider()
    st.subheader("Export")
    e1, e2, e3 = st.columns(3)
    e1.download_button("CSV", exporter.to_csv(), "action_items.csv", "text/csv", use_container_width=True)
    e2.download_button(
        "Excel", exporter.to_excel(), "action_items.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    e3.download_button("PDF", exporter.to_pdf(), "action_items.pdf", "application/pdf", use_container_width=True)


# Handle the scan click (kept outside the sidebar block so messages show centrally).
if run_clicked:
    from src.pipeline import run_pipeline

    with st.spinner("Fetching and analyzing emails…"):
        try:
            report = run_pipeline(
                max_emails=max_emails,
                label=label.strip() or config.DEFAULT_LABEL,
                unread_only=(scope == "Unread only"),
                last_hours=24 if scope == "Last 24 hours" else None,
                push_to_sheet=push_sheet,
            )
            if report["new"]:
                st.toast(f"Analyzed {report['new']} new email(s).", icon="✅")
            else:
                st.toast("No new emails — you're all caught up.", icon="📭")
        except FileNotFoundError:
            st.error(
                "**credentials.json not found.** Download a Desktop OAuth client "
                "from Google Cloud Console and place it in the project root. "
                "See the README for the 4-step setup."
            )
        except RuntimeError as exc:
            st.error(str(exc))
        except Exception as exc:  # noqa: BLE001
            st.error(f"Scan failed: {exc}")


# =============================================================================
# MAIN
# =============================================================================
st.title("📊 Inbox Action Dashboard")

stats = database.get_stats()

# --- onboarding: shown until the user has both a key and some data -----------
if not key_ok or stats["total"] == 0:
    with st.container(border=True):
        st.markdown("#### 👋 Let's get you set up")
        step1 = "✅" if key_ok else "⬜"
        step2 = "✅" if google_ok else "⬜"
        step3 = "✅" if stats["total"] else "⬜"
        st.markdown(
            f"{step1} **1. Add your OpenAI key** — open **Settings** and paste it in.\n\n"
            f"{step2} **2. Add Google credentials** — upload `credentials.json` on the **Settings** page.\n\n"
            f"{step3} **3. Run your first scan** — use the **Run a scan** panel in the sidebar."
        )
        if not key_ok or not google_ok:
            if st.button("⚙️ Go to Settings", type="primary"):
                st.switch_page("views/settings.py")

# --- analytics cards ---------------------------------------------------------
cards = [
    ("Total analyzed", stats["total"]),
    ("High priority", stats["high"]),
    ("Medium priority", stats["medium"]),
    ("Low priority", stats["low"]),
    ("Pending", stats["pending"]),
    ("Completed", stats["completed"]),
]
for col, (lbl, val), grad in zip(st.columns(6), cards, GRADIENTS):
    col.markdown(card(lbl, val, grad), unsafe_allow_html=True)

st.write("")

# --- charts ------------------------------------------------------------------
if stats["total"]:
    left, right = st.columns(2)
    prio_df = pd.DataFrame(
        {"Priority": ["High", "Medium", "Low"],
         "Count": [stats["high"], stats["medium"], stats["low"]]}
    )
    fig1 = px.bar(
        prio_df, x="Priority", y="Count", color="Priority",
        color_discrete_map={"High": "#DC2626", "Medium": "#D97706", "Low": "#64748B"},
        title="Emails by priority",
    )
    fig1.update_layout(showlegend=False, height=320, margin=dict(t=50, b=10))
    left.plotly_chart(fig1, use_container_width=True)

    status_df = pd.DataFrame(
        {"Status": ["Pending", "Completed"],
         "Count": [stats["pending"], stats["completed"]]}
    )
    fig2 = px.pie(
        status_df, names="Status", values="Count", hole=0.55, color="Status",
        color_discrete_map={"Pending": "#F59E0B", "Completed": "#10B981"},
        title="Action status",
    )
    fig2.update_layout(height=320, margin=dict(t=50, b=10))
    right.plotly_chart(fig2, use_container_width=True)

# --- AI insights -------------------------------------------------------------
st.subheader("🧠 AI insights")
if stats["total"] == 0:
    st.caption("Run a scan first, then generate a daily briefing here.")
elif st.button("Generate daily briefing", disabled=not key_ok):
    from src.insights import InsightsEngine

    with st.spinner("Thinking…"):
        try:
            ins = InsightsEngine(
                api_key=settings.get_openai_key(), model=settings.get_model()
            ).generate()
            st.markdown(f"**Daily summary:** {ins['daily_summary']}")
            ic1, ic2 = st.columns(2)
            with ic1:
                st.markdown("**🔥 Top urgent**")
                st.write("\n".join(f"- {x}" for x in ins["top_urgent"]) or "_None_")
                st.markdown("**⏰ Missed follow-ups**")
                st.write("\n".join(f"- {x}" for x in ins["missed_followups"]) or "_None_")
            with ic2:
                st.markdown("**✅ Recommended next actions**")
                st.write("\n".join(f"- {x}" for x in ins["recommended_actions"]) or "_None_")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not generate insights: {exc}")

# --- filterable, editable table ----------------------------------------------
st.subheader("📋 Action items")
f1, f2 = st.columns(2)
prio_filter = f1.selectbox("Priority", ["All"] + config.PRIORITIES)
status_filter = f2.selectbox("Status", ["All"] + config.STATUSES)

rows = database.get_all_emails(priority=prio_filter, status=status_filter)
if rows:
    df = pd.DataFrame(rows)[
        ["date", "sender", "subject", "summary", "action_item", "priority", "due_date", "status", "id"]
    ]
    edited = st.data_editor(
        df,
        column_config={
            "id": None,
            "date": st.column_config.TextColumn("Date", width="small"),
            "sender": st.column_config.TextColumn("Sender", width="medium"),
            "subject": st.column_config.TextColumn("Subject", width="medium"),
            "summary": st.column_config.TextColumn("Summary", width="large"),
            "action_item": st.column_config.TextColumn("Action Item", width="medium"),
            "priority": st.column_config.TextColumn("Priority", width="small"),
            "due_date": st.column_config.TextColumn("Due Date", width="small"),
            "status": st.column_config.SelectboxColumn("Status", options=config.STATUSES, width="small"),
        },
        hide_index=True,
        use_container_width=True,
        key="editor",
    )
    if st.button("💾 Save status changes"):
        for _, row in edited.iterrows():
            database.update_status(row["id"], row["status"])
        st.toast("Status changes saved.", icon="💾")
        st.rerun()
else:
    st.caption("No emails match the current filters.")
