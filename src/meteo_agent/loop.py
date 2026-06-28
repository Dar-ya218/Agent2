from __future__ import annotations

import json
import sys

from meteo_agent.config import model_name, openai_client
from meteo_agent.prompt import SYSTEM_PROMPT
from meteo_agent.tools import OPENAI_TOOLS, RunSqlArgs, get_schema, run_sql

MAX_STEPS = 8


def dispatch_tool(name: str, arguments: dict) -> str:
    try:
        if name == "run_sql":
            return run_sql(RunSqlArgs.model_validate(arguments).query)
        if name == "get_schema":
            return get_schema()
        return f"error: unknown tool {name!r}"
    except Exception as error:
        return f"error: {error}"


def assistant_message(message) -> dict:
    payload: dict = {"role": "assistant", "content": message.content or ""}
    if message.tool_calls:
        payload["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.function.name, "arguments": call.function.arguments},
            }
            for call in message.tool_calls
        ]
    return payload


def run_agent(question: str, client=None, model: str | None = None, trace=None) -> str:
    client = client or openai_client()
    model = model or model_name()
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    for _ in range(MAX_STEPS):
        response = client.chat.completions.create(
            model=model, messages=messages, tools=OPENAI_TOOLS, temperature=0
        )
        message = response.choices[0].message
        messages.append(assistant_message(message))

        if not message.tool_calls:
            return message.content or ""

        for call in message.tool_calls:
            arguments = json.loads(call.function.arguments or "{}")
            if trace is not None:
                trace(call.function.name, arguments)
            result = dispatch_tool(call.function.name, arguments)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    return "stopped: reached the maximum number of steps"


def log_tool_call(name: str, arguments: dict) -> None:
    print(f"  -> {name}({json.dumps(arguments, ensure_ascii=False)})", file=sys.stderr)


def main() -> None:
    if len(sys.argv) < 2:
        print('usage: meteo-loop "your question"', file=sys.stderr)
        raise SystemExit(1)
    question = " ".join(sys.argv[1:])
    print(run_agent(question, trace=log_tool_call))


if __name__ == "__main__":
    main()
