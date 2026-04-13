"""DB schema definitions and introspection helper."""

import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "data/deriv.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY,
    country TEXT NOT NULL,
    account_type TEXT NOT NULL CHECK(account_type IN ('real', 'demo')),
    signup_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS symbols (
    symbol TEXT PRIMARY KEY,
    asset_class TEXT NOT NULL,
    market TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    symbol TEXT NOT NULL REFERENCES symbols(symbol),
    side TEXT NOT NULL CHECK(side IN ('buy', 'sell')),
    amount REAL NOT NULL,
    profit REAL NOT NULL,
    duration_seconds INTEGER NOT NULL,
    timestamp TEXT NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)


def get_schema_string() -> str:
    """Return a compact schema description for use in LLM prompts."""
    with get_connection() as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()

        parts = []
        for (table,) in tables:
            cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
            col_defs = ", ".join(
                f"{c['name']} {c['type']}" for c in cols
            )
            # grab row count for context
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            parts.append(f"Table: {table} ({count} rows)\n  Columns: {col_defs}")

        return "\n\n".join(parts)


def get_schema_json() -> list[dict]:
    """Return schema as list of {table, columns} dicts for the UI sidebar."""
    with get_connection() as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()

        result = []
        for (table,) in tables:
            cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
            result.append({
                "table": table,
                "columns": [{"name": c["name"], "type": c["type"]} for c in cols],
            })
        return result
