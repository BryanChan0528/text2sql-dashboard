"""Text-to-SQL Dynamic Dashboard — FastAPI backend."""

import os
import re
import json
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

from openai import OpenAI
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from schema import get_connection, get_schema_string, get_schema_json, init_db
from seed import seed

# ---------------------------------------------------------------------------
# App init
# ---------------------------------------------------------------------------

app = FastAPI(title="Text-to-SQL Dashboard")
app.mount("/static", StaticFiles(directory="static"), name="static")

DB_PATH = os.getenv("DB_PATH", "data/deriv.db")
MAX_ROWS = int(os.getenv("MAX_ROWS", "500"))

# Each entry: (api_key_env, base_url, model)
# Tried in order — skips to next on 429 or 404.
LLM_PROVIDERS = [
    # Groq free tier — generous rate limits, fast
    (os.getenv("GROQ_API_KEY", ""),       "https://api.groq.com/openai/v1",  "llama-3.3-70b-versatile"),
    (os.getenv("GROQ_API_KEY", ""),       "https://api.groq.com/openai/v1",  "llama-3.1-8b-instant"),
    # OpenRouter free fallbacks
    (os.getenv("OPENROUTER_API_KEY", ""), "https://openrouter.ai/api/v1",    "meta-llama/llama-3.3-70b-instruct:free"),
    (os.getenv("OPENROUTER_API_KEY", ""), "https://openrouter.ai/api/v1",    "google/gemma-3-27b-it:free"),
    (os.getenv("OPENROUTER_API_KEY", ""), "https://openrouter.ai/api/v1",    "mistralai/mistral-7b-instruct:free"),
]

# Skill prompts loaded once at startup
_skills: dict[str, str] = {}


def load_skills():
    skills_path = Path("skills.md")
    if not skills_path.exists():
        return
    content = skills_path.read_text()
    # Parse sections: ## skill_name
    sections = re.split(r"^## ", content, flags=re.MULTILINE)
    for section in sections[1:]:
        lines = section.strip().splitlines()
        name = lines[0].strip()
        # Extract the prompt between the FIRST and LAST ``` fences in the section.
        # Greedy match so inner ```sql``` references in the prompt text don't truncate early.
        match = re.search(r"```\n(.*)\n```", section, re.DOTALL)
        if match:
            _skills[name] = match.group(1).strip()


@app.on_event("startup")
def startup():
    load_skills()
    seed()


# ---------------------------------------------------------------------------
# Safety
# ---------------------------------------------------------------------------

BLOCKED = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|ATTACH|DETACH)\b",
    re.IGNORECASE,
)


def validate_sql(sql: str):
    stripped = sql.strip()
    if not stripped.upper().startswith("SELECT"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed.")
    if BLOCKED.search(stripped):
        raise HTTPException(status_code=400, detail="Query contains a disallowed keyword.")


def validate_tables(sql: str):
    """Reject SQL that references tables not in the DB (catches LLM hallucinations)."""
    with get_connection() as conn:
        real_tables = {
            row[0].lower()
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    # Extract word tokens after FROM / JOIN keywords
    referenced = re.findall(
        r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)", sql, re.IGNORECASE
    )
    unknown = [t for t in referenced if t.lower() not in real_tables]
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Query references unknown table(s): {', '.join(unknown)}. Available tables: {', '.join(sorted(real_tables))}",
        )


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------

def call_llm(prompt: str, system: str = "") -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    last_err = None
    for api_key, base_url, model in LLM_PROVIDERS:
        if not api_key:
            continue  # skip unconfigured providers
        try:
            c = OpenAI(api_key=api_key, base_url=base_url)
            response = c.chat.completions.create(
                model=model, max_tokens=1024, messages=messages,
            )
            print(f"[LLM] used {model}")
            return response.choices[0].message.content
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "404" in err_str or "rate" in err_str.lower():
                print(f"[LLM] {model} skipped: {err_str[:120]}")
                last_err = e
                continue
            raise

    raise HTTPException(status_code=503, detail=f"All LLM providers are unavailable. Last error: {last_err}")


def extract_sql(text: str) -> str:
    match = re.search(r"```sql\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # fallback: return the whole text if it starts with SELECT
    stripped = text.strip()
    if stripped.upper().startswith("SELECT"):
        return stripped
    raise HTTPException(status_code=500, detail="LLM did not return a SQL query.")


def generate_sql(question: str) -> str:
    schema = get_schema_string()
    template = _skills.get("text_to_sql", "")
    prompt = template.replace("{schema}", schema).replace("{question}", question)
    response = call_llm(prompt)
    return extract_sql(response)


def suggest_chart(columns: list[str], rows: list[list]) -> dict:
    template = _skills.get("chart_type", "")
    if not template or not rows:
        return {"type": "none", "x": "", "y": ""}
    sample = rows[:3]
    prompt = (
        template
        .replace("{columns}", ", ".join(columns))
        .replace("{sample_rows}", json.dumps(sample))
    )
    try:
        raw = call_llm(prompt)
        # extract JSON from response
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return {"type": "none", "x": "", "y": ""}


def explain_query(sql: str) -> str:
    template = _skills.get("explain_sql", "")
    if not template:
        return ""
    prompt = template.replace("{sql}", sql)
    return call_llm(prompt)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    question: str


@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse("static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/schema")
def schema():
    return get_schema_json()


@app.post("/query")
def query(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 1. Generate SQL
    sql = generate_sql(req.question)
    validate_sql(sql)
    validate_tables(sql)

    # 2. Execute
    try:
        with get_connection() as conn:
            conn.execute("PRAGMA query_only = ON")
            cur = conn.execute(sql)
            columns = [d[0] for d in cur.description] if cur.description else []
            rows = [list(r) for r in cur.fetchmany(MAX_ROWS)]
    except sqlite3.Error as e:
        raise HTTPException(status_code=400, detail=f"SQL execution error: {e}")

    # 3. Chart suggestion + explanation (parallel-ish — sequential for simplicity)
    chart = suggest_chart(columns, rows)
    explanation = explain_query(sql)

    return {
        "sql": sql,
        "columns": columns,
        "rows": rows,
        "chart": chart,
        "explanation": explanation,
        "row_count": len(rows),
    }
