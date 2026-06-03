"""
app.py
------
The Streamlit dashboard — the face of the agent.

Layout:
  * Sidebar  -> scan controls (label, unread-only, last-24h, max emails) + export
  * Top row  -> analytics cards (totals, priority counts, pending/completed)
  * Charts   -> priority distribution + status breakdown
  * Insights -> AI daily briefing
  * Table    -> filterable action-item list with editable Status

Run it with:  streamlit run app.py
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

import config
from src import database, exporter
from src.insights import InsightsEngine
from src.pipeline import run_pipeline

# --- page setup --------------------------------------------------------------
st.set_page_config(
    page_title="Email Action Agent",
    page_icon="📬",
    layout="wide",
    initial_sidebar_state="expanded",
)

database.init_db()

# Light styling for the analytics cards.
st.markdown(
    """
    <style>
    .metric-card {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        padding: 1.1rem 1.3rem; border-radius: 14px; color: white;
    }
    .metric-card h2 { margin: 0; font-size: 2rem; }
    .metric-card p { margin: 0; opacity: 0.85; font-size: 0.85rem; }
    .block-container { padding-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def card(label: str, value, gradient: str) -> str:
    return (
        f'<div class="metric-card" style="background:{gradient}">'
        f"<h2>{value}</h2><p>{label}</p></div>"
    )


# --- sidebar: scan controls --------------------------------------------------
st.sidebar.title("📬 Email Action Agent")
st.sidebar.caption("Gmail → AI triage → Google Sheet")

st.sidebar.subheader("Scan settings")
scope = st.sidebar.radio(
    "What to scan",
    ["Last 24 hours", "Unread only", "Whole inbox"],
    index=0,
)
label = st.sidebar.text_input("Label / folder", value=config.DEFAULT_LABEL)
max_emails = st.sidebar.slider("Max emails", 5, 100, config.DEFAULT_MAX_EMAILS, step=5)
push_sheet = st.sidebar.checkbox("Also write to Google Sheet", value=True)

if st.sidebar.button("▶ Run scan", use_container_width=True, type="primary"):
    with st.spinner("Fetching and analyzing emails..."):
        try:
            report = run_pipeline(
                max_emails=max_emails,
                label=label.strip() or config.DEFAULT_LABEL,
                unread_only=(scope == "Unread only"),
                last_hours=24 if scope == "Last 24 hours" else None,
                push_to_sheet=push_sheet,
            )
            st.sidebar.success(
                f"Fetched {report['fetched']} · {report['new']} new · "
                f"{report['written_to_sheet']} → sheet"
            )
        except FileNotFoundError:
            st.sidebar.error("credentials.json not found. See the README for OAuth setup.")
        except Exception as exc:  # noqa: BLE001
            st.sidebar.error(f"Scan failed: {exc}")

last_run = database.get_meta("last_run")
if last_run:
    st.sidebar.caption(f"Last run: {last_run[:19].replace('T', ' ')} UTC")

# --- sidebar: export ---------------------------------------------------------
st.sidebar.subheader("Export")
c1, c2, c3 = st.sidebar.columns(3)
c1.download_button("CSV", exporter.to_csv(), "action_items.csv", "text/csv", use_container_width=True)
c2.download_button(
    "Excel",
    exporter.to_excel(),
    "action_items.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)
c3.download_button("PDF", exporter.to_pdf(), "action_items.pdf", "application/pdf", use_container_width=True)


# --- main: analytics cards ---------------------------------------------------
st.title("Inbox Action Dashboard")
stats = database.get_stats()

cols = st.columns(6)
gradients = [
    "linear-gradient(135deg,#4F46E5,#7C3AED)",
    "linear-gradient(135deg,#DC2626,#F87171)",
    "linear-gradient(135deg,#D97706,#FBBF24)",
    "linear-gradient(135deg,#059669,#34D399)",
    "linear-gradient(135deg,#2563EB,#60A5FA)",
    "linear-gradient(135deg,#475569,#94A3B8)",
]
labels = [
    ("Total analyzed", stats["total"]),
    ("High priority", stats["high"]),
    ("Medium priority", stats["medium"]),
    ("Low priority", stats["low"]),
    ("Pending", stats["pending"]),
    ("Completed", stats["completed"]),
]
for col, (lbl, val), grad in zip(cols, labels, gradients):
    col.markdown(card(lbl, val, grad), unsafe_allow_html=True)

st.write("")

# --- charts ------------------------------------------------------------------
left, right = st.columns(2)
if stats["total"]:
    prio_df = pd.DataFrame(
        {"Priority": ["High", "Medium", "Low"],
         "Count": [stats["high"], stats["medium"], stats["low"]]}
    )
    fig1 = px.bar(
        prio_df, x="Priority", y="Count", color="Priority",
        color_discrete_map={"High": "#DC2626", "Medium": "#D97706", "Low": "#64748B"},
        title="Emails by priority",
    )
    fig1.update_layout(showlegend=False, height=320)
    left.plotly_chart(fig1, use_container_width=True)

    status_df = pd.DataFrame(
        {"Status": ["Pending", "Completed"],
         "Count": [stats["pending"], stats["completed"]]}
    )
    fig2 = px.pie(
        status_df, names="Status", values="Count", hole=0.55,
        color="Status",
        color_discrete_map={"Pending": "#F59E0B", "Completed": "#10B981"},
        title="Action status",
    )
    fig2.update_layout(height=320)
    right.plotly_chart(fig2, use_container_width=True)
else:
    st.info("No data yet — run a scan from the sidebar to populate the dashboard.")

# --- AI insights -------------------------------------------------------------
st.subheader("🧠 AI insights")
if st.button("Generate daily briefing"):
    with st.spinner("Thinking..."):
        try:
            ins = InsightsEngine().generate()
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

# --- filterable table --------------------------------------------------------
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
            "id": None,  # hide
            "date": st.column_config.TextColumn("Date"),
            "sender": "Sender",
            "subject": "Subject",
            "summary": "Summary",
            "action_item": "Action Item",
            "priority": "Priority",
            "due_date": "Due Date",
            "status": st.column_config.SelectboxColumn("Status", options=config.STATUSES),
        },
        hide_index=True,
        use_container_width=True,
        key="editor",
    )
    if st.button("💾 Save status changes"):
        for _, row in edited.iterrows():
            database.update_status(row["id"], row["status"])
        st.success("Saved.")
        st.rerun()
else:
    st.caption("No emails match the current filters.")
