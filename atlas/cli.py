"""CLI interactive pour Atlas — avec mémoire longue, guardrails et monitoring."""
from __future__ import annotations

import sys
import time
import uuid

import typer

from atlas.guardrails import check as check_guardrails, load_config
from atlas.llm import OllamaClient
from atlas.memory import LongTermMemory, should_search_memory
from atlas.monitoring import log_trace

app = typer.Typer(help="Atlas — assistant IA local d'ATLAS Consulting.")

SYSTEM_PROMPT = (
    "Tu es Atlas, assistant IA interne d'ATLAS Consulting. "
    "Réponds en français, de façon concise et précise."
)


def _build_system_with_memory(souvenirs: list[dict]) -> str:
    """Enrichit le system prompt avec les souvenirs pertinents."""
    if not souvenirs:
        return SYSTEM_PROMPT

    rappels = "\n".join(f"- {s['document']}" for s in souvenirs)
    return (
        SYSTEM_PROMPT
        + "\n\n"
        + "Souvenirs de conversations passées pertinents pour cette question :\n"
        + rappels
        + "\n\nUtilise ces souvenirs si pertinent, sinon ignore-les."
    )


@app.command()
def chat(
    model: str = typer.Option("llama3.2:3b", "--model", "-m"),
    timeout: float = typer.Option(60.0, "--timeout", "-t"),
    memory_path: str = typer.Option("./data/memory", "--memory-path"),
    top_k: int = typer.Option(3, "--top-k", help="Nombre de souvenirs injectés."),
    guardrails_path: str = typer.Option(
        "config/guardrails.yaml", "--guardrails-config"
    ),
) -> None:
    """Ouvre une boucle interactive de chat avec mémoire longue."""
    client = OllamaClient(model=model, timeout=timeout)
    memory = LongTermMemory(path=memory_path)
    guardrails_config = load_config(guardrails_path)
    session_id = str(uuid.uuid4())[:8]

    typer.secho(
        f"Atlas prêt (modèle: {model}, session: {session_id}, "
        f"souvenirs en base: {memory.count()}). "
        f"Commandes : /quit, /forget, /memory",
        fg=typer.colors.CYAN,
    )

    while True:
        try:
            user_input = input("\nVous > ").strip()
        except (EOFError, KeyboardInterrupt):
            typer.echo("\nÀ bientôt.")
            sys.exit(0)

        if not user_input:
            continue
        if user_input.lower() in {"/quit", "/exit", "/bye"}:
            break
        if user_input.lower() == "/forget":
            memory.forget_all()
            typer.secho("Mémoire longue effacée.", fg=typer.colors.YELLOW)
            continue
        if user_input.lower() == "/memory":
            typer.echo(f"Souvenirs stockés : {memory.count()}")
            continue

        # --- Guardrails ---
        allowed, safe_message, triggered, reason = check_guardrails(
            user_input, guardrails_config
        )

        if not allowed:
            typer.secho(f"[🛑 bloqué: {reason}]", fg=typer.colors.RED)
            log_trace(
                session_id=session_id,
                model=model,
                user_preview=safe_message[:80],
                blocked=True,
                guardrails=triggered,
                reason=reason,
            )
            continue

        if triggered:
            typer.secho(f"[⚠️  {', '.join(triggered)}]", fg=typer.colors.YELLOW)

        # --- Mémoire ---
        souvenirs = []
        if should_search_memory(safe_message):
            souvenirs = memory.recall(safe_message, top_k=top_k)
            if souvenirs:
                typer.secho(
                    f"[{len(souvenirs)} souvenir(s) injecté(s)]",
                    fg=typer.colors.MAGENTA,
                )

        # --- Construction du prompt ---
        history = [
            {"role": "system", "content": _build_system_with_memory(souvenirs)},
            {"role": "user", "content": safe_message},
        ]

        # --- Appel LLM + trace ---
        t0 = time.perf_counter()
        try:
            response = client.chat(history)
            assistant_msg = response["message"]["content"]
            latency_ms = int((time.perf_counter() - t0) * 1000)

            typer.echo(f"Atlas > {assistant_msg}")

            log_trace(
                session_id=session_id,
                model=model,
                user_preview=safe_message[:80],          # ← CORRIGÉ : safe_message au lieu de user_input
                assistant_preview=assistant_msg[:120],
                latency_ms=latency_ms,
                prompt_tokens=response.get("prompt_eval_count", 0),
                completion_tokens=response.get("eval_count", 0),
                memory_hits=len(souvenirs),
                guardrails=triggered,
            )
        except Exception as e:  # noqa: BLE001
            typer.secho(f"Erreur : {e}", fg=typer.colors.RED, err=True)
            continue

        # --- Mémorisation de la paire Q/R ---
        memory.remember(safe_message, assistant_msg, session_id=session_id)

    typer.echo("À bientôt.")


if __name__ == "__main__":
    app()