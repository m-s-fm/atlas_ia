"""Sprint 2 · Tâche 1 — Démontrer la saturation de la fenêtre de contexte.

On enchaîne 50 tours avec le modèle et on trace la taille du prompt
envoyé à chaque tour. Objectif : rendre visible pourquoi une mémoire
longue externe est nécessaire.
"""
from __future__ import annotations

from atlas.llm import OllamaClient


def estimate_tokens(text: str) -> int:
    """Approximation grossière du nombre de tokens (cf. brief)."""
    return int(len(text.split()) * 1.3)


def main() -> None:
    client = OllamaClient(model="llama3.2:3b")
    history: list[dict] = [
        {"role": "system", "content": "Tu es un assistant. Réponds en une phrase."}
    ]

    print(f"{'tour':>4} | {'tokens_in':>9} | {'tokens_hist':>11} | {'latency_s':>9}")
    print("-" * 50)

    import time

    for i in range(1, 51):
        user_msg = f"Question {i} : donne-moi un fait aléatoire sur le numéro {i}."
        history.append({"role": "user", "content": user_msg})

        total_text = " ".join(m["content"] for m in history)
        tokens_in = estimate_tokens(total_text)

        t0 = time.perf_counter()
        response = client.chat(history)
        latency = time.perf_counter() - t0

        assistant_msg = response["message"]["content"]
        history.append({"role": "assistant", "content": assistant_msg})

        tokens_hist = estimate_tokens(
            " ".join(m["content"] for m in history)
        )
        print(f"{i:>4} | {tokens_in:>9} | {tokens_hist:>11} | {latency:>9.2f}")


if __name__ == "__main__":
    main()