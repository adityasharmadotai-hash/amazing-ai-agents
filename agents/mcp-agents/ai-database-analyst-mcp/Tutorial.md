# 📖 Tutorial — AI Database Analyst MCP Agent

A hands-on walkthrough: from first launch to asking questions, reading the
results, exporting reports, connecting your own database and calling the MCP
tools directly.

🔗 Live demo: <https://amazing-ai-agents.streamlit.app/>

---

## 1. Get a Gemini API key

1. Go to <https://aistudio.google.com/app/apikey>.
2. Click **Create API key** and copy it.

The app works without a key (you can still browse the schema and run manual SQL),
but natural-language questions, AI insights and reports need one.

---

## 2. Launch the app

### Option A — Use the hosted demo
Open <https://amazing-ai-agents.streamlit.app/>. Skip to step 3.

### Option B — Run locally
```bash
cd agents/mcp-agents/ai-database-analyst-mcp
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```
The app opens at <http://localhost:8501>. The sample database is created
automatically the first time it runs.

---

## 3. Add your API key

When no key is detected, the **⚙️ Settings — API Key & Preferences** panel opens
automatically at the top of the page.

1. Paste your key into **Gemini API Key**.
2. (Optional) choose a **Model** — `gemini-2.0-flash` is a good default. If a
   model isn't available for your key, the app automatically falls back to a
   supported one.
3. Click **Apply settings**. You'll see ✅ *Gemini API key detected*.

> On Streamlit Cloud you can instead set it once under **Manage app → Settings →
> Secrets**:
> ```toml
> GEMINI_API_KEY = "your-key-here"
> ```

### Other settings worth knowing
| Setting | What it does |
|---|---|
| **Temperature** | Higher = more creative SQL/insights; keep low (0.1–0.3) for accuracy. |
| **Max Tokens** | Upper bound on response length. |
| **Chart Theme** | Plotly theme for generated charts. |
| **Auto explain SQL** | Generate a plain-language explanation of each query. |
| **Auto generate charts** | Pick and draw the best chart for each result. |
| **🔓 Enable write mode** | Allows `INSERT/UPDATE/DELETE/DDL`. Off by default — leave off unless you mean it. |

---

## 4. Connect to a database

Use the **sidebar** (left). The fields change based on the database type.

### Try the bundled sample (fastest)
1. **Database Type:** `sqlite`
2. **Database File Path:** `sample_data/northwind.db` (pre-filled)
3. Click **Connect**.

You'll see *Connected … N tables* and a status pill showing **Connected**,
**Read-only**, and **AI ready**.

The sample database contains:
`customers`, `employees`, `products`, `orders`, `order_items`, `users` — seeded
with realistic data (including some orders dated *today*, duplicate user emails
and inactive users) so the example questions return meaningful results.

---

## 5. Ask your first question

Type in the chat box at the bottom, or click an **example** chip.

Try: **`Top 20 customers by revenue`**

What happens behind the scenes:
1. The agent reads the cached schema and identifies the relevant tables.
2. Gemini produces a query *plan* (intent + SQL + assumptions).
3. The **SafeSQLGuard** validates the SQL (read-only check, injection guard).
4. The repository executes it with a row cap and timing.
5. Insights, recommendations, a chart and an SQL explanation are generated.

### Reading the answer
The result is shown in tabs:

| Tab | Contents |
|---|---|
| 📋 **Results** | The data table + **download** buttons (CSV / Excel / JSON / PDF / Markdown). |
| 📊 **Chart** | An interactive Plotly chart. Use the **Chart type** dropdown to switch (bar/line/pie/…). |
| 🧠 **Insights** | AI summary, key findings and recommendations with real figures. |
| 🛠 **Recommendations** | SQL optimisation tips, index suggestions and performance warnings. |
| 🔎 **SQL & Plan** | Plain-language explanation, assumptions, and **Show execution plan**. |

Above the tabs you'll see metric cards: **Rows**, **Execution time**, **Columns**
and **Mode**. The **Generated SQL** is shown with **Save** and **Re-run** buttons.

---

## 6. More questions to try

| Question | Demonstrates |
|---|---|
| `Show today's sales` | Date filtering on live "today" rows |
| `Revenue by month` | Time-series → line chart |
| `Most profitable products` | Joins + aggregation (price − cost) |
| `Average order value` | Aggregation across orders/items |
| `Find duplicate users` | `GROUP BY ... HAVING COUNT(*) > 1` |
| `Users inactive for 90 days` | Date math on `last_login` |
| `Employee performance` | Joins across employees/orders |
| `Which tables contain email?` | Schema search (no SQL needed) |
| `Compare last month vs this month` | Conditional aggregation |

