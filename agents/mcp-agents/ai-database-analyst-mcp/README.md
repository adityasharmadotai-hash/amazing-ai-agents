# 🧠 AI Database Analyst — MCP Agent

Chat with your SQL database in plain English. The AI Database Analyst inspects
your schema, understands table relationships, generates **safe, optimised SQL**,
executes it, explains the results, builds interactive charts and exports
professional reports — all wired together through a **Model Context Protocol
(MCP)** tool layer and powered by **Google Gemini**.

🔗 **Live demo:** <https://amazing-ai-agents.streamlit.app/>
📖 **Hands-on guide:** [Tutorial.md](Tutorial.md)

> Read-only by default. Destructive statements are blocked unless you explicitly
> enable write mode.

---

## ✨ Features

- **Natural-language → SQL** with automatic schema inspection and relationship
  discovery.
- **Safe execution**: read-only by default; `DROP`/`DELETE`/`UPDATE`/`TRUNCATE`/
  `ALTER`/`INSERT` are blocked unless write mode is enabled. Parameterised
  queries, identifier validation, multi-statement injection protection.
- **MCP tool layer** — 10 independently-callable tools (schema, table, column,
  index, relationship, statistics, SQL executor, CSV/PDF export, chart
  generator), served over JSON-RPC stdio.
- **Auto visualisation** — Plotly bar / line / pie / scatter / area / histogram /
  heatmap, with automatic chart-type selection.
- **AI insights & reports** — executive summaries, key metrics, recommendations,
  anomalies and opportunities.
- **SQL optimisation** — index suggestions, JOIN/`SELECT *` warnings, query
  simplification hints and live execution-plan reading.
- **Exports** — CSV, Excel, JSON, Markdown and PDF.
- **Multi-database** — SQLite, MySQL, PostgreSQL and DuckDB, with connection
  pooling, validation, timeouts and automatic reconnect.
- **Resilient AI** — auto-falls back to a supported Gemini model if the
  configured one is unavailable for your key.
- **Session memory** — conversation history, previous SQL/results, schema cache,
  saved queries and recent connections.
- **Modern dashboard** — dark mode, responsive layout, metric cards.

---

## 🏗 Architecture

```
ai-database-analyst-mcp/
├── streamlit_app.py         # Streamlit Cloud entry point (next to requirements)
├── run.py                   # Local launcher / dual-mode entry point
├── app/                     # Streamlit UI
│   ├── main.py              # builds the page (header, sidebar, settings, chat)
│   ├── context.py           # dependency-injection container (AnalystContext)
│   └── components/          # sidebar, chat, results, charts, settings
├── core/                    # config, models, exceptions, logging, session memory
├── agents/                  # Gemini client + DatabaseAnalystAgent (orchestrator)
├── mcp/                     # MCP tool registry, tools, JSON-RPC stdio server
├── database/                # connection mgr, repository, schema inspector, safe SQL
├── services/                # chart, export, optimisation, query, report services
├── utils/                   # SQL/format/validation helpers
├── prompts/                 # LLM prompt templates
├── scripts/                 # sample database generator
├── tests/                   # pytest suite (no API key required)
├── exports/  logs/  sample_data/
├── requirements.txt   requirements-dev.txt   .env.example   pytest.ini
```

**Request flow:** `Chat UI → DatabaseAnalystAgent → Gemini (plan + SQL) →
SafeSQLGuard → Repository (execute) → Services (insights / charts / optimise /
export) → Results UI`. The same capabilities are exposed as MCP tools through the
registry and the stdio server.

---

## 🚀 Installation (local)

Requires **Python 3.11+** (tested on 3.11–3.13).

```bash
cd agents/mcp-agents/ai-database-analyst-mcp

# 1. Create & activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env        # Windows: copy .env.example .env
#  → edit .env and set GEMINI_API_KEY

# 4. (optional) create the sample database — the app also auto-creates it
python scripts/create_sample_db.py
```

