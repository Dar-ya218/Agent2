from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from meteo_agent.tools import get_schema as _get_schema
from meteo_agent.tools import run_sql as _run_sql

mcp = FastMCP("meteobeguda")


@mcp.tool(description="Run a single read-only SQL SELECT query and return the rows.")
def run_sql(query: str) -> str:
    return _run_sql(query)


@mcp.tool(description="Return the database schema: the events table and the daily/monthly/yearly views.")
def get_schema() -> str:
    return _get_schema()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
