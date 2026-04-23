"""CLI interactive pour Atlas — config YAML centralisée (S4)."""
from __future__ import annotations

import sys
import time
import uuid

import typer

from atlas.config import load_atlas_config
from atlas.guardrails import check as check_guardrails, load_config as load_guardrails_config
from atlas.llm import OllamaClient
from atlas.memory import LongTermMemory, should_search_memory
from atlas.monitoring import log_trace

app = typer.Typer(help="Atlas — assistant IA local d'ATLAS Consulting.")


def _build_system_with_memory(system_prompt: str, souvenirs: list[dict]) -> str:
    if not souvenirs:
        return system_prompt
    rappels = "\n".join(f"- {s['document']}" for s in souvenirs)
    return (
        system_prompt
        + "\n\n"
        + "Souvenirs de conversations passées pertinents pour cette question :\n"
        + rappels
        + "\n\nUtilise ces souvenirs si pertinent, sinon ignore-les."
    )


@app.command()
def chat(
    config_path: str = typer.Option("config/atlas.yaml", "--config", "-c"),
    # Overrides CLI ponctuels (pratiques pour la démo)
    model: str | None = typer.Option(None, "--model", "-m"),
    temperature: float | None = typer.Option(None, "--temperature"),
) -> None:
    """Ouvre une boucle de chat en lisant la config YAML."""
    try:
        cfg = load_atlas_config(config_path)
    except ValueError as e:
        typer.secho(str(e), fg=typer.colors.RED, err=True)
        sys.exit(2)

    # Overrides CLI (les flags gagnent sur le YAML)
    if model is not None:
        cfg.model.name = model
    if temperature is not None:
        cfg.model.temperature = temperature

    client = OllamaClient(
        model=cfg.model.name,
        timeout=cfg.model.timeout_seconds,
        options={
            "temperature": cfg.model.temperature,
            "top_p": cfg.model.top_p,
            "num_ctx": cfg.model.num_ctx,
        },
    )
    memory = LongTermMemory(path=cfg.memory.path)
    guardrails_config = (
        load_guardrails_config(cfg.guardrails.config_path) if cfg.guardrails.enabled else {}
    )
    session_id = str(uuid.uuid4())[:8]

    typer.secho(
        f"{cfg.persona.name} prêt — modèle: {cfg.model.name}, "
        f"T={cfg.model.temperature}, top_k mémoire={cfg.memory.top_k}, "
        f"session: {session_id}, souvenirs: {memory.count()}",
        fg=typer.colors.CYAN,
    )
    typer.secho("Commandes : /quit, /forget, /memory, /config", fg=typer.colors.BRIGHT_BLACK)

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
        if user_input.lower() == "/config":
            typer.echo(cfg.model_dump_json(indent=2))
            continue

        # --- Guardrails ---
        if cfg.guardrails.enabled:
            allowed, safe_message, triggered, reason = check_guardrails(user_input, guardrails_config)
        else:
            allowed, safe_message, triggered, reason = True, user_input, [], ""

        if not allowed:
            typer.secho(f"[🛑 bloqué: {reason}]", fg=typer.colors.RED)
            log_trace(
                cfg.monitoring.log_path,
                session_id=session_id, model=cfg.model.name,
                user_preview=safe_message[:80],
                blocked=True, guardrails=triggered, reason=reason,
            )
            continue

        if triggered:
            typer.secho(f"[⚠️  {', '.join(triggered)}]", fg=typer.colors.YELLOW)

        # --- Mémoire ---
        souvenirs = []
        if should_search_memory(safe_message):
            souvenirs = memory.recall(
                safe_message,
                top_k=cfg.memory.top_k,
                min_similarity=cfg.memory.min_similarity,
            )
            if souvenirs:
                typer.secho(
                    f"[{len(souvenirs)} souvenir(s) injecté(s)]",
                    fg=typer.colors.MAGENTA,
                )

        # --- Construction du prompt ---
        history = [
            {"role": "system", "content": _build_system_with_memory(cfg.persona.system_prompt, souvenirs)},
            {"role": "user", "content": safe_message},
        ]

        # --- Appel LLM + trace ---
        t0 = time.perf_counter()
        try:
            response = client.chat(history)
            assistant_msg = response["message"]["content"]
            latency_ms = int((time.perf_counter() - t0) * 1000)
            typer.echo(f"{cfg.persona.name} > {assistant_msg}")

            log_trace(
                cfg.monitoring.log_path,
                session_id=session_id, model=cfg.model.name,
                user_preview=safe_message[:80],
                assistant_preview=assistant_msg[:120],
                latency_ms=latency_ms,
                prompt_tokens=response.get("prompt_eval_count", 0),
                completion_tokens=response.get("eval_count", 0),
                memory_hits=len(souvenirs),
                guardrails=triggered,
                temperature=cfg.model.temperature,
            )
        except Exception as e:  # noqa: BLE001
            typer.secho(f"Erreur : {e}", fg=typer.colors.RED, err=True)
            continue

        # --- Mémorisation de la paire Q/R ---
        memory.remember(safe_message, assistant_msg, session_id=session_id)

    typer.echo("À bientôt.")


if __name__ == "__main__":
    app()