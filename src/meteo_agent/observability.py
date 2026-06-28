from __future__ import annotations

import sys
from functools import lru_cache


def langfuse_handler():
    from langfuse.langchain import CallbackHandler

    return CallbackHandler()


@lru_cache
def langfuse_client():
    from langfuse import get_client

    return get_client()


def traced_config() -> dict:
    return {"callbacks": [langfuse_handler()]}


def run_traced(question: str, model=None) -> str:
    from meteo_agent.graph import run_agent

    answer = run_agent(question, model=model, config=traced_config())
    langfuse_client().flush()
    return answer


def main() -> None:
    if len(sys.argv) < 2:
        print('usage: meteo-trace "your question"', file=sys.stderr)
        raise SystemExit(1)
    print(run_traced(" ".join(sys.argv[1:])))


if __name__ == "__main__":
    main()
