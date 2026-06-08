"""
storage.py — Founder profile + lightweight app settings.

Connector data (emails, meetings, tasks, slack, revenue) lives in connectors.py.
This module only holds the founder's identity and connection toggles, kept in
st.session_state so no database is required.
"""

import streamlit as st


def init_profile():
    defaults = {
        "user_api_key": "",
        "profile": {
            "founder_name": "Aditya",
            "company": "Acme Inc.",
            "role": "Founder & CEO",
            "currency": "$",
        },
        "connections": {
            "Gmail": True,
            "Google Calendar": True,
            "Notion": True,
            "Slack": True,
            "Stripe": True,
            "Razorpay": False,
        },
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def get_profile() -> dict:
    init_profile()
    return st.session_state.profile


def update_profile(**kwargs):
    init_profile()
    for k, v in kwargs.items():
        if k in st.session_state.profile:
            st.session_state.profile[k] = v


def get_connections() -> dict:
    init_profile()
    return st.session_state.connections


def toggle_connection(name: str, on: bool):
    init_profile()
    st.session_state.connections[name] = on
