"""Agentic cost benchmark — compare measured tokens and fake price, not list price.

Live Token Factory is optional. Offline tests use recorded token counts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


# Approximate Token Factory list prices USD / 1M tokens (input, output).
PRICES = {
    "MiniMaxAI/MiniMax-M3": (0.30, 1.20),
    "meta-llama/Llama-3.3-70B-Instruct": (0.13, 0.40),
    "zai-org/GLM-5.2": (1.40, 4.40),
}


@dataclass
class Run:
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    correct: bool
    usd: float


def estimate_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    inp, out = PRICES.get(model, (1.0, 1.0))
    return (prompt_tokens * inp + completion_tokens * out) / 1_000_000


def score_correctness(answer: str, expected: str) -> bool:
    return expected.lower() in answer.lower()


def benchmark(task: str, expected: str, recorded: list[dict]) -> dict:
    runs = []
    for row in recorded:
        usd = estimate_usd(row["model"], row["prompt_tokens"], row["completion_tokens"])
        runs.append(
            Run(
                row["model"],
                row["prompt_tokens"],
                row["completion_tokens"],
                row["latency_ms"],
                score_correctness(row["answer"], expected),
                round(usd, 6),
            )
        )
    cheapest_correct = min(
        (r for r in runs if r.correct),
        key=lambda r: r.usd,
        default=None,
    )
    return {
        "task": task,
        "runs": [asdict(r) for r in runs],
        "cheapest_correct": cheapest_correct.model if cheapest_correct else None,
    }


FIXTURE = [
    {
        "model": "MiniMaxAI/MiniMax-M3",
        "prompt_tokens": 120,
        "completion_tokens": 80,
        "latency_ms": 900,
        "answer": "Token Factory is an OpenAI-compatible inference API for open models.",
    },
    {
        "model": "meta-llama/Llama-3.3-70B-Instruct",
        "prompt_tokens": 120,
        "completion_tokens": 60,
        "latency_ms": 700,
        "answer": "Nebius Token Factory serves open models.",
    },
    {
        "model": "zai-org/GLM-5.2",
        "prompt_tokens": 120,
        "completion_tokens": 90,
        "latency_ms": 1100,
        "answer": "I do not know.",
    },
]


if __name__ == "__main__":
    print(
        benchmark(
            "Name Token Factory in one sentence",
            "Token Factory",
            FIXTURE,
        )
    )
