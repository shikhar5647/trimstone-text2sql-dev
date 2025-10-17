## Trimstone Text-to-SQL (LangGraph + Gemini)

An agentic Text-to-SQL app using LangGraph and Google Gemini that connects to MS SQL Server, understands natural language, generates safe T‑SQL, validates, and executes with a human‑in‑the‑loop approval step. Includes schema ingestion from DB, Excel, or a predefined manual schema.

### Features
- Robust NLU and SQL generation prompts tuned for MS SQL Server
- Safety checks: SELECT‑only, no multi‑statements, approval gate
- TOP 100 auto‑limit for large queries
- Schema ingestion sources:
  - Live DB introspection (INFORMATION_SCHEMA)
  - Excel (`trimstone_final.xlsx`)
  - Manual schema for `client`, `contacts`, `project`
- Streamlit UI: stepper, SQL preview, validation, results table, CSV download

### Prerequisites
- Python 3.11+
- ODBC Driver 18 for SQL Server
- Network access to the MS SQL Server
- Google Gemini API key

### Setup
1) Clone or open this folder in Cursor.
2) Create `.env` in `trimstone-text2sql-dev/`:
```
GEMINI_API_KEY="your-key"
GEMINI_MODEL="gemini-2.5-pro"  # or gemini-2.5-flash

DB_SERVER="your-server"
DB_DATABASE="your-db"
DB_USERNAME="your-user"
DB_PASSWORD="your-password"

LOG_LEVEL=INFO
CACHE_TTL=3600
```
3) (Optional) Place `trimstone_final.xlsx` at the project root to enable Excel schema.
4) Create/activate a virtualenv and install deps:
```
python -m venv sd
sd\Scripts\activate
pip install -r requirements.txt
```

### Run
```
streamlit run app.py
```

### Using the App
1) Verify DB connection in the sidebar.
2) Under "Schema Source":
   - Load schema from DB, Excel, or Manual.
3) Ask a question, review the generated SQL, check validation.
4) Approve to execute and view results; download CSV as needed.

### Manual Schema (built-in)
- `client(id, name, slug, email, phone, address1, address2, city, state, country, zipcode, created_at, updated_at, team_id, channel_id, drive_id, delta_token, drive_item_id, hubspot_id, owner_name, status, industry, type, no_employees, description, timezone, created_by, client_number)`
- `contacts(id, first_name, last_name, email, owner, phone, mobile, stage, client_id, client_name, hubspot_id, created_at, updated_at)`
- `project(id, name, client_id, description, slug, category, status, priority, start_date, end_date, currency, budget, created_by, updated_by, created_at, updated_at, billing_type, amount_billed, budget_hours, team_id, channel_id, drive_id, drive_subscription_id, delta_token, drive_item_id, hubspot_id, xero_id, owner_id, owner_email, last_modified_date, project_number)`

### Notes
- Only SELECT statements are allowed; app blocks destructive SQL.
- The generator adds `TOP 100` when the user doesn’t specify limits.
- If Excel schema columns differ, adjust in `database/schema_cache.py`.

### Troubleshooting
- "Missing required configuration" → ensure `.env` exists at project root and values are set; the app now loads `.env` explicitly.
- ODBC issues → verify ODBC Driver 18 installed and DSN connectivity.
