"""Client minimal pour l'API Ollama (endpoint /api/chat)."""
from __future__ import annotations

import json
from typing import Any, Iterator

import httpx


class OllamaClient:
    """Wrapper HTTP pur autour de l'API Ollama.

    On évite volontairement la lib `ollama-python` pour garder
    la main sur la couche transport (debug, timeouts, streaming).
    """

    def __init__(
        self,
        model: str = "llama3.2:3b",
        base_url: str = "http://localhost:11434",
        timeout: float = 60.0,
        options: dict[str, Any] | None = None,
    ) -> None:
        """
        options : dict Ollama (temperature, top_p, num_ctx, etc.).
        Voir https://github.com/ollama/ollama/blob/main/docs/modelfile.md#parameter
        """
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.options = options or {}

    def _payload(self, messages: list[dict], stream: bool) -> dict:
        payload = {"model": self.model, "messages": messages, "stream": stream}
        if self.options:
            payload["options"] = self.options
        return payload

    def chat(self, messages: list[dict]) -> dict:
        url = f"{self.base_url}/api/chat"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, json=self._payload(messages, stream=False))
            response.raise_for_status()
            return response.json()

    def chat_stream(self, messages: list[dict]) -> Iterator[str]:
        """Variante streaming. Yield les tokens au fil de l'eau.

        Ollama renvoie du NDJSON : une ligne JSON par chunk.
        """
        url = f"{self.base_url}/api/chat"
        with httpx.Client(timeout=self.timeout) as client:
            with client.stream("POST", url, json=self._payload(messages, stream=True)) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    # Chaque chunk contient message.content (incrémental)
                    # et un flag `done` à True sur le dernier.
                    if "message" in chunk:
                        yield chunk["message"].get("content", "")
                    if chunk.get("done"):
                        break