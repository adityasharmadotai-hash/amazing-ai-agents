# Job Market Intelligence Agent
**HireGen.co · Dice + Indeed + HubSpot MCP**

Monitors Dice and Indeed for companies actively hiring engineers at scale, scores them as HireGen.co prospects, and automatically syncs to HubSpot CRM.

---

## How it works

```
User configures search
        │
        ▼
┌─────────────────────────────────────────────┐
│            Claude claude-sonnet-4-6 Agent               │
│                                             │
│  1. Search Dice + Indeed (parallel)         │
│  2. Aggregate postings by company           │
│  3. Score: A (5+ roles) B (3-4) C (1-2)    │
│  4. Enrich A+B with Indeed company data     │
│  5. Create/update HubSpot records           │
│  6. Return structured JSON report           │
└─────────────────────────────────────────────┘
        │
        ▼
  Streamlit Dashboard
  (metrics + prospect cards + CRM status)
```

## MCP servers used

| Server | Purpose | URL |
|--------|---------|-----|
| Dice | Search engineering job postings | `https://mcp.dice.com/mcp` |
| Indeed | Job postings + company enrichment | `https://mcp.indeed.com/claude/mcp` |
| HubSpot | Create/update CRM records | `https://mcp.hubspot.com/anthropic` |

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set your Anthropic API key
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Ensure MCP servers are connected
Log into claude.ai and connect Dice, Indeed, and HubSpot under Settings → Integrations. The MCP URLs are already configured in `agent.py`.

### 4. Run the app
```bash
streamlit run app.py
```

---

## File structure

```
job_market_agent/
├── app.py          # Streamlit UI — sidebar config, dashboard, prospect cards
├── agent.py        # Agent core — system prompt, MCP config, orchestration
├── requirements.txt
└── README.md
```

## Prospect scoring

| Score | Criteria | Action |
|-------|----------|--------|
| **Priority A** | 5+ relevant roles in 30 days | Urgent outreach this week |
| **Priority B** | 3–4 roles | Reach out this week |
| **Priority C** | 1–2 roles | Add to pipeline |

**Priority boosts:** AI/ML/LLM roles, remote-friendly positions, SF Bay Area.

## HubSpot sync

For each qualified prospect, the agent:
- Searches existing HubSpot records to avoid duplicates
- **Creates** a new company record if not found
- **Updates** an existing record with fresh hiring signal data
- Adds a **note** with role count, top titles, and recommended outreach angle
- Sets deal stage to `Prospect - Hiring Signal Detected`

## Customization

Edit `agent.py`:
- `SYSTEM_PROMPT` — adjust scoring thresholds, priority logic, HubSpot field mapping
- `MCP_SERVERS` — add or swap job board MCP servers
- `run_agent()` — change default params or add new filters

Edit `app.py`:
- Sidebar defaults (`default_categories`, `location`, `min_roles`)
- Dashboard layout and card design
- Export formats (currently: JSON download)

---

*Built by Aditya Sharma · HireGen.co · AdityaSharma.ai*
