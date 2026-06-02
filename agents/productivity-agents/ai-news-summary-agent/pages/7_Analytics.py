"""📊 Analytics Dashboard — inbox health, response time, volume, contacts."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.ui import bootstrap, analytics_service, page_config, render_sidebar, require_auth

bootstrap()
page_config("Analytics", "📊")
render_sidebar()
if not require_auth():
    st.stop()

st.title("📊 Analytics Dashboard")
st.caption("Computed from your locally cached emails. Fetch more on the Inbox page for richer stats.")

with st.spinner("Crunching numbers…"):
    a = analytics_service().compute()

# ----- Top metrics -----
c1, c2, c3, c4 = st.columns(4)
c1.metric("Inbox Health", f"{a.health_score}/100", a.health_label)
c2.metric("Unread", a.unread_count)
c3.metric("Follow-up rate", f"{a.followup_rate * 100:.0f}%")
c4.metric(
    "Avg response time",
    f"{a.avg_response_hours:.1f} h" if a.avg_response_hours is not None else "n/a",
)

st.divider()

left, right = st.columns([3, 2])

# ----- Health gauge -----
with left:
    st.subheader("Inbox Health")
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=a.health_score,
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#4F8DFD"},
            "steps": [
                {"range": [0, 40], "color": "#3a1c20"},
                {"range": [40, 60], "color": "#3a341c"},
                {"range": [60, 80], "color": "#1c3a2a"},
                {"range": [80, 100], "color": "#163a23"},
            ],
        },
    ))
    gauge.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10),
                        paper_bgcolor="rgba(0,0,0,0)", font_color="#E6EAF1")
    st.plotly_chart(gauge, use_container_width=True)

# ----- Status breakdown -----
with right:
    st.subheader("Status Breakdown")
    breakdown = {
        "Unread": a.unread_count,
        "Starred": a.starred_count,
        "Important": a.important_count,
        "Follow-up": a.followup_count,
    }
    if any(breakdown.values()):
        fig = px.pie(values=list(breakdown.values()), names=list(breakdown.keys()), hole=0.55,
                     color_discrete_sequence=px.colors.sequential.Blues_r)
        fig.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10),
                          paper_bgcolor="rgba(0,0,0,0)", font_color="#E6EAF1",
                          legend=dict(orientation="h"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No status data yet.")

st.divider()

# ----- Email volume -----
st.subheader("📈 Email Volume (last 14 days)")
if a.volume_by_day:
    df = pd.DataFrame({"date": list(a.volume_by_day.keys()),
                       "emails": list(a.volume_by_day.values())})
    fig = px.bar(df, x="date", y="emails", color_discrete_sequence=["#4F8DFD"])
    fig.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font_color="#E6EAF1",
                      margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Fetch some emails first to see volume trends.")

# ----- Top contacts -----
st.subheader("👥 Top Contacts")
if a.top_contacts:
    df = pd.DataFrame(a.top_contacts)
    df = df.rename(columns={"name": "Contact", "sender_email": "Email", "count": "Emails"})
    bar = px.bar(df.sort_values("Emails"), x="Emails", y="Contact", orientation="h",
                 color_discrete_sequence=["#7AB0FF"])
    bar.update_layout(height=360, paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font_color="#E6EAF1",
                      margin=dict(t=10, b=10))
    st.plotly_chart(bar, use_container_width=True)
    st.dataframe(df[["Contact", "Email", "Emails"]], use_container_width=True, hide_index=True)
else:
    st.info("No contact data yet.")
