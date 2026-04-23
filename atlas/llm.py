"""Client minimal pour l'API Ollama (endpoint /api/chat)."""
from __future__ import annotations

import json
from typing import Iterator

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
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def chat(self, messages: list[dict]) -> dict:
        """Appel bloquant. Retourne la réponse JSON complète d'Ollama.

        `messages` suit le format OpenAI : [{"role": "user"|"assistant"|"system",
                                              "content": "..."}]
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    def chat_stream(self, messages: list[dict]) -> Iterator[str]:
        """Variante streaming. Yield les tokens au fil de l'eau.

        Ollama renvoie du NDJSON : une ligne JSON par chunk.
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }
        with httpx.Client(timeout=self.timeout) as client:
            with client.stream("POST", url, json=payload) as response:
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