"""OpenAI-compatible client for Nebius Token Factory."""

from __future__ import annotations

import os
from collections.abc import Iterator

import httpx

DEFAULT_BASE = "https://api.tokenfactory.nebius.com/v1"
DEFAULT_MODEL = "MiniMaxAI/MiniMax-M3"


class TokenFactoryError(RuntimeError):
    pass


class TokenFactoryClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("NEBIUS_API_KEY", "")
        self.base_url = (base_url or os.getenv("NEBIUS_BASE_URL") or DEFAULT_BASE).rstrip("/")
        self.model = model or os.getenv("NEBIUS_MODEL") or DEFAULT_MODEL
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise TokenFactoryError(
                "NEBIUS_API_KEY is empty. Copy .env.example to .env and set the key."
            )
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.2) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        url = f"{self.base_url}/chat/completions"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=self._headers(), json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TokenFactoryError(f"Token Factory request failed: {exc}") from exc
        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise TokenFactoryError(f"Unexpected response shape: {data!r}") from exc

    def chat_stream(self, messages: list[dict[str, str]]) -> Iterator[str]:
        """Yield content deltas. Token Factory uses SSE like OpenAI."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }
        url = f"{self.base_url}/chat/completions"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream("POST", url, headers=self._headers(), json=payload) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line.startswith("data: "):
                            continue
                        chunk = line[6:].strip()
                        if chunk == "[DONE]":
                            break
                        yield chunk
        except httpx.HTTPError as exc:
            raise TokenFactoryError(f"Token Factory stream failed: {exc}") from exc
