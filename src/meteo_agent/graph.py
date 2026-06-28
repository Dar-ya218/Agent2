from __future__ import annotations

import sys

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from meteo_agent.config import chat_model
from meteo_agent.prompt import SYSTEM_PROMPT
from meteo_agent.tools import RunSqlArgs, get_schema, run_sql

LANGCHAIN_TOOLS = [
    StructuredTool.from_function(
        func=run_sql,
        name="run_sql",
        description="Run a single read-only SQL SELECT query and return the rows.",
        args_schema=RunSqlArgs,
    ),
    StructuredTool.from_function(
        func=get_schema,
        name="get_schema",
        description="Return the database schema: the events table and the daily/monthly/yearly views.",
    ),
]


def build_agent(model=None, tools=None):
    tools = tools or LANGCHAIN_TOOLS
    bound = (model or chat_model()).bind_tools(tools)

    def call_model(state: MessagesState) -> dict:
        return {"messages": [bound.invoke(state["messages"])]}

    graph = StateGraph(MessagesState)
    graph.add_node("model", call_model)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", tools_condition)
    graph.add_edge("tools", "model")
    return graph.compile()


def run_agent(question: str, model=None, config=None) -> str:
    agent = build_agent(model)
    initial = {"messages": [SystemMessage(SYSTEM_PROMPT), HumanMessage(question)]}
    result = agent.invoke(initial, config=config)
    return result["messages"][-1].content


def main() -> None:
    if len(sys.argv) < 2:
        print('usage: meteo-graph "your question"', file=sys.stderr)
        raise SystemExit(1)
    question = " ".join(sys.argv[1:])
    print(run_agent(question))


if __name__ == "__main__":
    main()
