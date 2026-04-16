# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pip install -r requirements.txt

python seed.py                              # create data/deriv.db (idempotent)
uvicorn main:app --reload                   # dev server → http://localhost:8000
uvicorn main:app --host 0.0.0.0 --port $PORT  # production (Render)
```

## Environment variables

| Variable | Required | Default | Notes |
|---|---|---|---|
| `GROQ_API_KEY` | One of these two must be set | — | Primary LLM provider |
| `OPENROUTER_API_KEY` | One of these two must be set | — | Fallback LLM provider |
| `DB_PATH` | No | `data/deriv.db` | Set to `/data/deriv.db` on Render (persistent disk) |
| `MAX_ROWS` | No | `500` | Max rows returned per `/query` call |

## Architecture

### Request flow

```
POST /query {question}
  → generate_sql()       calls call_llm() with text_to_sql skill
  → validate_sql()       SELECT-only check + DDL/DML keyword block
  → validate_tables()    rejects hallucinated table names against live DB
  → sqlite execute       with PRAGMA query_only = ON
  → suggest_chart()      calls call_llm() with chart_type skill
  → explain_query()      calls call_llm() with explain_sql skill
```

All three LLM calls go through `call_llm()` in `main.py`, which iterates `LLM_PROVIDERS` and skips to the next provider on 429 or 404. Returns 503 only if every configured provider fails.

### Prompt templates (`prompts.md` + `main.py:load_skills()`)

LLM prompt templates are stored in `prompts.md` and parsed at startup by `load_skills()`. Each `## section` becomes a key in `_skills`. The prompt body is extracted with a **greedy** regex between the first and last ` ``` ` fence — this is intentional so that ` ```sql ``` ` references inside the prompt text don't truncate the extraction early.

Placeholders use `.replace("{var}", value)` — **not** f-strings or `.format()`. Adding a new `{variable}` in a prompt requires a matching `.replace()` call at the use site.

`debug_sql` and `summarize_results` are defined in `prompts.md` but not yet wired to any endpoint.

### SQL safety (three layers)

1. `validate_sql()` — regex blocks `INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|ATTACH|DETACH`; query must start with `SELECT`
2. `validate_tables()` — extracts `FROM`/`JOIN` targets via regex, rejects any not present in `sqlite_master`
3. `PRAGMA query_only = ON` — SQLite enforces read-only at the connection level

### Schema introspection (`schema.py`)

- `get_schema_string()` — used in LLM prompts; includes row counts per table to help the model generate realistic queries
- `get_schema_json()` — used by the `GET /schema` endpoint for the UI sidebar; separate from the LLM prompt

### Database

Three tables seeded by `seed.py`: `clients` (300 rows), `symbols` (12 rows), `trades` (2000 rows). Seed is idempotent — skips if `trades` already has rows. Connections are created per-request with `timeout=5`; no connection pool.

## Deployment

`render.yaml` is fully configured. On Render, set `GROQ_API_KEY` (and optionally `OPENROUTER_API_KEY`) as environment secrets. The persistent disk mounts at `/data` — `DB_PATH` must be `/data/deriv.db` in that environment.
