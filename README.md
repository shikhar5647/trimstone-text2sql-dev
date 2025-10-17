# Trimstone Text2SQL Assistant

A Streamlit-based Text→SQL assistant that uses an agent pipeline to convert natural-language questions into SQL, validate and (optionally) execute them against a Microsoft SQL Server database. The project is designed to work offline using a schema cache (`schema_cache.json`) so SQL generation can proceed even when DB connectivity is unavailable.

---

## Table of contents
- Project overview
- Architecture & components
- How it works (pipeline)
- Quickstart (Windows)
- Environment / configuration
- Schema sources (cache / Excel / manual)
- Running the app
- Debugging & common issues
- Development & testing
- Suggested improvements
- License

---

## Project overview
This repository provides:
- A Streamlit UI for entering natural-language queries and viewing SQL + results.
- An agent pipeline that:
  - Detects intent & entities (NLU agent)
  - Selects schema context (schema agent)
  - Generates SQL (text2sql agent)
  - Formats SQL (formatter agent)
  - Validates SQL for safety (validator agent)
  - Executes approved SQL (executor agent)
- A schema caching mechanism so LLMs see a stable DB schema without every request hitting the DB.

Primary goals:
- Produce correct SQL using cached schema.
- Keep DB execution optional and manual (human-in-the-loop approval).
- Allow offline generation using cached schema file.

---

## Architecture & components
- `app.py` — Streamlit entrypoint and UI. Manages session state and orchestrates workflow execution.
- `database/`
  - `connection.py` — DB connection wrapper. Handles queries, fetching tables/columns, and test_connection.
  - `schema_cache.py` — Loads/saves schema cache, refreshes from DB or Excel, exposes schema as text for LLM context.
- `agents/` — Agent modules implementing the pipeline:
  - `nlu_agent.py`
  - `schema_agent.py`
  - `text2sql_agent.py`
  - `formatter_agent.py`
  - `validator_agent.py`
  - `executor_agent.py`
- `graph/`
  - `workflow.py` — Assembles and executes the agent pipeline for a single user query.
  - `state.py` — Workflow state object / helpers.
- `ui/components.py` — Streamlit UI helper functions for rendering schema, SQL, results, and status.
- `config/`
  - `settings.py` — Project settings, paths, TTL for cache, etc.
  - `secrets.py` — Loads and validates sensitive settings (from .env).
- `utils/`
  - `logger.py` — Logging setup
  - `helpers.py` — Misc helpers used across the app

---

## How it works (pipeline)
1. User submits a natural-language question in the UI.
2. NLU agent extracts intent and entities.
3. Schema agent builds a minimal schema context (from schema_cache or DB) containing only relevant tables and columns.
4. Text2SQL agent generates candidate SQL using schema context + question.
5. Formatter agent normalizes formatting and parametrization.
6. Validator agent runs safety checks (DROP/ALTER etc.) and syntactic validation.
7. Human reviews generated SQL; if approved, Executor runs the SQL against the DB and returns results.
8. Results are displayed in a formatted table in the UI.

Note: If DB is not available, the pipeline still generates SQL using the schema cache. Execution step will fail or be skipped.

---

## Quickstart (Windows)
1. Clone repository (or open project folder in VS Code).
2. Create / activate a Python environment:
   - `python -m venv .venv`
   - `.venv\Scripts\activate`
3. Install dependencies (example list — adapt to your runtime):
   - `pip install streamlit pandas openpyxl python-dotenv requests`
   - If you use pyodbc: `pip install pyodbc`
4. Populate `.env` with your keys and DB credentials (see below).
5. Start the app:
   - `streamlit run app.py`

---

## Environment / configuration
The app reads configuration from `.env` via `config/secrets.py`. Example keys:
- `GEMINI_API_KEY` — Google Gemini / LLM API key
- `GEMINI_MODEL` — model name
- `DB_SERVER`, `DB_DATABASE`, `DB_USERNAME`, `DB_PASSWORD` — SQL Server connection details
- `PROJECT_ROOT` — root path (defaults to project directory)
- `CACHE_TTL` — schema cache TTL in seconds

Important:
- Do **NOT** commit secret keys.
- If DB password contains special characters, verify how the driver/connection builder treats them; escaping may be required.

---

## Schema sources
1. `schema_cache.json` (preferred offline) — loaded at startup from project root (path defined in settings).
2. Live DB — if connection is healthy, cache can be refreshed from DB.
3. Excel — `trimstone_final.xlsx` expected layout:
   - Either one sheet with columns `[table_name, column_name, data_type, is_nullable]`
   - Or one sheet per table with rows listing columns.

The UI provides buttons:
- Load schema from Excel
- Load manual schema (predefined for quick demos)
- Refresh schema cache (pull from DB)

---

## Running the app
- Start: `streamlit run app.py`
- In the sidebar you can:
  - Test DB connection manually (non-blocking)
  - Load/refresh schema
  - See table list and detailed schema
- Enter questions in the main area and click "Generate SQL". The app will show intent, generated SQL, validation results, and allow manual approval for execution.

---

## Debugging & common issues
- "Incorrect syntax near '1'." when testing connection:
  - Some DB drivers are strict about unnamed columns or the test query text. Use a portable test query (e.g., `SELECT 1 AS result`) or adapt the driver.
  - If using FreeTDS / pymssql, driver differences can cause odd error messages. Consider switching to pyodbc + Microsoft ODBC Driver 18 for SQL Server.
- "Unknown error" from driver:
  - Check credentials, server name, port, firewall rules and driver installation.
  - Try a small Python script to connect using the same connection logic to isolate driver vs app logic.
- SQL execution fails but SQL looks correct:
  - Verify schema (table/column names) in `schema_cache.json` match actual DB (case/quoting).
  - If executing, run the generated SQL directly in SSMS to see server side error details.
- Want to avoid DB execution while iterating on prompts:
  - Use the schema cache and do not press "Execute". Execution is human-in-the-loop; you can review SQL only.

Logging:
- Logs are produced by `utils/logger.py`. Check logs for stack traces and DB driver messages.

---

## Development & testing
- Files to inspect for debugging generation: `agents/text2sql_agent.py`, `agents/schema_agent.py`, `graph/workflow.py`.
- To validate schema cache: open `database/schema_cache.py`. You can force-refresh to get a fresh schema or load from Excel.
- Unit tests: not included by default. Suggested approach:
  - Add pytest and create tests for:
    - schema_cache load/save/refresh
    - text2sql agent input→SQL deterministic cases
    - validator agent safety checks
- Formatting & linting:
  - Use black / ruff in CI locally.

---

## Suggested improvements
- Add a dedicated `requirements.txt` with pinned versions.
- Add unit tests for agent modules and DB wrapper.
- Add "offline mode" toggle to UI that disables DB actions and emphasizes using cached schema.
- Improve DB connection code to use pyodbc and parameterized queries. Normalize column name casing from DB driver for consistent agents.
- Add example `schema_cache.json` and sample Excel in `data/` for demos.

---

## License
Add your preferred license (MIT/Apache2/Proprietary). This repository currently has no license file.

---

If you want, I can:
- Create a sample `requirements.txt` and `README` additions with commands to install the ODBC driver on Windows.
- Add an "offline mode" toggle in `app.py` and a non-blocking DB test button.
- Add a sample `schema_cache.json` and an example Excel file for testing.
