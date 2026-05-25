# 📝 Build an AI Proposal Generator from Scratch

### Step-by-Step Tutorial

---

<div align="center">

⭐ **[Star the repo](https://github.com/adityasharmadotai-hash)** &nbsp;·&nbsp;
🌐 **[adityasharma.ai](https://www.adityasharma.ai)** &nbsp;·&nbsp;
💼 **[LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)** &nbsp;·&nbsp;
📺 **[YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)** &nbsp;·&nbsp;
🚀 **[AI Jobs USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

</div>

---

> **What you'll build:** A 6-page Streamlit app that takes 5 client inputs and uses GPT-4o to generate a complete 12-section business proposal — with scope of work, 3 pricing packages, timeline, legal terms, and case study — then exports it as a branded PDF or DOCX.

---

## Table of Contents

1. [What Are We Building?](#1-what-are-we-building)
2. [How It Works](#2-how-it-works)
3. [Prerequisites](#3-prerequisites)
4. [Project Setup](#4-project-setup)
5. [File 1 — generator.py](#5-file-1--generatorpy)
6. [File 2 — storage.py](#6-file-2--storagepy)
7. [File 3 — exporter.py](#7-file-3--exporterpy)
8. [File 4 — app.py](#8-file-4--apppy)
9. [Running Locally](#9-running-locally)
10. [Deploying to Streamlit Cloud](#10-deploying-to-streamlit-cloud)
11. [Common Errors](#11-common-errors)
12. [What You Learned](#12-what-you-learned)
13. [What's Next](#13-whats-next)

---

## 1. What Are We Building?

Writing proposals manually takes 4-8 hours. A good one still often loses because it's generic. This agent generates a tailored, professional proposal in 20-30 seconds for $0.05.

```
Input:
  Client: Acme Corporation
  Project: E-commerce Website Redesign
  Budget: £15,000–£25,000
  Timeline: 8 weeks
  Requirements: Mobile-first, Shopify, SEO, CRM integration

Output (12 sections, 2000+ words):
  ✅ Proposal Title: "Transforming Acme's Digital Commerce: A Strategic Redesign"
  ✅ Executive Summary (4 paragraphs)
  ✅ Scope of Work (3 phases, 9 deliverables)
  ✅ 3 Pricing Packages (£12k / £18k / £24k)
  ✅ 5-Milestone Timeline
  ✅ 7 Legal Terms & Conditions
  ✅ Case Study with real metrics
  ✅ Download PDF + DOCX
```

---

## 2. How It Works

```
┌─────────────────────────────────────────────────────┐
│                 ARCHITECTURE                        │
│                                                     │
│  User fills form (5 fields + template selection)   │
│           ↓                                         │
│  generator.py — 1 GPT-4o call (4000 tokens)        │
│  System prompt: specialist role per template        │
│  User prompt: all inputs + exact JSON schema        │
│  Returns: complete proposal as structured JSON      │
│           ↓                                         │
│  storage.py — st.session_state                      │
│  Save proposal, client, update status               │
│           ↓                                         │
│  app.py — 6-page dashboard                          │
│  Display all sections with regeneration buttons     │
│           ↓                                         │
│  exporter.py — PDF (ReportLab) + DOCX (python-docx) │
│  Branded with custom colors and agency name         │
└─────────────────────────────────────────────────────┘
```

**Three modules, one clear job each:**

| File | Job | Key tech |
|------|-----|----------|
| `generator.py` | AI proposal generation | OpenAI GPT-4o |
| `storage.py` | In-session data store | st.session_state |
| `exporter.py` | Document export | ReportLab, python-docx |

---

## 3. Prerequisites

- Python 3.10+
- OpenAI API key
- ~$0.05 per full proposal

---

## 4. Project Setup

```bash
mkdir proposal-agent && cd proposal-agent
mkdir modules

python3 -m venv venv && source venv/bin/activate
pip install streamlit openai reportlab python-docx plotly python-dotenv

cp .env.example .env  # add OPENAI_API_KEY
```

---

## 5. File 1 — `generator.py`

> **What this file does:** Uses GPT-4o with specialist system prompts per template type. One API call returns all 12 sections as structured JSON.

### The single-call architecture

The key insight is sending ONE large, well-structured prompt instead of 12 separate calls:

```python
user = f"""Generate a complete {template} proposal and return EXACTLY this JSON:
{{
  "proposal_title": "Compelling title",
  "executive_summary": "3-4 paragraphs...",
  "scope_of_work": [{{"phase":"...","duration":"...","deliverables":["..."]}}],
  "pricing": {{"packages": [{{"name":"Starter","price":"£X","features":["..."]}}]}},
  "timeline": [{{"milestone":"...","week":"Week X","description":"..."}}],
  "terms": {{"intellectual_property":"...","payment":"..."}},
  ...
}}"""
```

**Why this works:** GPT-4o is excellent at following exact JSON schemas. By showing it the complete structure with example values, it fills in every field without hallucinating extra keys or missing required ones.

### Template contexts — specialist prompting

```python
TEMPLATE_CONTEXTS = {
    "Agency":     "You are a senior account manager at a top creative agency. Write confidently, creatively, results-focused.",
    "SaaS":       "You are a SaaS solutions architect. Write technically yet accessibly, focused on ROI.",
    "Consulting": "You are a senior Big 4 consultant. Write authoritatively and strategically.",
    "Marketing":  "You are a growth marketing director. Write data-driven and results-oriented.",
    "Development":"You are a lead software engineer and CTO. Write precisely and delivery-focused.",
}
```

Different templates need different tones. An Agency proposal should be creative and bold. A Consulting proposal should be analytical and authoritative. The system prompt sets this persona before generating content.

### JSON parsing with fence stripping

```python
def _parse_json(text: str):
    # GPT-4o sometimes wraps in ```json ... ``` even when told not to
    return json.loads(re.sub(r"```(?:json)?|```","",text).strip())
```

### Metadata attachment

After generation, we attach a `_meta` dict to store the original inputs:

```python
data["_meta"] = {
    "client_name": client_name,
    "project_type": project_type,
    "template": template,
    "generated_at": datetime.now().isoformat(),
    ...
}
```

This lets any module (exporter, regenerator) access the original context without re-querying the user.

### Section regeneration

Individual sections can be rewritten without regenerating the entire proposal:

```python
def regenerate_section(section_name, proposal, instruction=""):
    meta = proposal.get("_meta", {})
    # Sends just the section + context, returns only the new text
    return _call(system, user, tokens=700)
```

---

## 6. File 2 — `storage.py`

> **What this file does:** Uses `st.session_state` as an in-memory database for proposals, clients, and branding. No external database required — everything persists within the browser tab.

### Session state as a database

```python
def init_stores():
    defaults = {
        "proposals": [],   # list of proposal dicts
        "clients": [],     # list of client dicts
        "branding": {...},  # agency name, colors, logo
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
```

Streamlit reruns the full script on every interaction. `st.session_state` persists between reruns — it's the equivalent of a database for the session.

### Proposal structure

```python
{
    "id": "abc123",                 # 12-char UUID for button keys
    "title": "Proposal Title",
    "client_name": "Acme Corp",
    "status": "Draft",             # Draft | Sent | Accepted | Rejected
    "template": "Agency",
    "created_at": "2025-01-15 14:30",
    "data": { ...full proposal... }  # the complete GPT-4o output
}
```

### Win rate calculation

```python
accepted = status_counts.get("Accepted", 0)
sent     = status_counts.get("Sent", 0)
win_rate = round(accepted / max(sent + accepted, 1) * 100, 1)
```

`max(..., 1)` prevents division by zero when no proposals are sent yet.

---

## 7. File 3 — `exporter.py`

> **What this file does:** Converts the proposal JSON into a professional PDF (ReportLab) and an editable DOCX (python-docx), both branded with the user's custom colors.

### Color conversion

```python
def _hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

# Convert for ReportLab:
pr  = _hex_to_rgb("#4f46e5")       # → (79, 70, 229)
PRI = colors.Color(pr[0]/255, pr[1]/255, pr[2]/255)
```

### ReportLab story pattern

```python
story = []
story.append(Paragraph("Proposal Title", H1_style))
story.append(HRFlowable(width="100%", color=PRIMARY))
story.append(Spacer(1, 0.2*inch))

# Pricing table
table = Table(data, colWidths=[1.8*inch, 1.4*inch, 3.4*inch])
table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), SECONDARY),  # header row
    ("TEXTCOLOR",  (0,0), (-1,0), WHITE),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [LIGHT, WHITE]),
]))
story.append(table)

doc.build(story)  # renders all flowables to PDF
```

### HTML escaping for ReportLab

ReportLab's `Paragraph` class interprets `<` and `>` as XML tags. Always escape:

```python
def _safe(text) -> str:
    return str(text).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
```

---

## 8. File 4 — `app.py`

> **What this file does:** 6-page Streamlit dashboard. The New Proposal page has template selection, a detailed form, and a step progress bar. My Proposals has 5 tabs per proposal: content, pricing, timeline, cover letter, export.

### The 6 pages

| Page | Key feature |
|------|-------------|
| ✨ New Proposal | Template pills, form, step progress bar, quick estimator |
| 📋 My Proposals | Expandable cards, 5 tabs, status tracking, regenerate sections |
| 👥 Clients | Client directory with proposal counts and history |
| 📊 Dashboard | Pie chart by status, bar chart by template, proposal table |
| 🎨 Branding | Color pickers, logo upload, live brand preview |
| 🔑 Settings | API key, cost breakdown, sections list |

### Template selection with state

```python
if "sel_tmpl" not in st.session_state: st.session_state.sel_tmpl = "Agency"
tcols = st.columns(5)
for col, tmpl in zip(tcols, templates):
    with col:
        is_selected = (st.session_state.sel_tmpl == tmpl)
        if st.button(f"{icon} {tmpl}", type="primary" if is_selected else "secondary"):
            st.session_state.sel_tmpl = tmpl
            st.rerun()
```

### Step progress bar

```python
steps = [
    (0.12, "📡 Analysing requirements..."),
    (0.25, "✍️  Writing executive summary..."),
    ...
    (1.00, "✅ Finalising proposal..."),
]
prog = st.progress(0)
status_el = st.empty()

for pct, msg in steps[:3]:
    prog.progress(pct)
    status_el.info(msg)
    time.sleep(0.25)

# The actual API call happens here
with st.spinner("🤖 GPT-4o writing..."):
    proposal = generate_full_proposal(...)

for pct, msg in steps[3:]:  # animate remaining steps
    prog.progress(pct)
    status_el.info(msg)
    time.sleep(0.2)
```

### Section regeneration with custom instructions

```python
ri1, ri2 = st.columns([3,1])
with ri2:
    if st.button("🔄 Regenerate", key=f"rg_{key}_{pid}"):
        new = regenerate_section(section_name, proposal)
        proposal[key] = new
        update_proposal(pid, proposal)
        st.session_state.cur_proposal = proposal
        st.rerun()
with ri1:
    custom = st.text_input("Custom instruction", placeholder="Make it more concise")
    if custom and st.button("✍️ Apply"):
        new = regenerate_section(section_name, proposal, custom)
        # update and rerun...
```

---

## 9. Running Locally

```bash
source venv/bin/activate
streamlit run app.py
```

### First run walkthrough

1. **🔑 Settings** → enter your OpenAI API key → Save
2. **🎨 Branding** → set agency name and colors
3. **✨ New Proposal** → select "Agency" template
4. Fill in: Client Name, Project Type, Budget, Timeline, Requirements
5. Click **🚀 Generate Agency Proposal**
6. Watch the 7-step progress bar animate
7. Auto-navigates to **📋 My Proposals** → proposal is open
8. Click **📄 Proposal Content** tab → read each section
9. Click **🔄 Regenerate** on Executive Summary → rewrite it
10. Click **💰 Pricing** tab → view 3 packages
11. Click **✉️ Cover Letter** → Generate → download
12. Click **📥 Export** → Download PDF → Download DOCX

---

## 10. Deploying to Streamlit Cloud

```bash
git add . && git commit -m "AI Proposal Generator" && git push
```

1. [share.streamlit.io](https://share.streamlit.io) → New app
2. Select repo, main file: `app.py`
3. **Advanced → Secrets:**

```toml
OPENAI_API_KEY = "sk-your-key"
```

4. Deploy ✅

---

## 11. Common Errors

| Error | Fix |
|-------|-----|
| `Invalid API key` | Go to 🔑 Settings → re-enter key |
| `JSON parse error` | GPT-4o returned malformed JSON — try again |
| `reportlab not found` | `pip install reportlab` |
| `python-docx not found` | `pip install python-docx` |
| Proposal is generic | Add more detail to Requirements field |
| `Invalid format: TOML` | Use `KEY = "value"` with quotes in Streamlit secrets |

---

## 12. What You Learned

- ✅ **Large structured GPT-4o calls** — sending a complete JSON schema in the prompt
- ✅ **Template-based system prompting** — different specialist roles per template type
- ✅ **JSON schema enforcement** — exact field names with example values
- ✅ **Section-level regeneration** — targeted rewrites without full regeneration
- ✅ **Session state as database** — proposals, clients, branding in memory
- ✅ **ReportLab branded PDFs** — story pattern, tables, custom colors
- ✅ **python-docx generation** — headings, paragraphs, tables, styling
- ✅ **Hex to RGB conversion** — applying brand colors to both PDF and DOCX
- ✅ **Step progress bars** — animating before/during/after API calls
- ✅ **Streamlit form patterns** — `st.form()` with multi-column layouts
- ✅ **Status tracking** — proposal lifecycle (Draft → Sent → Accepted/Rejected)

---

## 13. What's Next

### Easy
- **Email sending** — integrate SendGrid to email proposals directly from the app
- **Proposal versioning** — track edits and allow rollback

### Intermediate
- **Supabase persistence** — save proposals across sessions and devices
- **PDF digital signature** — add client e-signature via DocuSign API

### Advanced
- **CRM integration** — push accepted proposals to HubSpot or Salesforce
- **Multi-language proposals** — generate in Spanish, French, German

---

## ⭐ Enjoyed this?

- ⭐ **[Star the repository](https://github.com/adityasharmadotai-hash)**
- 🌐 **[Visit adityasharma.ai](https://www.adityasharma.ai)**
- 💼 **[Follow on LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)**
- 📺 **[Subscribe on YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)**
- 🚀 **[AI Jobs in the USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

---

*Built with ❤️ by [Aditya Sharma](https://www.adityasharma.ai) · OpenAI GPT-4o + ReportLab + Streamlit*