Follow-ups work too — after "Revenue by month", ask **"now only completed
orders"** and the agent uses the previous query as context.

---

## 7. Export a report

In the **📋 Results** tab:
- **CSV / Excel / JSON** — instant downloads of the raw result set.
- **📄 PDF Report** / **📝 MD Report** — generates an AI executive report
  (Executive Summary, Business Insights, Key Metrics, Recommendations, Anomalies,
  Opportunities) with a data sample, then offers a download and a preview.

All exports are also saved under the `exports/` folder.

---

## 8. Save and reuse queries

- Click **💾 Save** under any generated SQL, give it a name → it appears under
  **Saved Queries** in the sidebar.
- From the sidebar you can **Run** or **Delete** a saved query.
- **Recent Connections** lets you reconnect with one click.

---

## 9. Run SQL manually

Expand **⌨️ Run SQL manually** to write SQL yourself. It goes through the same
safety guard and enrichment (charts, insights, optimisation) as AI-generated
queries.

---

## 10. Write mode (advanced, optional)

By default the app is **read-only** and blocks any statement that modifies data.
To run writes:

1. Open **Settings** → tick **🔓 Enable write mode** → **Apply settings**.
2. Ask a modifying question, or run write SQL manually.
3. You'll get an explicit **Confirm and execute** step before anything runs.

Turn it back off when you're done. Never enable write mode against a production
database you don't intend to change.

---

## 11. Connect your own database

Pick the **Database Type** in the sidebar and fill in the fields:

| Type | Fields needed |
|---|---|
| **SQLite** | File path (e.g. `data/app.db`, or `:memory:`) |
| **DuckDB** | File path (e.g. `data/analytics.duckdb`) |
| **MySQL** | Host, Port (3306), Username, Password, Database |
| **PostgreSQL** | Host, Port (5432), Username, Password, Database |

Then click **Connect**. The app validates the connection, inspects the schema and
caches it. Passwords are never logged or stored on disk.

> Drivers: MySQL uses `PyMySQL`, PostgreSQL uses `psycopg2-binary`, DuckDB uses
> `duckdb-engine` — all included in `requirements.txt`.

---

## 12. Use the MCP tools directly

Every capability is also an independently-callable **MCP tool**. Start the
JSON-RPC server:

```bash
python -m mcp.server
```

Then send line-delimited JSON-RPC on stdin:

```json
{"jsonrpc":"2.0","id":1,"method":"tools/list"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"schema_reader","arguments":{"include_row_counts":true}}}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"sql_executor","arguments":{"sql":"SELECT country, COUNT(*) AS n FROM customers GROUP BY country"}}}
{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"column_inspector","arguments":{"keyword":"email"}}}
```

| Tool | Purpose |
|---|---|
| `schema_reader` | Full schema (tables, columns, keys, indexes) |
| `table_inspector` | One table + optional sample rows |
| `column_inspector` | List a table's columns, or find columns by keyword |
| `sql_executor` | Safely execute SQL |
| `index_inspector` | List indexes; suggest missing ones for a query |
| `relationship_analyzer` | Explicit + inferred table relationships |
| `statistics_collector` | Descriptive stats for a table |
| `csv_export` / `pdf_export` | Run a query and export |
| `chart_generator` | Recommend/build the best chart for a query |

---

## 13. Troubleshooting

| Symptom | Fix |
|---|---|
| **Blank page on Streamlit Cloud** | Set Main file path to `…/streamlit_app.py` (or `run.py`) and **Reboot**. |
| **"Error installing requirements"** | Ensure you're using this folder's `requirements.txt`; for SQLite-only demos you can remove `psycopg2-binary` and `duckdb`. |
| **"model … is not available"** | Pick a current model in Settings (e.g. `gemini-2.0-flash`); the app also auto-falls back. |
| **"rate limit reached"** | You've hit Gemini quota — wait and retry, or use a key with higher limits. |
| **"blocked in read-only mode"** | Intended — enable write mode in Settings if you really want to modify data. |
| **Connection failed** | Check host/port/credentials; for cloud DBs ensure the host allows external connections. |

Logs are written to `logs/app.log` (questions, generated SQL, timings, errors).

---

Happy analysing! For full reference, see [README.md](README.md).
