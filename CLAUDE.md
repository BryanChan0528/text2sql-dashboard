# CLAUDE.md — Text-to-SQL Dynamic Dashboard

## Project Purpose
AI-powered dashboard that lets users ask questions in plain English and see the results as tables and charts. Built to demonstrate Applied AI Engineering: vibe coding, AI-as-co-developer, end-to-end ownership.

## Stack (KISS)
- **Backend**: Python 3.11 + FastAPI + uvicorn
- **LLM**: DeepSeek API (`deepseek-chat`) via `openai` SDK (OpenAI-compatible)
- **Database**: SQLite (`data/deriv.db`) — file-based, zero config, ships with the app
- **Frontend**: Single `static/index.html` — Chart.js, vanilla JS, no build step
- **Deploy**: Render free tier (Web Service + 1GB persistent disk at `/data`)

## Database Schema

```sql
-- Trading activity
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    client_id INTEGER,
    symbol TEXT,
    side TEXT,           -- 'buy' or 'sell'
    amount REAL,         -- stake amount in USD
    profit REAL,         -- realized profit/loss
    duration_seconds INTEGER,
    timestamp TEXT       -- ISO8601
);

-- Client profiles
CREATE TABLE clients (
    id INTEGER PRIMARY KEY,
    country TEXT,
    account_type TEXT,   -- 'real' or 'demo'
    signup_date TEXT     -- ISO8601 date
);

-- Tradeable instruments
CREATE TABLE symbols (
    symbol TEXT PRIMARY KEY,
    asset_class TEXT,    -- 'forex', 'crypto', 'indices', 'commodities'
    market TEXT          -- e.g. 'EURUSD', 'BTC/USD'
);
```

## How to Run Locally

```bash
# 1. Install deps
pip install -r requirements.txt

# 2. Set API key
cp .env.example .env
# Edit .env → add your ANTHROPIC_API_KEY

# 3. Seed the database
python seed.py

# 4. Start server
uvicorn main:app --reload

# 5. Open browser
open http://localhost:8000
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Serves dashboard HTML |
| POST | `/query` | `{question}` → `{sql, columns, rows, chart_suggestion, explanation}` |
| GET | `/schema` | Returns DB schema for UI sidebar |
| GET | `/health` | Render health check → `{status: "ok"}` |

## Text-to-SQL Prompt Pattern

The system uses `skills.md` skill `text_to_sql`. The prompt is assembled as:

```
[skill: text_to_sql from skills.md]
Schema: {schema_string}
Question: {user_question}
```

Claude returns a ```sql block. The app extracts the SQL, validates it (SELECT only), executes it, then calls `chart_type` skill to pick the right Chart.js type.

## Safety Guardrails
- Only `SELECT` statements are executed — enforced by regex before execution
- Blocked keywords: `DROP`, `INSERT`, `UPDATE`, `DELETE`, `ALTER`, `CREATE`, `TRUNCATE`
- Max 500 rows returned
- Query timeout: 5 seconds

## AI Workflow (Vibe Coding)
This project is built with Claude Code as co-developer. When adding features:
1. Describe the feature in plain English in the chat
2. Reference `skills.md` for the relevant skill prompt
3. Claude generates the code; review and test
4. Guardrails are non-negotiable — never skip SQL validation

## Environment Variables
- `DEEPSEEK_API_KEY` — required, get a key at https://platform.deepseek.com/api_keys
- `DEEPSEEK_MODEL` — optional, defaults to `deepseek-chat`
- `DB_PATH` — optional, defaults to `data/deriv.db` (use `/data/deriv.db` on Render)
- `MAX_ROWS` — optional, defaults to `500`