Get a Gemini API key from <https://aistudio.google.com/app/apikey>.

---

## ▶️ Running (local)

```bash
python run.py                  # ensures sample DB + launches Streamlit
# or:
streamlit run streamlit_app.py
# or:
streamlit run app/main.py
```

Open <http://localhost:8501>, paste your API key in the **Settings** panel (it
auto-opens until a key is found), connect from the sidebar (the SQLite sample DB
is pre-filled), and start asking questions.

---

## ☁️ Deploying to Streamlit Community Cloud

1. Push this repo to GitHub.
2. On <https://share.streamlit.io>, create an app pointing at
   **Main file path:** `agents/mcp-agents/ai-database-analyst-mcp/streamlit_app.py`
   (the launcher `run.py` also works as an entry point).
3. **Settings → Secrets**, add your key:
   ```toml
   GEMINI_API_KEY = "your-key-here"
   ```
   (You can also paste the key into the in-app Settings panel.)
4. Deploy. The sample SQLite database is created automatically on first run.

> If the build fails, the only source-build-risky packages are `psycopg2-binary`
> and `duckdb`. If you only need the SQLite demo, comment those two lines out of
> `requirements.txt`.

---

## ⚙️ Configuration

All configuration lives in `.env` (see `.env.example`) or Streamlit secrets.

| Variable | Description | Default |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key | _required for AI_ |
| `GEMINI_MODEL` | Model name | `gemini-2.0-flash` |
| `READ_ONLY_MODE` | Block write statements | `true` |
| `DB_TYPE` | `sqlite` / `mysql` / `postgresql` / `duckdb` | `sqlite` |
| `DB_NAME` | DB name or file path | `sample_data/northwind.db` |
| `MAX_RESULT_ROWS` | Row cap per query | `10000` |
| `QUERY_TIMEOUT` | Per-query timeout (s) | `30` |

The API key, model, temperature, max tokens, chart theme, auto-explain /
auto-chart toggles and **write mode** can also be changed at runtime in the
**⚙️ Settings** panel.

---

## 🔌 MCP server (standalone)

The same capabilities are available as MCP tools over JSON-RPC (stdio):

```bash
python -m mcp.server
```

```json
{"jsonrpc":"2.0","id":1,"method":"tools/list"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"sql_executor","arguments":{"sql":"SELECT COUNT(*) FROM customers"}}}
```

Available tools: `schema_reader`, `table_inspector`, `column_inspector`,
`sql_executor`, `index_inspector`, `relationship_analyzer`,
`statistics_collector`, `csv_export`, `pdf_export`, `chart_generator`.

---

## 💬 Example questions

- Show today's sales
- Top 20 customers by revenue
- Revenue by month
- Find duplicate users
- Users inactive for 90 days
- Most profitable products
- Average order value
- Employee performance
- Compare last month vs this month
- Which tables contain email?
- Explain this SQL / Optimize this query / Find missing indexes

See [Tutorial.md](Tutorial.md) for a guided walkthrough.

---

## 🧪 Testing

The suite runs entirely on an in-memory SQLite database — **no API key or
network required**.

```bash
pip install -r requirements-dev.txt
pytest                 # run all tests
pytest --cov           # with coverage
```

---

## 🖼 Screenshots

> _Placeholder — add screenshots of the dashboard, chat, charts and reports here._

| Dashboard | Chat & SQL | Charts & Reports |
|---|---|---|
| _screenshot_ | _screenshot_ | _screenshot_ |

---

## 🔒 Security

- Passwords are never logged or written to disk; they live in the environment /
  session only and are URL-encoded into connection strings.
- All user values are bound as parameters; identifiers are validated against a
  strict pattern.
- Read-only mode + a defence-in-depth keyword scan block destructive SQL.
- Multi-statement payloads containing writes are rejected (injection guard).

---

## 📄 License

MIT License. Provided as-is for educational and internal use.
