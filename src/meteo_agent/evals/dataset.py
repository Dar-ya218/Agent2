from __future__ import annotations

from dataclasses import dataclass

from meteo_agent.tools import read_only_connection


@dataclass(frozen=True)
class EvalCase:
    question: str
    reference_sql: str


CASES = [
    EvalCase(
        "What was the hottest day on record, by highest daily maximum temperature? Give the date as YYYY-MM-DD.",
        "SELECT date FROM meteobeguda_daily ORDER BY temperature_max DESC LIMIT 1",
    ),
    EvalCase(
        "In which year did a single calendar month see the most total rainfall? Give the year.",
        "SELECT substr(month, 1, 4) FROM meteobeguda_monthly ORDER BY rain_total DESC LIMIT 1",
    ),
    EvalCase(
        "How many days in 2023 had a maximum temperature above 35 degrees Celsius?",
        "SELECT COUNT(*) FROM meteobeguda_daily WHERE temperature_max > 35 AND date LIKE '2023%'",
    ),
    EvalCase(
        "What is the earliest year present in the dataset?",
        "SELECT MIN(year) FROM meteobeguda_yearly",
    ),
    EvalCase(
        "What was the average temperature in 2003, to one decimal place?",
        "SELECT round(temperature_avg, 1) FROM meteobeguda_yearly WHERE year = '2003'",
    ),
]


def ground_truth(case: EvalCase) -> str:
    with read_only_connection() as connection:
        value = connection.execute(case.reference_sql).fetchone()[0]
    return str(value)


def local_dataset() -> list[dict]:
    return [
        {
            "input": case.question,
            "expected_output": ground_truth(case),
            "metadata": {"reference_sql": case.reference_sql},
        }
        for case in CASES
    ]
