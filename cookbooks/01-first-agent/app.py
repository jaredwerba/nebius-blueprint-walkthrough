"""Recipe 01 — Foundation: first agent on Token Factory."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.token_factory import TokenFactoryClient, TokenFactoryError

SYSTEM = (
    "You are a concise infrastructure assistant. "
    "Answer in short sentences. If you do not know, say you do not know."
)


def run_agent(prompt: str, client: TokenFactoryClient | None = None) -> str:
    client = client or TokenFactoryClient()
    return client.chat(
        [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ]
    )


def main() -> int:
    prompt = "Explain Nebius Token Factory in one paragraph."
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    try:
        print(run_agent(prompt))
        return 0
    except TokenFactoryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print(
            "Fix: set NEBIUS_API_KEY. Live inference did not run in this environment.",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
