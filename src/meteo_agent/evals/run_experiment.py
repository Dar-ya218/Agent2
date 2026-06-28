from __future__ import annotations

import argparse

from langfuse import Evaluation

from meteo_agent.evals.dataset import local_dataset

EXPERIMENT_NAME = "meteo-canonical-questions"


def task(*, item, **_):
    from meteo_agent.graph import run_agent

    return run_agent(item["input"])


def contains_reference(*, input, output, expected_output, metadata=None, **_):
    passed = expected_output.lower() in (output or "").lower()
    return Evaluation(
        name="contains_reference",
        value=passed,
        comment=f"expected the answer to contain {expected_output!r}",
    )


def maybe_langfuse_client():
    try:
        from langfuse import get_client

        client = get_client()
        return client if client.auth_check() else None
    except Exception:
        return None


def run_locally(data: list[dict]) -> None:
    passes = 0
    for item in data:
        output = task(item=item)
        evaluation = contains_reference(
            input=item["input"], output=output, expected_output=item["expected_output"]
        )
        passes += bool(evaluation.value)
        mark = "PASS" if evaluation.value else "FAIL"
        print(f"[{mark}] {item['input']}")
        print(f"       expected~ {item['expected_output']!r}  got: {output!r}")
    print(f"\nscore: {passes}/{len(data)} contain the reference value")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the canonical-question eval.")
    parser.add_argument("--limit", type=int, default=None)
    arguments = parser.parse_args()

    data = local_dataset()
    if arguments.limit is not None:
        data = data[: arguments.limit]

    client = maybe_langfuse_client()
    if client is None:
        print("(Langfuse not configured — running a local eval)\n")
        run_locally(data)
        return

    result = client.run_experiment(
        name=EXPERIMENT_NAME, data=data, task=task, evaluators=[contains_reference]
    )
    client.flush()
    print(result.format())


if __name__ == "__main__":
    main()
