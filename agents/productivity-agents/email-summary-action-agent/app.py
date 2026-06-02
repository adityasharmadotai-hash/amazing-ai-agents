"""Email Summary & Action Items Agent — Streamlit dashboard."""
import asyncio
import os

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from modules import (analyzer, database, exporter, gmail_client,
                     insights, sheets_client)

load_dotenv()
database.init_db()


def get_setting(key: str, default: str) -> str:
    """Read a config value from env first, then Streamlit secrets."""
    if os.getenv(key):
        return os.getenv(key)
    try:
        return st.secrets[key]
    except Exception:
        return default


st.set_page_config(page_title="Email Action Agent",
                   page_icon="📧", layout="wide")

# ---------- Sidebar: connection & controls ----------
st.sidebar.title("📧 Email Action Agent")
mode = st.sidebar.selectbox("Fetch mode", ["last_24h", "unread", "inbox"])
max_results = st.sidebar.slider("Max emails", 5, 50, 20)

if "service" not in st.session_state:
    st.session_state.service = None

if st.sidebar.button("🔐 Connect Gmail"):
    try:
        st.session_state.service = gmail_client.get_gmail_service()
        st.sidebar.success("Connected!")
    except Exception as e:
        st.sidebar.error(f"Auth failed: {e}")

label = None
if st.session_state.service:
    try:
        labels = gmail_client.list_labels(st.session_state.service)
        label = st.sidebar.selectbox("Label (optional)", ["(none)"] + labels)
        label = None if label == "(none)" else label
    except Exception as e:
        st.sidebar.warning(f"Could not load labels: {e}")

if st.sidebar.button("⚡ Analyze Emails") and st.session_state.service:
    with st.spinner("Fetching and analyzing..."):
        raw = gmail_client.fetch_emails(
            st.session_state.service, mode=mode,
            label=label, max_results=max_results)
        fresh = [e for e in raw
                 if not database.already_processed(e["email_id"])]
        if fresh:
            analyzed = asyncio.run(analyzer.analyze_batch(fresh))
            for r in analyzed:
                database.save_email(r)
            try:
                ws = sheets_client.get_sheet(
                    get_setting("GOOGLE_SHEET_NAME", "Email Action Items"))
                sheets_client.append_rows(ws, analyzed)
            except Exception as e:
                st.warning(f"Saved locally; Sheets sync skipped: {e}")
        st.success(f"Analyzed {len(fresh)} new emails.")

# ---------- Load data ----------
emails = database.get_all_emails()

st.title("📧 Email Summary & Action Items")

if not emails:
    st.info("Connect Gmail and click **Analyze Emails** to get started.")
    st.stop()

# ---------- Metric cards ----------
stats = insights.quick_stats(emails)
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total", stats["total"])
c2.metric("🔴 High", stats["high"])
c3.metric("🟡 Medium", stats["medium"])
c4.metric("🟢 Low", stats["low"])
c5.metric("⏳ Pending", stats["pending"])
c6.metric("✅ Completed", stats["completed"])

# ---------- AI insights ----------
with st.expander("🧠 Daily AI Briefing", expanded=True):
    if st.button("Generate briefing"):
        with st.spinner("Thinking..."):
            st.write(insights.daily_summary(emails))
    st.subheader("🔥 Top urgent")
    urgent = insights.top_urgent(emails)
    if urgent:
        for e in urgent:
            st.markdown(f"- **{e['subject']}** — {e['action_item']}")
    else:
        st.caption("No pending high-priority items. 🎉")

# ---------- Charts ----------
df = pd.DataFrame(emails)
g1, g2 = st.columns(2)
with g1:
    fig = px.pie(df, names="priority", title="Priority distribution",
                 color="priority",
                 color_discrete_map={"High": "#EF4444",
                                     "Medium": "#F59E0B",
                                     "Low": "#10B981"})
    st.plotly_chart(fig, use_container_width=True)
with g2:
    fig2 = px.histogram(df, x="status", title="Status overview", color="status")
    st.plotly_chart(fig2, use_container_width=True)

# ---------- Filters + table ----------
st.subheader("📋 Action Items")
f1, f2 = st.columns(2)
prio = f1.multiselect("Priority", ["High", "Medium", "Low"],
                      default=["High", "Medium", "Low"])
stat = f2.multiselect("Status", ["Pending", "Completed"],
                      default=["Pending", "Completed"])
view = df[df["priority"].isin(prio) & df["status"].isin(stat)]
st.dataframe(view[["id", "date", "sender", "subject", "summary",
                   "action_item", "priority", "status"]],
             use_container_width=True, hide_index=True)

# ---------- Mark complete ----------
with st.expander("✅ Update status"):
    row_id = st.number_input("Email id", min_value=1, step=1)
    new_status = st.selectbox("Status", ["Completed", "Pending"])
    if st.button("Update"):
        database.update_status(int(row_id), new_status)
        st.success("Updated — refresh to see changes.")

# ---------- Export ----------
st.subheader("⬇️ Export")
e1, e2, e3 = st.columns(3)
e1.download_button("CSV", exporter.to_csv(emails), "emails.csv", "text/csv")
e2.download_button("Excel", exporter.to_excel(emails), "emails.xlsx")
e3.download_button("PDF", exporter.to_pdf(emails), "emails.pdf",
                   "application/pdf")
