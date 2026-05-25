"""
app.py — AI Proposal Generator Agent
6-page Streamlit dashboard: New Proposal · My Proposals · Clients · Dashboard · Branding · Settings
"""

import os, sys, time
import streamlit as st
sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(page_title="AI Proposal Generator", page_icon="📝", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
html,body,[class*="css"]{ font-family:'Inter',sans-serif; }

[data-testid="stSidebar"]{ background:linear-gradient(180deg,#07090f 0%,#0d1117 55%,#0a0e1a 100%) !important; }
[data-testid="stSidebar"]>div:first-child{ background:transparent !important; }
[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,[data-testid="stSidebar"] label{ color:#e2e8f0 !important; }
[data-testid="stSidebar"] .stButton>button{
    background:rgba(255,255,255,0.06) !important; border:1px solid rgba(255,255,255,0.1) !important;
    border-radius:10px !important; color:#cbd5e1 !important; font-size:14px !important;
    font-weight:500 !important; padding:10px 14px !important; width:100% !important;
    margin:2px 0 !important; text-align:left !important; transition:all 0.18s !important;
}
[data-testid="stSidebar"] .stButton>button p{ color:#cbd5e1 !important; }
[data-testid="stSidebar"] .stButton>button:hover{
    background:rgba(79,70,229,0.28) !important; border-color:rgba(79,70,229,0.5) !important; color:white !important;
}
[data-testid="stSidebar"] .nav-active>button{
    background:linear-gradient(135deg,#4f46e5,#7c3aed) !important;
    border-left:4px solid #a78bfa !important; border-top:1px solid rgba(167,139,250,0.3) !important;
    border-right:1px solid rgba(167,139,250,0.15) !important; border-bottom:1px solid rgba(167,139,250,0.15) !important;
    color:white !important; font-weight:700 !important;
    box-shadow:0 4px 18px rgba(79,70,229,0.45) !important; transform:translateX(3px) !important;
}
[data-testid="stSidebar"] .nav-active>button p{ color:white !important; }
.nav-div{ height:1px; background:rgba(255,255,255,0.08); margin:10px 0; }

/* Cards */
.card{background:white;border:1px solid #e2e8f0;border-radius:16px;padding:20px;
      box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-bottom:12px;transition:all 0.2s;}
.card:hover{transform:translateY(-2px);box-shadow:0 8px 20px rgba(0,0,0,0.1);}
.metric-card{background:white;border-radius:14px;padding:18px;text-align:center;
             border:1px solid #e2e8f0;box-shadow:0 2px 6px rgba(0,0,0,0.05);}
.metric-val{font-size:28px;font-weight:900;color:#0f172a;}
.metric-lbl{font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;margin-top:4px;}

/* Status badges */
.s-draft{background:#f1f5f9;color:#475569;border:1px solid #cbd5e1;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:700;}
.s-sent{background:#eff6ff;color:#2563eb;border:1px solid #bfdbfe;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:700;}
.s-accepted{background:#f0fdf4;color:#16a34a;border:1px solid #bbf7d0;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:700;}
.s-rejected{background:#fef2f2;color:#dc2626;border:1px solid #fecaca;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:700;}

/* Section header */
.sec-hdr{background:linear-gradient(90deg,#4f46e5,#7c3aed);color:white;border-radius:10px;
         padding:11px 18px;margin:18px 0 12px;font-size:14px;font-weight:600;}

/* Phase card */
.phase{background:#f8fafc;border:1px solid #e2e8f0;border-left:4px solid #4f46e5;
       border-radius:10px;padding:14px 18px;margin:8px 0;}

/* Pricing */
.pkg{background:white;border:2px solid #e2e8f0;border-radius:14px;padding:20px;text-align:center;transition:all 0.2s;}
.pkg:hover{border-color:#4f46e5;transform:translateY(-2px);}
.pkg-rec{border-color:#4f46e5;background:linear-gradient(135deg,#eff6ff,#f0f4ff);}
.pkg-price{font-size:24px;font-weight:900;color:#4f46e5;margin:8px 0;}
.pkg-name{font-size:15px;font-weight:700;color:#0f172a;}

/* Timeline */
.tl-step{display:flex;gap:16px;align-items:flex-start;padding:12px 0;border-bottom:1px solid #f1f5f9;}
.tl-dot{width:32px;height:32px;border-radius:50%;background:#4f46e5;color:white;
        font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;}

/* Why us */
.why-card{background:white;border:1px solid #e2e8f0;border-radius:12px;padding:16px;border-top:3px solid #4f46e5;}

/* Cover letter */
.cover-box{background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:20px;
           font-size:14px;color:#374151;line-height:1.8;white-space:pre-wrap;}

/* Page header */
.page-hdr{padding:4px 0 20px;}
.page-hdr h1{font-size:26px;font-weight:800;color:#0f172a;margin:0;}
.page-hdr p{color:#64748b;font-size:14px;margin-top:5px;}

/* Inputs */
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea{
    border-radius:10px !important; border:2px solid #e2e8f0 !important;}
[data-testid="stTextInput"] input:focus,[data-testid="stTextArea"] textarea:focus{border-color:#4f46e5 !important;}
.stTabs [data-baseweb="tab-list"]{background:#f1f5f9;border-radius:10px;padding:3px;gap:2px;}
.stTabs [data-baseweb="tab"]{border-radius:8px;font-weight:500;font-size:13px;}
.stTabs [aria-selected="true"]{background:white !important;box-shadow:0 1px 4px rgba(0,0,0,0.1);}
#MainMenu,footer{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

from modules.generator import is_configured, generate_full_proposal, regenerate_section, generate_cover_letter, quick_pricing_estimate
from modules.storage import init_stores, save_proposal, update_proposal, delete_proposal, get_proposals, update_status, save_client, get_clients, get_branding, update_branding, get_analytics
from modules.exporter import export_pdf, export_docx

init_stores()

for k,v in {"page":"✨ New Proposal","cur_proposal":None,"cur_pid":None,"user_api_key":""}.items():
    if k not in st.session_state: st.session_state[k] = v

def _key():
    sk = st.session_state.get("user_api_key","").strip()
    if sk: return sk
    try: return st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY","")
    except: return os.environ.get("OPENAI_API_KEY","")

def _sync():
    k = _key()
    if k: os.environ["OPENAI_API_KEY"] = k
_sync()

NAV = [("✨","New Proposal"),("📋","My Proposals"),("👥","Clients"),("📊","Dashboard"),("🎨","Branding"),("🔑","Settings")]
SICON = {"Draft":"📝","Sent":"📤","Accepted":"✅","Rejected":"❌","Archived":"📦"}
SCSS  = {"Draft":"s-draft","Sent":"s-sent","Accepted":"s-accepted","Rejected":"s-rejected","Archived":"s-draft"}
TMPL_ICON = {"Agency":"🎨","SaaS":"💻","Consulting":"📊","Marketing":"📣","Development":"⚙️"}
TMPL_DESC = {"Agency":"Creative, design, branding","SaaS":"Software & platforms","Consulting":"Strategy & advisory","Marketing":"Campaigns & growth","Development":"Web & app engineering"}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    brand = get_branding()
    pc = brand.get("primary_color","#4f46e5")
    sc = brand.get("secondary_color","#7c3aed")
    analytics = get_analytics()

    st.markdown(f"""
    <div style="padding:18px 4px 14px;text-align:center;">
        <div style="width:54px;height:54px;background:linear-gradient(135deg,{pc},{sc});
                    border-radius:14px;margin:0 auto;display:flex;align-items:center;
                    justify-content:center;font-size:24px;box-shadow:0 4px 14px rgba(79,70,229,0.4);">📝</div>
        <div style="font-size:15px;font-weight:800;color:white;margin-top:9px;">{brand.get('agency_name','Proposal Agent')}</div>
        <div style="font-size:11px;color:#475569;margin-top:2px;">AI Proposal Generator</div>
    </div>
    <div class="nav-div"></div>
    <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:0.1em;font-weight:600;padding:0 4px;margin-bottom:6px;">Navigation</div>
    """, unsafe_allow_html=True)

    current = st.session_state.get("page","✨ New Proposal")
    for icon, label in NAV:
        full   = f"{icon} {label}"
        active = (current == full)
        if active: st.markdown('<div class="nav-active">', unsafe_allow_html=True)
        btn_lbl = f"✦  {icon}  {label}" if active else f"{icon}  {label}"
        if st.button(btn_lbl, key=f"nav_{label}", use_container_width=True):
            st.session_state.page = full; st.rerun()
        if active: st.markdown("</div>", unsafe_allow_html=True)

    page = st.session_state.get("page","✨ New Proposal")

    st.markdown(f"""
    <div class="nav-div"></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;padding:0 2px;">
        <div style="background:rgba(79,70,229,0.15);border:1px solid rgba(79,70,229,0.3);border-radius:8px;padding:8px;text-align:center;">
            <div style="font-size:18px;font-weight:700;color:white;">{analytics['total']}</div>
            <div style="font-size:10px;color:#64748b;">Proposals</div>
        </div>
        <div style="background:rgba(79,70,229,0.15);border:1px solid rgba(79,70,229,0.3);border-radius:8px;padding:8px;text-align:center;">
            <div style="font-size:18px;font-weight:700;color:#22c55e;">{analytics['win_rate']}%</div>
            <div style="font-size:10px;color:#64748b;">Win Rate</div>
        </div>
    </div>
    <div class="nav-div"></div>
    <div style="font-size:11px;color:#334155;text-align:center;padding:2px 0 8px;">
        Built with ❤️ by <a href="https://www.adityasharma.ai" target="_blank" style="color:#818cf8;text-decoration:none;">adityasharma.ai</a>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: NEW PROPOSAL
# ══════════════════════════════════════════════════════════════════════════════
if page == "✨ New Proposal":
    brand = get_branding()
    st.markdown('<div class="page-hdr"><h1>✨ New Proposal</h1><p>Fill in the details — AI generates your complete professional proposal in seconds</p></div>', unsafe_allow_html=True)

    if not _key():
        st.warning("⚠️  No OpenAI API key found. Go to 🔑 Settings to add one.")

    # Template selector
    st.markdown('<div class="sec-hdr">📐 Choose Template</div>', unsafe_allow_html=True)
    templates = ["Agency","SaaS","Consulting","Marketing","Development"]
    if "sel_tmpl" not in st.session_state: st.session_state.sel_tmpl = "Agency"

    tcols = st.columns(5)
    for col, tmpl in zip(tcols, templates):
        with col:
            sel = (st.session_state.sel_tmpl == tmpl)
            if st.button(f"{TMPL_ICON[tmpl]} {tmpl}", key=f"t_{tmpl}",
                         use_container_width=True, type="primary" if sel else "secondary"):
                st.session_state.sel_tmpl = tmpl; st.rerun()
            st.caption(TMPL_DESC[tmpl])

    selected = st.session_state.sel_tmpl
    st.markdown("<br>", unsafe_allow_html=True)

    # Form
    st.markdown('<div class="sec-hdr">📋 Project Details</div>', unsafe_allow_html=True)
    with st.form("prop_form"):
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            client_name  = st.text_input("👤 Client Name *", placeholder="Acme Corporation")
            budget       = st.text_input("💰 Budget", placeholder="e.g. £15,000 – £25,000")
            agency_input = st.text_input("🏢 Your Agency Name", value=brand.get("agency_name","Your Agency"))
        with r1c2:
            project_type = st.text_input("🎯 Project Type *", placeholder="e.g. E-commerce Website Redesign")
            timeline     = st.text_input("📅 Timeline", placeholder="e.g. 8 weeks")
            extra        = st.text_input("🔍 Extra Context (optional)", placeholder="e.g. Healthcare sector, needs HIPAA compliance")

        requirements = st.text_area("📝 Requirements & Objectives *",
            placeholder="Describe what the client needs:\n• Goal 1\n• Goal 2\n• Technical requirements\n• Success criteria",
            height=160)

        submitted = st.form_submit_button(f"🚀 Generate {selected} Proposal", type="primary", use_container_width=True)

    if submitted:
        if not client_name or not project_type or not requirements:
            st.error("❌ Please fill in Client Name, Project Type, and Requirements.")
        elif not _key():
            st.error("❌ No API key. Go to 🔑 Settings.")
        else:
            prog = st.progress(0); status_el = st.empty()
            steps = [
                (0.12,"📡 Analysing requirements..."),
                (0.25,"✍️  Writing executive summary..."),
                (0.40,"📋 Building scope of work..."),
                (0.55,"💰 Creating pricing packages..."),
                (0.70,"📅 Planning project timeline..."),
                (0.85,"⚖️  Drafting terms & conditions..."),
                (1.00,"✅ Finalising your proposal..."),
            ]
            for pct, msg in steps[:3]:
                prog.progress(pct); status_el.info(msg); time.sleep(0.25)

            with st.spinner("🤖 GPT-4o is writing your proposal — this takes ~20 seconds..."):
                proposal = generate_full_proposal(
                    client_name=client_name, project_type=project_type, budget=budget,
                    timeline=timeline, requirements=requirements, template=selected,
                    agency_name=agency_input or brand.get("agency_name","Your Agency"),
                    extra_context=extra,
                )

            for pct, msg in steps[3:]:
                prog.progress(pct); status_el.info(msg); time.sleep(0.2)

            prog.empty(); status_el.empty()

            if "error" in proposal:
                st.error(f"❌ Generation failed: {proposal['error']}")
            else:
                pid = save_proposal(proposal)
                save_client(client_name)
                st.session_state.cur_proposal = proposal
                st.session_state.cur_pid      = pid
                if agency_input: update_branding(agency_name=agency_input)
                st.success("✅ Proposal generated! Opening preview...")
                time.sleep(0.5)
                st.session_state.page = "📋 My Proposals"; st.rerun()

    # Quick pricing estimator
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">⚡ Quick Pricing Estimator</div>', unsafe_allow_html=True)
    with st.expander("Get a rough estimate before generating — no API call needed... actually uses AI"):
        pe1,pe2,pe3 = st.columns(3)
        with pe1: qtype = st.text_input("Project type", placeholder="Website redesign", key="qp_type")
        with pe2: qreq  = st.text_input("Key requirements", placeholder="5 pages, CMS, responsive", key="qp_req")
        with pe3: qtime = st.text_input("Timeline", placeholder="6-8 weeks", key="qp_time")
        if st.button("⚡ Estimate", key="qp_btn") and qtype:
            with st.spinner("Estimating..."):
                est = quick_pricing_estimate(qtype, qreq, qtime)
            if not est.get("error"):
                ec1,ec2,ec3,ec4 = st.columns(4)
                for col,val,lbl in [(ec1,est.get("recommended",""),"Recommended"),(ec2,est.get("low",""),"Low"),(ec3,est.get("high",""),"High"),(ec4,est.get("hours",""),"Est. Hours")]:
                    with col:
                        st.markdown(f'<div class="metric-card"><div class="metric-val" style="font-size:18px;color:#4f46e5;">{val}</div><div class="metric-lbl">{lbl}</div></div>', unsafe_allow_html=True)
                if est.get("reasoning"): st.info(f"💡 {est['reasoning']}")

    # Landing features
    if not get_proposals():
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="sec-hdr">🚀 What You Get in Every Proposal</div>', unsafe_allow_html=True)
        items = [
            ("📌","Executive Summary","Compelling opening that acknowledges the client's pain points and your solution"),
            ("📋","Scope of Work","Phased breakdown with deliverables, timelines, and clear expectations"),
            ("💰","3 Pricing Packages","Starter, Professional, and Enterprise options to suit every budget"),
            ("📅","Project Timeline","Milestone-based schedule from kickoff to final delivery"),
            ("⭐","Why Choose Us","4 compelling differentiators tailored to the specific project"),
            ("📊","Case Study","Relevant past work showing measurable results"),
            ("⚖️","Terms & Conditions","7 legal clauses including IP, confidentiality, and payment terms"),
            ("📥","PDF + DOCX Export","Professional branded documents ready to send"),
        ]
        cols = st.columns(4)
        for i, (icon, title, desc) in enumerate(items):
            with cols[i%4]:
                st.markdown(f"""
                <div class="card" style="text-align:center;padding:20px 14px;">
                    <div style="font-size:28px;margin-bottom:8px;">{icon}</div>
                    <div style="font-weight:700;color:#0f172a;font-size:13px;margin-bottom:5px;">{title}</div>
                    <div style="font-size:11px;color:#64748b;line-height:1.5;">{desc}</div>
                </div>
                """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: MY PROPOSALS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📋 My Proposals":
    st.markdown('<div class="page-hdr"><h1>📋 My Proposals</h1><p>View, edit, and export your saved proposals</p></div>', unsafe_allow_html=True)

    proposals = get_proposals()
    brand     = get_branding()

    if not proposals:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;background:white;border:1px solid #e2e8f0;border-radius:16px;">
            <div style="font-size:52px;margin-bottom:14px;">📝</div>
            <div style="font-size:18px;font-weight:700;color:#0f172a;">No proposals yet</div>
            <div style="font-size:14px;color:#64748b;margin-top:6px;">Click ✨ New Proposal to create your first one</div>
        </div>""", unsafe_allow_html=True)
        if st.button("✨ Create First Proposal", type="primary"): st.session_state.page="✨ New Proposal"; st.rerun()
        st.stop()

    # Filters
    fc1,fc2,fc3 = st.columns([3,2,1])
    with fc1: search = st.text_input("🔍 Search proposals...", label_visibility="collapsed", placeholder="Search by client, project, title...")
    with fc2: sf = st.selectbox("Filter status", ["All","Draft","Sent","Accepted","Rejected"], label_visibility="collapsed")
    with fc3:
        if st.button("✨ New", type="primary", use_container_width=True): st.session_state.page="✨ New Proposal"; st.rerun()

    filtered = proposals
    if search: filtered = [p for p in filtered if search.lower() in (p.get("client_name","")+p.get("project_type","")+p.get("title","")).lower()]
    if sf != "All": filtered = [p for p in filtered if p.get("status")==sf]
    st.caption(f"{len(filtered)} proposal(s)")

    for prop in filtered:
        pid = prop["id"]
        is_cur = (pid == st.session_state.get("cur_pid"))

        with st.expander(f"{SICON.get(prop.get('status','Draft'),'📝')}  {prop['title']}  ·  {prop['client_name']}  ·  {prop.get('created_at','')[:10]}", expanded=is_cur):
            # Header row
            hc1,hc2,hc3,hc4 = st.columns([3,2,2,1])
            with hc1:
                st.markdown(f"""
                <div style="font-size:12px;color:#64748b;">
                    <span class="{SCSS.get(prop.get('status','Draft'),'s-draft')}">{prop.get('status','Draft')}</span>
                    &nbsp;·&nbsp; {TMPL_ICON.get(prop.get('template',''),'📝')} {prop.get('template','')}
                    &nbsp;·&nbsp; {prop.get('budget','')}
                </div>""", unsafe_allow_html=True)
            with hc2:
                ns = st.selectbox("Status",["Draft","Sent","Accepted","Rejected","Archived"],
                    index=["Draft","Sent","Accepted","Rejected","Archived"].index(prop.get("status","Draft")),
                    key=f"st_{pid}", label_visibility="collapsed")
                if ns != prop.get("status"): update_status(pid, ns); st.rerun()
            with hc3:
                if st.button("👁️ View & Export", key=f"v_{pid}", use_container_width=True):
                    st.session_state.cur_proposal = prop["data"]
                    st.session_state.cur_pid      = pid; st.rerun()
            with hc4:
                if st.button("🗑️", key=f"d_{pid}", use_container_width=True):
                    delete_proposal(pid)
                    if st.session_state.cur_pid == pid:
                        st.session_state.cur_proposal = None; st.session_state.cur_pid = None
                    st.rerun()

            # ── Full proposal view ────────────────────────────────────────────
            if is_cur and st.session_state.cur_proposal:
                proposal = st.session_state.cur_proposal
                meta     = proposal.get("_meta",{})

                st.markdown("---")

                # Hero banner
                pc = brand.get("primary_color","#4f46e5")
                sc = brand.get("secondary_color","#7c3aed")
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,{pc}15,{sc}10);border:1px solid {pc}40;
                            border-radius:14px;padding:22px 26px;margin:8px 0 16px;">
                    <div style="font-size:22px;font-weight:800;color:#0f172a;">{proposal.get('proposal_title','')}</div>
                    <div style="font-size:13px;color:{pc};font-style:italic;margin-top:5px;">{proposal.get('tagline','')}</div>
                    <div style="margin-top:12px;display:flex;gap:20px;flex-wrap:wrap;font-size:12px;color:#64748b;">
                        <span>👤 <strong>{meta.get('client_name','')}</strong></span>
                        <span>💰 {meta.get('budget','')}</span>
                        <span>📅 {meta.get('timeline','')}</span>
                        <span>🗓 {meta.get('today','')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Tabs
                t1,t2,t3,t4,t5 = st.tabs(["📄 Proposal Content","💰 Pricing","📅 Timeline & Next Steps","✉️ Cover Letter","📥 Export"])

                # ── TAB 1: PROPOSAL CONTENT ───────────────────────────────────
                with t1:
                    text_sections = [
                        ("📌 Executive Summary","executive_summary",True),
                        ("🏢 About Us","about_us",False),
                        ("🔴 The Challenge","problem_statement",False),
                        ("💡 Our Solution","proposed_solution",False),
                    ]
                    for title_, key_, expanded_ in text_sections:
                        content = proposal.get(key_,"")
                        if content:
                            with st.expander(title_, expanded=expanded_):
                                # Display with nice formatting
                                for para in str(content).split("\n\n"):
                                    if para.strip():
                                        st.markdown(f'<p style="font-size:14px;color:#374151;line-height:1.75;margin-bottom:12px;">{para.strip()}</p>', unsafe_allow_html=True)
                                # Regenerate
                                ri1,ri2 = st.columns([3,1])
                                with ri2:
                                    if st.button("🔄 Regenerate", key=f"rg_{key_}_{pid}", use_container_width=True):
                                        with st.spinner("Rewriting..."):
                                            new = regenerate_section(title_.split(" ",1)[1] if " " in title_ else title_, proposal)
                                        proposal[key_] = new
                                        update_proposal(pid, proposal)
                                        st.session_state.cur_proposal = proposal; st.rerun()
                                with ri1:
                                    custom = st.text_input("Custom instruction", key=f"ci_{key_}_{pid}",
                                        placeholder="e.g. Make it more concise", label_visibility="collapsed")
                                    if custom and st.button("✍️ Apply", key=f"apply_{key_}_{pid}"):
                                        with st.spinner("Rewriting..."):
                                            new = regenerate_section(title_.split(" ",1)[1] if " " in title_ else title_, proposal, custom)
                                        proposal[key_] = new
                                        update_proposal(pid, proposal)
                                        st.session_state.cur_proposal = proposal; st.rerun()

                    # Scope of Work
                    sow = proposal.get("scope_of_work",[])
                    if sow:
                        st.markdown('<div class="sec-hdr">📋 Scope of Work</div>', unsafe_allow_html=True)
                        for phase in sow:
                            deliv_html = "".join(f'<span style="display:inline-block;background:#eff6ff;color:#2563eb;border:1px solid #bfdbfe;padding:2px 8px;border-radius:8px;font-size:11px;margin:2px;">✓ {d}</span>' for d in phase.get("deliverables",[]))
                            st.markdown(f"""
                            <div class="phase">
                                <div style="font-weight:700;color:#4f46e5;font-size:14px;">{phase.get('phase','')}
                                    <span style="font-size:11px;color:#94a3b8;font-weight:400;margin-left:8px;">⏱ {phase.get('duration','')}</span></div>
                                <div style="font-size:13px;color:#374151;margin-top:5px;margin-bottom:8px;">{phase.get('description','')}</div>
                                <div>{deliv_html}</div>
                            </div>""", unsafe_allow_html=True)

                    # Why us
                    why = proposal.get("why_us",[])
                    if why:
                        st.markdown('<div class="sec-hdr">⭐ Why Choose Us</div>', unsafe_allow_html=True)
                        wc = st.columns(min(len(why),2))
                        for i, r in enumerate(why):
                            with wc[i%2]:
                                st.markdown(f"""
                                <div class="why-card">
                                    <div style="font-weight:700;color:#0f172a;font-size:14px;margin-bottom:5px;">{r.get('title','')}</div>
                                    <div style="font-size:13px;color:#374151;">{r.get('description','')}</div>
                                </div>""", unsafe_allow_html=True)

                    # Case study
                    cs = proposal.get("case_study",{})
                    if cs and cs.get("title"):
                        st.markdown('<div class="sec-hdr">📊 Case Study</div>', unsafe_allow_html=True)
                        st.markdown(f"""
                        <div class="card">
                            <div style="font-size:16px;font-weight:700;color:#4f46e5;margin-bottom:12px;">{cs.get('title','')} · {cs.get('client','')}</div>
                            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;">
                                <div><div style="font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;margin-bottom:5px;">Challenge</div>
                                    <div style="font-size:13px;color:#374151;">{cs.get('challenge','')}</div></div>
                                <div><div style="font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;margin-bottom:5px;">Solution</div>
                                    <div style="font-size:13px;color:#374151;">{cs.get('solution','')}</div></div>
                                <div><div style="font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;margin-bottom:5px;">Result</div>
                                    <div style="font-size:22px;font-weight:800;color:#22c55e;">{cs.get('result','')}</div></div>
                            </div>
                        </div>""", unsafe_allow_html=True)

                    # Terms
                    terms = proposal.get("terms",{})
                    if terms:
                        st.markdown('<div class="sec-hdr">⚖️ Terms & Conditions</div>', unsafe_allow_html=True)
                        for k, v in terms.items():
                            if v:
                                st.markdown(f"""
                                <div style="padding:9px 0;border-bottom:1px solid #f1f5f9;">
                                    <span style="font-size:12px;font-weight:700;color:#4f46e5;min-width:180px;display:inline-block;">{k.replace('_',' ').title()}</span>
                                    <span style="font-size:13px;color:#374151;">{v}</span>
                                </div>""", unsafe_allow_html=True)

                # ── TAB 2: PRICING ────────────────────────────────────────────
                with t2:
                    pricing = proposal.get("pricing",{})
                    if pricing.get("intro"):
                        st.info(pricing["intro"])

                    packages = pricing.get("packages",[])
                    if packages:
                        pcols = st.columns(len(packages))
                        for col, pkg in zip(pcols, packages):
                            with col:
                                is_rec = pkg.get("recommended",False)
                                rec_html = '<div style="background:#4f46e5;color:white;font-size:10px;font-weight:700;padding:2px 8px;border-radius:10px;margin-bottom:8px;display:inline-block;">★ RECOMMENDED</div>' if is_rec else ""
                                feats_html = "".join(f'<div style="font-size:12px;padding:4px 0;border-bottom:1px solid #f1f5f9;color:#374151;">✓ {f}</div>' for f in pkg.get("features",[]))
                                st.markdown(f"""
                                <div class="pkg {'pkg-rec' if is_rec else ''}">
                                    {rec_html}
                                    <div class="pkg-name">{pkg.get('name','')}</div>
                                    <div class="pkg-price">{pkg.get('price','')}</div>
                                    <div style="font-size:12px;color:#64748b;margin-bottom:12px;">{pkg.get('description','')}</div>
                                    {feats_html}
                                </div>""", unsafe_allow_html=True)

                    if pricing.get("payment_terms"):
                        st.markdown(f"""
                        <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;padding:12px 16px;margin-top:14px;">
                            <strong style="color:#92400e;">💳 Payment Terms:</strong>
                            <span style="font-size:13px;color:#374151;"> {pricing['payment_terms']}</span>
                        </div>""", unsafe_allow_html=True)

                    inc = pricing.get("included",[]); exc = pricing.get("excluded",[])
                    if inc or exc:
                        ic1,ic2 = st.columns(2)
                        with ic1:
                            if inc:
                                st.markdown("**✅ What's Included**")
                                for item in inc: st.markdown(f'<div style="font-size:13px;padding:3px 0;">✓ {item}</div>', unsafe_allow_html=True)
                        with ic2:
                            if exc:
                                st.markdown("**❌ What's Excluded**")
                                for item in exc: st.markdown(f'<div style="font-size:13px;padding:3px 0;color:#94a3b8;">✗ {item}</div>', unsafe_allow_html=True)

                # ── TAB 3: TIMELINE & NEXT STEPS ─────────────────────────────
                with t3:
                    tl = proposal.get("timeline",[])
                    if tl:
                        st.markdown('<div class="sec-hdr">📅 Project Milestones</div>', unsafe_allow_html=True)
                        for i, m in enumerate(tl, 1):
                            st.markdown(f"""
                            <div class="tl-step">
                                <div class="tl-dot">{i}</div>
                                <div>
                                    <div style="font-weight:700;color:#0f172a;font-size:14px;">{m.get('milestone','')}</div>
                                    <div style="font-size:12px;color:#4f46e5;font-weight:600;margin-top:2px;">📅 {m.get('week','')}</div>
                                    <div style="font-size:13px;color:#374151;margin-top:3px;">{m.get('description','')}</div>
                                </div>
                            </div>""", unsafe_allow_html=True)

                    ns = proposal.get("next_steps",[])
                    if ns:
                        st.markdown('<div class="sec-hdr">🚀 Next Steps</div>', unsafe_allow_html=True)
                        for i, step in enumerate(ns,1):
                            icon_ = "✅" if i==1 else "⬜"
                            st.markdown(f'<div style="font-size:14px;padding:8px 0;color:#374151;">{icon_} <strong>{i}.</strong> {step}</div>', unsafe_allow_html=True)

                    closing = proposal.get("closing_statement","")
                    if closing:
                        st.markdown(f"""
                        <div style="background:linear-gradient(135deg,{brand.get('primary_color','#4f46e5')}12,{brand.get('secondary_color','#7c3aed')}10);
                                    border:2px solid {brand.get('primary_color','#4f46e5')}40;
                                    border-radius:14px;padding:22px;margin-top:16px;
                                    font-size:14px;color:#374151;line-height:1.75;font-style:italic;">
                            "{closing}"
                        </div>""", unsafe_allow_html=True)

                # ── TAB 4: COVER LETTER ───────────────────────────────────────
                with t4:
                    st.markdown('<div class="sec-hdr">✉️ Cover Email</div>', unsafe_allow_html=True)
                    cc1,cc2 = st.columns([2,2])
                    with cc1: tone = st.selectbox("Tone", ["professional","warm and friendly","formal","concise and direct"], key=f"tone_{pid}")
                    with cc2:
                        if st.button("✉️ Generate Cover Letter", key=f"gcl_{pid}", type="primary", use_container_width=True):
                            with st.spinner("Writing..."):
                                cover = generate_cover_letter(proposal, tone)
                            st.session_state[f"cl_{pid}"] = cover

                    if f"cl_{pid}" in st.session_state:
                        cover_text = st.session_state[f"cl_{pid}"]
                        st.markdown(f'<div class="cover-box">{cover_text}</div>', unsafe_allow_html=True)
                        st.download_button("⬇️ Download Cover Letter .txt", data=cover_text,
                            file_name=f"cover_{meta.get('client_name','client').lower().replace(' ','_')}.txt",
                            mime="text/plain", key=f"dlcl_{pid}")

                # ── TAB 5: EXPORT ─────────────────────────────────────────────
                with t5:
                    st.markdown('<div class="sec-hdr">📥 Export Your Proposal</div>', unsafe_allow_html=True)
                    safe_name = meta.get('client_name','client').lower().replace(' ','_')

                    ex1, ex2 = st.columns(2)
                    with ex1:
                        st.markdown("""
                        <div class="card" style="text-align:center;">
                            <div style="font-size:48px;margin-bottom:12px;">📄</div>
                            <div style="font-weight:700;font-size:17px;color:#0f172a;margin-bottom:6px;">PDF Report</div>
                            <div style="font-size:12px;color:#64748b;line-height:1.6;">
                                Branded PDF with your colors, logo, tables, pricing matrix, and all sections — ready to email to clients
                            </div>
                        </div>""", unsafe_allow_html=True)
                        with st.spinner("Building PDF..."):
                            pdf_bytes = export_pdf(proposal, brand)
                        st.download_button("⬇️ Download PDF", data=pdf_bytes,
                            file_name=f"proposal_{safe_name}.pdf", mime="application/pdf",
                            use_container_width=True, type="primary", key=f"pdf_{pid}")

                    with ex2:
                        st.markdown("""
                        <div class="card" style="text-align:center;">
                            <div style="font-size:48px;margin-bottom:12px;">📝</div>
                            <div style="font-weight:700;font-size:17px;color:#0f172a;margin-bottom:6px;">Word Document</div>
                            <div style="font-size:12px;color:#64748b;line-height:1.6;">
                                Fully editable DOCX file — customise in Microsoft Word or Google Docs before sending
                            </div>
                        </div>""", unsafe_allow_html=True)
                        with st.spinner("Building DOCX..."):
                            docx_bytes = export_docx(proposal, brand)
                        st.download_button("⬇️ Download DOCX", data=docx_bytes,
                            file_name=f"proposal_{safe_name}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True, key=f"docx_{pid}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: CLIENTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👥 Clients":
    st.markdown('<div class="page-hdr"><h1>👥 Client Management</h1><p>Track clients and their proposal history</p></div>', unsafe_allow_html=True)

    with st.form("cl_form", clear_on_submit=True):
        st.markdown("**➕ Add New Client**")
        cf1,cf2,cf3 = st.columns(3)
        with cf1: cl_name    = st.text_input("Name *", placeholder="Acme Corporation", label_visibility="collapsed")
        with cf2: cl_email   = st.text_input("Email", placeholder="contact@acme.com", label_visibility="collapsed")
        with cf3: cl_company = st.text_input("Company", placeholder="Acme Corp", label_visibility="collapsed")
        cl_notes = st.text_input("Notes", placeholder="Industry, key contacts, notes...", label_visibility="collapsed")
        if st.form_submit_button("Add Client ➕", type="primary") and cl_name:
            save_client(cl_name, cl_email, cl_company, cl_notes); st.success(f"✅ {cl_name} added!"); st.rerun()

    clients   = get_clients()
    proposals = get_proposals()

    st.markdown(f'<div class="sec-hdr">👥 All Clients ({len(clients)})</div>', unsafe_allow_html=True)
    if not clients:
        st.info("No clients yet. They are added automatically when you create proposals, or add one above.")
    for c in clients:
        c_props = [p for p in proposals if p.get("client_name","").lower()==c["name"].lower()]
        accepted = sum(1 for p in c_props if p.get("status")=="Accepted")
        with st.expander(f"👤 {c['name']}  ·  {len(c_props)} proposal(s)"):
            cc1,cc2 = st.columns([3,2])
            with cc1:
                info_parts = []
                if c.get("email"):   info_parts.append(f"📧 {c['email']}")
                if c.get("company"): info_parts.append(f"🏢 {c['company']}")
                if c.get("notes"):   info_parts.append(f"📝 {c['notes']}")
                info_parts.append(f"🗓 Added: {c.get('created_at','')[:10]}")
                for part in info_parts:
                    st.markdown(f'<div style="font-size:13px;color:#374151;padding:2px 0;">{part}</div>', unsafe_allow_html=True)
            with cc2:
                st.markdown(f"""
                <div style="display:flex;gap:10px;">
                    <div class="metric-card" style="flex:1;min-width:80px;">
                        <div class="metric-val">{len(c_props)}</div><div class="metric-lbl">Proposals</div>
                    </div>
                    <div class="metric-card" style="flex:1;min-width:80px;">
                        <div class="metric-val" style="color:#22c55e;">{accepted}</div><div class="metric-lbl">Accepted</div>
                    </div>
                </div>""", unsafe_allow_html=True)
            if c_props:
                st.markdown("**Recent proposals:**")
                for p in c_props[:3]:
                    st.markdown(f'<div style="font-size:13px;padding:3px 0;color:#374151;">{SICON.get(p.get("status","Draft"),"📝")} {p["title"]} · {p.get("created_at","")[:10]}</div>', unsafe_allow_html=True)
            if st.button(f"✨ New Proposal for {c['name']}", key=f"np_{c['id']}", type="primary"):
                st.session_state.page="✨ New Proposal"; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Dashboard":
    import plotly.graph_objects as go

    st.markdown('<div class="page-hdr"><h1>📊 Analytics Dashboard</h1><p>Track proposal performance and win rates</p></div>', unsafe_allow_html=True)

    analytics = get_analytics()
    proposals = get_proposals()

    if analytics["total"] == 0:
        st.info("No proposals yet. Create your first one to see analytics!")
        st.stop()

    # KPIs
    k1,k2,k3,k4,k5 = st.columns(5)
    for col,val,lbl,color in [
        (k1, analytics["total"],   "Total Proposals", "#4f46e5"),
        (k2, analytics["sent"],    "Sent",            "#3b82f6"),
        (k3, analytics["accepted"],"Accepted",        "#22c55e"),
        (k4, f"{analytics['win_rate']}%","Win Rate",  "#f59e0b"),
        (k5, analytics["draft"],   "In Draft",        "#94a3b8"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card" style="border-top:3px solid {color};"><div class="metric-val" style="color:{color};">{val}</div><div class="metric-lbl">{lbl}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    ch1, ch2 = st.columns(2)

    with ch1:
        st.markdown('<div class="sec-hdr">📊 Proposals by Status</div>', unsafe_allow_html=True)
        sd = analytics.get("by_status",{})
        if sd:
            SC = {"Draft":"#94a3b8","Sent":"#3b82f6","Accepted":"#22c55e","Rejected":"#ef4444","Archived":"#e2e8f0"}
            fig = go.Figure(go.Pie(labels=list(sd.keys()), values=list(sd.values()),
                marker_colors=[SC.get(k,"#4f46e5") for k in sd], hole=0.45,
                textinfo="label+value"))
            fig.update_layout(margin=dict(l=0,r=0,t=10,b=10),height=260,paper_bgcolor="white",showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

    with ch2:
        st.markdown('<div class="sec-hdr">📋 Proposals by Template</div>', unsafe_allow_html=True)
        td = analytics.get("by_template",{})
        if td:
            TC = {"Agency":"#4f46e5","SaaS":"#0ea5e9","Consulting":"#f59e0b","Marketing":"#ec4899","Development":"#22c55e"}
            fig2 = go.Figure(go.Bar(x=list(td.values()), y=list(td.keys()), orientation="h",
                marker_color=[TC.get(k,"#4f46e5") for k in td], marker_line_width=0))
            fig2.update_layout(plot_bgcolor="white",paper_bgcolor="white",
                margin=dict(l=10,r=10,t=10,b=10),height=260,
                xaxis=dict(showgrid=True,gridcolor="#f1f5f9",title="Count"))
            st.plotly_chart(fig2, use_container_width=True)

    # Recent proposals table
    st.markdown('<div class="sec-hdr">📋 All Proposals</div>', unsafe_allow_html=True)
    for p in proposals:
        sc_ = {"Draft":"#94a3b8","Sent":"#3b82f6","Accepted":"#22c55e","Rejected":"#ef4444"}.get(p.get("status","Draft"),"#94a3b8")
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    padding:10px 16px;background:white;border:1px solid #e2e8f0;border-radius:10px;margin:4px 0;">
            <div>
                <span style="font-size:13px;font-weight:600;color:#0f172a;">{p['title'][:50]}</span>
                <span style="font-size:12px;color:#94a3b8;margin-left:8px;">· {p['client_name']}</span>
            </div>
            <div style="display:flex;align-items:center;gap:16px;">
                <span style="font-size:11px;color:#64748b;">{TMPL_ICON.get(p.get('template',''),'📝')} {p.get('template','')}</span>
                <span style="font-size:12px;color:#64748b;">{p.get('budget','')}</span>
                <span style="font-size:12px;color:{sc_};font-weight:700;">{SICON.get(p.get('status','Draft'),'📝')} {p.get('status','Draft')}</span>
                <span style="font-size:11px;color:#94a3b8;">{p.get('created_at','')[:10]}</span>
            </div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: BRANDING
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🎨 Branding":
    st.markdown('<div class="page-hdr"><h1>🎨 Branding & Customisation</h1><p>Your brand applied to every exported proposal</p></div>', unsafe_allow_html=True)

    brand = get_branding()
    bc1, bc2 = st.columns([3,2])

    with bc1:
        st.markdown('<div class="sec-hdr">🏢 Agency Identity</div>', unsafe_allow_html=True)
        with st.form("brand_form"):
            ag_name    = st.text_input("Agency / Company Name *", value=brand.get("agency_name",""))
            ag_tagline = st.text_input("Tagline", value=brand.get("tagline",""), placeholder="Building the future, together.")
            bf1,bf2    = st.columns(2)
            with bf1:
                ag_email   = st.text_input("Email", value=brand.get("email",""))
                ag_phone   = st.text_input("Phone", value=brand.get("phone",""))
            with bf2:
                ag_website = st.text_input("Website", value=brand.get("website",""))
                ag_address = st.text_input("Address", value=brand.get("address",""))
            st.markdown('<div class="sec-hdr">🎨 Brand Colors</div>', unsafe_allow_html=True)
            cc1,cc2 = st.columns(2)
            with cc1: pri_color = st.color_picker("Primary Color", value=brand.get("primary_color","#4f46e5"))
            with cc2: sec_color = st.color_picker("Secondary Color", value=brand.get("secondary_color","#7c3aed"))
            if st.form_submit_button("💾 Save Branding", type="primary", use_container_width=True):
                update_branding(agency_name=ag_name, tagline=ag_tagline, email=ag_email,
                    phone=ag_phone, website=ag_website, address=ag_address,
                    primary_color=pri_color, secondary_color=sec_color)
                st.success("✅ Branding saved!"); st.rerun()

        # Logo
        st.markdown('<div class="sec-hdr">🖼️ Logo Upload</div>', unsafe_allow_html=True)
        logo_file = st.file_uploader("Upload logo (PNG, JPG, SVG)", type=["png","jpg","jpeg","svg"])
        if logo_file:
            update_branding(logo_bytes=logo_file.read(), logo_name=logo_file.name)
            st.success(f"✅ Logo uploaded: {logo_file.name}"); st.rerun()
        if brand.get("logo_bytes"):
            st.image(brand["logo_bytes"], caption=brand.get("logo_name","Logo"), width=180)
            if st.button("🗑️ Remove Logo"):
                update_branding(logo_bytes=None, logo_name=""); st.rerun()

    with bc2:
        st.markdown('<div class="sec-hdr">👁️ Live Preview</div>', unsafe_allow_html=True)
        brand = get_branding()
        pc = brand.get("primary_color","#4f46e5")
        sc = brand.get("secondary_color","#7c3aed")
        contacts = " · ".join(x for x in [brand.get("email",""), brand.get("website","")] if x)

        st.markdown(f"""
        <div style="background:white;border:1px solid #e2e8f0;border-radius:16px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.08);">
            <div style="background:linear-gradient(135deg,{pc},{sc});padding:30px 24px;text-align:center;">
                <div style="font-size:22px;font-weight:800;color:white;">{brand.get('agency_name','Your Agency')}</div>
                <div style="font-size:13px;color:rgba(255,255,255,0.8);margin-top:4px;">{brand.get('tagline','')}</div>
            </div>
            <div style="padding:20px 24px;">
                <div style="font-size:18px;font-weight:800;color:#0f172a;">Business Proposal</div>
                <div style="font-size:12px;color:{pc};margin-top:4px;font-style:italic;">Prepared exclusively for: Your Client</div>
                <div style="margin-top:14px;background:#f8fafc;border-radius:8px;padding:12px;font-size:12px;color:#64748b;">
                    <strong style="color:#374151;">Prepared by:</strong> {brand.get('agency_name','')}<br>
                    <strong style="color:#374151;">Date:</strong> Today<br>
                    <strong style="color:#374151;">Status:</strong> <span style="color:#22c55e;">Confidential</span>
                </div>
                {"<div style='margin-top:12px;padding-top:12px;border-top:1px solid #f1f5f9;font-size:11px;color:#94a3b8;'>"+contacts+"</div>" if contacts else ""}
            </div>
            <div style="height:5px;background:linear-gradient(90deg,{pc},{sc});"></div>
        </div>
        <div style="margin-top:16px;background:white;border:1px solid #e2e8f0;border-radius:12px;padding:16px;">
            <div style="font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;margin-bottom:10px;">Color Palette</div>
            <div style="display:flex;gap:12px;">
                <div style="text-align:center;">
                    <div style="width:52px;height:52px;border-radius:12px;background:{pc};box-shadow:0 3px 8px rgba(0,0,0,0.15);margin:0 auto 5px;"></div>
                    <div style="font-size:10px;color:#64748b;font-weight:600;">Primary</div>
                    <div style="font-size:10px;color:#94a3b8;">{pc}</div>
                </div>
                <div style="text-align:center;">
                    <div style="width:52px;height:52px;border-radius:12px;background:{sc};box-shadow:0 3px 8px rgba(0,0,0,0.15);margin:0 auto 5px;"></div>
                    <div style="font-size:10px;color:#64748b;font-weight:600;">Secondary</div>
                    <div style="font-size:10px;color:#94a3b8;">{sc}</div>
                </div>
                <div style="text-align:center;flex:1;">
                    <div style="width:100%;height:52px;border-radius:12px;background:linear-gradient(135deg,{pc},{sc});box-shadow:0 3px 8px rgba(0,0,0,0.15);margin-bottom:5px;"></div>
                    <div style="font-size:10px;color:#64748b;font-weight:600;">Gradient</div>
                    <div style="font-size:10px;color:#94a3b8;">Used in headers</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔑 Settings":
    st.markdown('<div class="page-hdr"><h1>🔑 Settings</h1><p>Configure your OpenAI API key to power proposal generation</p></div>', unsafe_allow_html=True)

    current_key = _key()
    if current_key:
        src = "Your key" if st.session_state.get("user_api_key","").strip() else "Server-configured"
        st.markdown(f"""<div style="background:#f0fdf4;border:2px solid #86efac;border-radius:12px;padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;gap:12px;">
            <div style="font-size:24px;">🟢</div>
            <div><div style="font-weight:700;color:#15803d;">API Key Active — Proposal generation enabled</div>
            <div style="font-size:12px;color:#166534;">Source: {src}</div></div></div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style="background:#fef2f2;border:2px solid #fca5a5;border-radius:12px;padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;gap:12px;">
            <div style="font-size:24px;">🔴</div>
            <div><div style="font-weight:700;color:#dc2626;">No API Key</div>
            <div style="font-size:12px;color:#991b1b;">Enter your OpenAI key below to generate proposals</div></div></div>""", unsafe_allow_html=True)

    s1, s2 = st.columns([3,2])
    with s1:
        st.markdown('<div class="sec-hdr">🔑 OpenAI API Key</div>', unsafe_allow_html=True)
        entered = st.text_input("Key", value=st.session_state.get("user_api_key",""),
                                type="password", placeholder="sk-proj-...", label_visibility="collapsed")
        c1,c2 = st.columns(2)
        with c1:
            if st.button("💾 Save Key", type="primary", use_container_width=True):
                if entered.strip().startswith("sk-"):
                    st.session_state.user_api_key = entered.strip()
                    os.environ["OPENAI_API_KEY"] = entered.strip()
                    st.success("✅ Key saved!"); st.rerun()
                elif entered.strip(): st.error("Keys must start with 'sk-'")
                else: st.error("Please enter a key.")
        with c2:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.user_api_key = ""
                os.environ.pop("OPENAI_API_KEY",None); st.rerun()

        st.markdown("""<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;padding:12px 14px;margin-top:10px;font-size:12px;color:#78350f;">
            🔒 Stored in browser session only. Never saved to any server or database. Cleared on tab close.</div>""", unsafe_allow_html=True)

        st.markdown('<div class="sec-hdr">💰 Cost Per Proposal</div>', unsafe_allow_html=True)
        for item, cost in [
            ("Full proposal generation (GPT-4o)","~$0.04"),
            ("Cover letter","~$0.005"),
            ("Section regeneration","~$0.003"),
            ("Quick pricing estimate","~$0.001"),
            ("Total per proposal (full)","~$0.05"),
        ]:
            bold = "font-weight:700;color:#4f46e5;" if "Total" in item else ""
            st.markdown(f"""<div style="display:flex;justify-content:space-between;padding:6px 12px;background:{'#eff6ff' if 'Total' in item else 'white'};border:1px solid #e2e8f0;border-radius:8px;margin:2px 0;">
                <span style="font-size:12px;color:#374151;">{item}</span>
                <span style="font-size:12px;{bold}">{cost}</span></div>""", unsafe_allow_html=True)

    with s2:
        st.markdown('<div class="sec-hdr">📋 Get an API Key</div>', unsafe_allow_html=True)
        st.markdown("""<div style="background:white;border:1px solid #e2e8f0;border-radius:12px;padding:18px;">
            <div style="font-size:13px;color:#374151;line-height:2.2;">
                1. Visit <a href="https://platform.openai.com/api-keys" target="_blank" style="color:#4f46e5;font-weight:600;">platform.openai.com/api-keys</a><br>
                2. Sign in or create an account<br>
                3. Click <strong>+ Create new secret key</strong><br>
                4. Name it "Proposal Generator"<br>
                5. Copy the key (starts with <code>sk-</code>)<br>
                6. Paste it on the left and save
            </div></div>""", unsafe_allow_html=True)

        st.markdown('<div class="sec-hdr">📝 Proposal Sections Generated</div>', unsafe_allow_html=True)
        for s in ["Executive Summary (3-4 paragraphs)","About Us","Problem Statement","Proposed Solution","Scope of Work (3 phases)","Project Timeline (5 milestones)","3 Pricing Packages","Why Choose Us (4 reasons)","Case Study with measurable results","7 Legal Terms & Conditions","Next Steps","Closing Statement"]:
            st.markdown(f'<div style="font-size:12px;padding:3px 0;color:#374151;">✅ {s}</div>', unsafe_allow_html=True)

    if current_key:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✨ Create Your First Proposal →", type="primary"):
            st.session_state.page="✨ New Proposal"; st.rerun()
