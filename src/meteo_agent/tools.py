from __future__ import annotations

import re
import sqlite3

from pydantic import BaseModel, Field

from meteo_agent.config import database_path

MAX_ROWS = 100
FORBIDDEN_KEYWORDS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "attach",
    "detach",
    "truncate",
}


class RunSqlArgs(BaseModel):
    query: str = Field(
        description="A single read-only SQL SELECT statement against the meteobeguda SQLite database."
    )


def read_only_connection() -> sqlite3.Connection:
    return sqlite3.connect(f"file:{database_path()}?mode=ro", uri=True)


def ensure_read_only(query: str) -> None:
    statement = query.strip().rstrip(";").strip()
    lowered = statement.lower()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        raise ValueError("only SELECT/WITH queries are allowed")
    if ";" in statement:
        raise ValueError("only a single statement is allowed")
    forbidden = {token for token in re.findall(r"[a-z_]+", lowered)} & FORBIDDEN_KEYWORDS
    if forbidden:
        raise ValueError(f"forbidden keyword(s): {', '.join(sorted(forbidden))}")


def render_table(columns: list[str], rows: list[tuple]) -> str:
    if not rows:
        return "(no rows)"
    truncated = len(rows) > MAX_ROWS
    visible = rows[:MAX_ROWS]
    lines = [" | ".join(columns)]
    lines += [" | ".join("" if value is None else str(value) for value in row) for row in visible]
    if truncated:
        lines.append(f"... (truncated to {MAX_ROWS} rows)")
    return "\n".join(lines)


def run_sql(query: str) -> str:
    ensure_read_only(query)
    try:
        with read_only_connection() as connection:
            cursor = connection.execute(query)
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchmany(MAX_ROWS + 1)
    except sqlite3.Error as error:
        return f"error: {error}"
    return render_table(columns, rows)


def get_schema() -> str:
    with read_only_connection() as connection:
        columns = connection.execute("PRAGMA table_info(meteobeguda_events)").fetchall()
        views = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'view' ORDER BY name"
        ).fetchall()
        view_columns = {}
        for (view_name,) in views:
            info = connection.execute(f"PRAGMA table_info({view_name})").fetchall()
            view_columns[view_name] = [row[1] for row in info]

    table = "table meteobeguda_events (raw sub-daily readings):\n  " + ", ".join(
        f"{name} {column_type}" for _, name, column_type, *_ in columns
    )
    aggregates = "\n".join(
        f"view {name} (pre-aggregated): " + ", ".join(view_columns[name])
        for name in view_columns
    )
    return f"{table}\n{aggregates}"


OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": "Run a single read-only SQL SELECT query and return the rows.",
            "parameters": RunSqlArgs.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_schema",
            "description": "Return the database schema: the events table and the daily/monthly/yearly views.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

TOOL_FUNCTIONS = {"run_sql": run_sql, "get_schema": get_schema}
