# Text-to-SQL Dynamic Dashboard

Ask questions about trading data in plain English — get SQL, tables, and charts instantly.

![Python](https://img.shields.io/badge/Python-3.11-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green) ![SQLite](https://img.shields.io/badge/DB-SQLite-lightgrey) ![Groq](https://img.shields.io/badge/LLM-Groq-orange)

---

## What it does

Type a question like _"Top 5 most traded symbols by volume"_ and the app:

1. Sends your question + database schema to an LLM
2. Generates a safe SQLite `SELECT` query
3. Executes it against the database
4. Returns the results as a table **and** a Chart.js visualisation

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Python + FastAPI |
| LLM | Groq (`llama-3.3-70b-versatile`) with OpenRouter free-tier fallback |
| Database | SQLite (file-based, zero config) |
| Frontend | Single HTML file, Chart.js, vanilla JS |
| Deploy | Render free tier (Web Service + 1 GB persistent disk) |

---

## Getting started

### 1. Clone and install

```bash
git clone https://github.com/<you>/text2sql-dashboard.git
cd text2sql-dashboard
pip install -r requirements.txt
```

### 2. Set up environment

```bash
cp .env.example .env
```

Edit `.env`:

```
GROQ_API_KEY=your_groq_key        # https://console.groq.com/keys (free)
OPENROUTER_API_KEY=your_or_key    # https://openrouter.ai/keys (free, fallback)
```

### 3. Seed the database and run

```bash
python seed.py          # creates data/deriv.db with sample trading data
uvicorn main:app --reload
```

Open [http://localhost:8000](http://localhost:8000)

---

## Sample questions

- Top 5 most traded symbols by volume
- Daily profit by country this year
- How many clients signed up per account type?
- Average profit per trade by asset class
- Total trades and profit by month

---

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Dashboard UI |
| `POST` | `/query` | `{question}` → `{sql, columns, rows, chart, explanation}` |
| `GET` | `/schema` | Database schema (used by sidebar) |
| `GET` | `/health` | Health check for Render |

---

## Safety guardrails

- Only `SELECT` statements are executed
- Blocked keywords: `DROP`, `INSERT`, `UPDATE`, `DELETE`, `ALTER`, `CREATE`
- Table names validated against actual DB before execution
- Max 500 rows returned per query

---

## Deploy to Render

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New Web Service → connect repo
3. Render auto-detects `render.yaml`
4. Add `GROQ_API_KEY` (and optionally `OPENROUTER_API_KEY`) as environment secrets
5. Deploy

---

## AI development workflow

This project is built with **Claude Code** as co-developer:

- [`CLAUDE.md`](CLAUDE.md) — project context loaded into every Claude Code session
- [`skills.md`](skills.md) — reusable LLM prompt templates (`text_to_sql`, `explain_sql`, `chart_type`, `debug_sql`)

New features are added by describing them in plain English to Claude Code — the prompts in `skills.md` and context in `CLAUDE.md` keep responses accurate and on-spec.
