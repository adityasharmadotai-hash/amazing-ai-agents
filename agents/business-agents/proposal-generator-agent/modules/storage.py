"""
storage.py — In-session storage for proposals, clients, and branding.
All data stored in st.session_state — no database required.
"""

import re, uuid
from datetime import datetime
import streamlit as st


def init_stores():
    defaults = {
        "proposals": [],
        "clients": [],
        "branding": {
            "agency_name": "Your Agency",
            "tagline": "Building the future, together.",
            "primary_color": "#4f46e5",
            "secondary_color": "#7c3aed",
            "email": "", "phone": "", "website": "", "address": "",
            "logo_bytes": None, "logo_name": "",
        },
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _id() -> str:
    return str(uuid.uuid4())[:12]

def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ── Proposals ──────────────────────────────────────────────────────────────────

def save_proposal(proposal: dict) -> str:
    init_stores()
    meta = proposal.get("_meta", {})
    pid  = _id()
    st.session_state.proposals.insert(0, {
        "id":           pid,
        "title":        proposal.get("proposal_title", "Untitled Proposal"),
        "client_name":  meta.get("client_name", ""),
        "project_type": meta.get("project_type", ""),
        "budget":       meta.get("budget", ""),
        "template":     meta.get("template", ""),
        "status":       "Draft",
        "created_at":   _now(),
        "updated_at":   _now(),
        "data":         proposal,
    })
    return pid


def update_proposal(pid: str, proposal: dict):
    init_stores()
    for p in st.session_state.proposals:
        if p["id"] == pid:
            p["data"] = proposal
            p["title"] = proposal.get("proposal_title", p["title"])
            p["updated_at"] = _now()


def delete_proposal(pid: str):
    init_stores()
    st.session_state.proposals = [p for p in st.session_state.proposals if p["id"] != pid]


def get_proposals() -> list:
    init_stores()
    return st.session_state.proposals


def update_status(pid: str, status: str):
    init_stores()
    for p in st.session_state.proposals:
        if p["id"] == pid:
            p["status"] = status
            p["updated_at"] = _now()


# ── Clients ────────────────────────────────────────────────────────────────────

def save_client(name: str, email: str = "", company: str = "", notes: str = "") -> str:
    init_stores()
    for c in st.session_state.clients:
        if c["name"].lower() == name.lower():
            return c["id"]
    cid = _id()
    st.session_state.clients.insert(0, {
        "id": cid, "name": name, "email": email,
        "company": company, "notes": notes, "created_at": _now(),
    })
    return cid


def get_clients() -> list:
    init_stores()
    return st.session_state.clients


# ── Branding ───────────────────────────────────────────────────────────────────

def get_branding() -> dict:
    init_stores()
    return st.session_state.branding


def update_branding(**kwargs):
    init_stores()
    for k, v in kwargs.items():
        if k in st.session_state.branding:
            st.session_state.branding[k] = v


# ── Analytics ──────────────────────────────────────────────────────────────────

def get_analytics() -> dict:
    init_stores()
    props = st.session_state.proposals
    total = len(props)
    if total == 0:
        return {"total":0,"draft":0,"sent":0,"accepted":0,"rejected":0,
                "win_rate":0,"total_value":0,"by_template":{},"by_status":{}}

    status_c = {}; tmpl_c = {}; total_val = 0
    for p in props:
        s = p.get("status","Draft"); t = p.get("template","Agency")
        status_c[s] = status_c.get(s,0)+1
        tmpl_c[t]   = tmpl_c.get(t,0)+1
        nums = re.findall(r"\d[\d,]*", p.get("budget","").replace(",",""))
        if nums:
            try: total_val += int(nums[0])
            except: pass

    accepted = status_c.get("Accepted",0)
    sent     = status_c.get("Sent",0)
    return {
        "total": total, "draft": status_c.get("Draft",0),
        "sent": sent, "accepted": accepted,
        "rejected": status_c.get("Rejected",0),
        "win_rate": round(accepted/max(sent+accepted,1)*100,1),
        "total_value": total_val,
        "by_template": tmpl_c, "by_status": status_c,
    }
