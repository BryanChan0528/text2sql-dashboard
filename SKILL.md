# SKILL.md — Developer Workflows for Claude Code

These are instructions for **Claude Code** (you) to follow when the developer asks to perform common maintenance tasks on this project. Follow each workflow step-by-step.

---

## add-table

**Trigger**: Developer says something like "add a [name] table", "create a new table for [x]", or "I want to track [x] in the DB".

**Goal**: Add a new table end-to-end — schema, seed data, and LLM awareness — so it's immediately queryable through the dashboard.

### Steps

1. **Define the schema** in `schema.py`:
   - Add a `CREATE TABLE IF NOT EXISTS <name> (...)` block inside `SCHEMA_SQL`.
   - Use `INTEGER PRIMARY KEY` for surrogate keys, `TEXT NOT NULL` for enums with a `CHECK(col IN (...))` constraint, `REAL` for decimals, `TEXT` for ISO dates/timestamps.
   - Add a `REFERENCES <parent>(col)` FK if the table joins to an existing one.

2. **Write seed data** in `seed.py`:
   - Add a constant (list or dict) for the static lookup values, or a generation loop for synthetic rows.
   - Use the existing `rng = random.Random(42)` instance so results are deterministic.
   - Add an `INSERT OR IGNORE INTO <name> VALUES (...)` call inside `seed()`, before the `trades` insert if this table is referenced by trades.
   - Update the final `print()` line to include the new row count.

3. **Update the idempotency guard** in `seed.py`:
   - The current guard checks `COUNT(*) FROM trades`. If the new table should also be checked (e.g. it's a top-level table), add a parallel check or note that re-running seed is safe due to `INSERT OR IGNORE`.

4. **Re-seed the database**:
   - Run `python seed.py` and confirm output shows the new table's row count.
   - If the DB already exists with old data, delete `data/deriv.db` first so `init_db()` recreates it cleanly: `rm data/deriv.db && python seed.py`.

5. **Verify the LLM can see the new table**:
   - `get_schema_string()` in `schema.py` is dynamic — it reads `sqlite_master` at runtime, so no changes needed there.
   - Start the dev server (`uvicorn main:app --reload`) and open `http://localhost:8000`.
   - Check the schema sidebar — the new table should appear with its columns.
   - Run a test query in the dashboard, e.g. "how many [new table] rows are there?" and confirm it returns a valid result.

6. **Update prompts if needed**:
   - Open `prompts.md`. If the `text_to_sql` prompt has any hard-coded table hints or examples, update them to include the new table.
   - This is usually not needed because the schema is injected dynamically via `{schema}`.

7. **Update `CLAUDE.md`**:
   - In the "Database" section, update the table count and description to include the new table and its row count.

### Checklist

- [ ] `SCHEMA_SQL` in `schema.py` has the new `CREATE TABLE IF NOT EXISTS` block
- [ ] `seed.py` inserts seed rows for the new table
- [ ] `rm data/deriv.db && python seed.py` runs cleanly and prints the new table's count
- [ ] Schema sidebar in the UI shows the new table
- [ ] A natural-language query about the new table returns correct SQL and results
- [ ] `CLAUDE.md` "Database" section updated
