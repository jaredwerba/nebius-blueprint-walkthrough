"""Recipe 08 — Guardrails: input and output filters."""

from __future__ import annotations

import re

BLOCKED_INPUT = re.compile(r"(ignore previous|exfiltrate|bomb making)", re.I)
PII = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


class GuardrailRejected(ValueError):
    pass


def check_input(text: str) -> str:
    if BLOCKED_INPUT.search(text):
        raise GuardrailRejected("Input failed policy.")
    return text


def check_output(text: str) -> str:
    return PII.sub("[REDACTED-SSN]", text)


def guarded_generate(prompt: str, generator) -> str:
    check_input(prompt)
    raw = generator(prompt)
    return check_output(raw)


if __name__ == "__main__":
    print(guarded_generate("hello", lambda p: f"ok:{p}"))
