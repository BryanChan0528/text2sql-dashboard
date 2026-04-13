# skills.md — Reusable Claude Skill Prompts

These are structured prompts used by `main.py` when calling the Claude API. Each skill has a **name**, **when to use it**, and the **prompt template** (use `{variable}` placeholders).

---

## text_to_sql

**When**: Convert a natural language question into a SQL SELECT query.

**Prompt**:
```
You are an expert SQL assistant for a trading analytics platform.

Given the database schema and a user question, generate a single valid SQLite SELECT query.

Rules:
- Return ONLY the SQL query inside a ```sql ... ``` code block, nothing else.
- CRITICAL: Only reference tables and columns that exist in the schema below. Do NOT invent or assume any other table or column names.
- Use only SELECT statements. Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or TRUNCATE.
- Use proper SQLite syntax (strftime for dates, CAST for type conversions).
- Limit results to 100 rows unless the user asks for more.
- If the question is ambiguous, make a reasonable assumption using ONLY the available tables.
- Column aliases should be human-readable (e.g., "Total Profit" not "sum_profit").

Database schema:
{schema}

User question: {question}
```

---

## explain_sql

**When**: Explain a generated SQL query in plain English for the user.

**Prompt**:
```
Explain the following SQL query in 1-2 plain English sentences. 
Be concise. Focus on what the query returns, not how SQL works.

SQL:
{sql}
```

---

## chart_type

**When**: Suggest the best Chart.js chart type for a result set.

**Prompt**:
```
Given the column names and a sample of rows from a query result, suggest the best chart type.

Reply with a JSON object only, no explanation:
{"type": "<bar|line|pie|doughnut|scatter|none>", "x": "<column_name>", "y": "<column_name>"}

- Use "bar" for comparisons across categories (e.g. profit by symbol)
- Use "line" for time series (e.g. daily trades over time)
- Use "pie" or "doughnut" for proportions with <8 categories
- Use "scatter" for two numeric dimensions
- Use "none" if a chart doesn't make sense (e.g. raw text data)

Columns: {columns}
Sample rows (first 3): {sample_rows}
```

---

## debug_sql

**When**: Fix a broken SQL query given the error message.

**Prompt**:
```
The following SQLite query failed with an error. Fix it.

Return ONLY the corrected SQL query inside a ```sql ... ``` code block.

Database schema:
{schema}

Failed query:
{sql}

Error:
{error}
```

---

## summarize_results

**When**: Generate a 1-sentence insight from query results for display in the dashboard.

**Prompt**:
```
Given this data from a trading analytics query, write one sentence summarizing the key insight.
Be specific with numbers. Keep it under 20 words.

Question asked: {question}
Columns: {columns}
Top rows: {sample_rows}
```
