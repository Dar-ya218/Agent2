from __future__ import annotations

import asyncio
import sys

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

from meteo_agent.graph import build_agent
from meteo_agent.prompt import SYSTEM_PROMPT

SERVER_CONFIG = {
    "meteobeguda": {
        "command": "uv",
        "args": ["run", "meteo-mcp"],
        "transport": "stdio",
    }
}


async def load_mcp_tools():
    client = MultiServerMCPClient(SERVER_CONFIG)
    return await client.get_tools()


async def run_agent(question: str, model=None, config=None) -> str:
    tools = await load_mcp_tools()
    agent = build_agent(model=model, tools=tools)
    initial = {"messages": [SystemMessage(SYSTEM_PROMPT), HumanMessage(question)]}
    result = await agent.ainvoke(initial, config=config)
    return result["messages"][-1].content


def main() -> None:
    if len(sys.argv) < 2:
        print('usage: meteo-mcp-agent "your question"', file=sys.stderr)
        raise SystemExit(1)
    question = " ".join(sys.argv[1:])
    print(asyncio.run(run_agent(question)))


if __name__ == "__main__":
    main()
