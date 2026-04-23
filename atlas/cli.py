"""CLI interactive pour Atlas — avec mémoire longue."""
from __future__ import annotations

import sys
import uuid

import typer

from atlas.llm import OllamaClient
from atlas.memory import LongTermMemory, should_search_memory

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
    stream: bool = typer.Option(True, "--stream/--no-stream"),
    memory_path: str = typer.Option("./data/memory", "--memory-path"),
    top_k: int = typer.Option(3, "--top-k", help="Nombre de souvenirs injectés."),
) -> None:
    """Ouvre une boucle interactive de chat avec mémoire longue."""
    client = OllamaClient(model=model, timeout=timeout)
    memory = LongTermMemory(path=memory_path)
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

        # Recherche conditionnelle en mémoire longue
        souvenirs = []
        if should_search_memory(user_input):
            souvenirs = memory.recall(user_input, top_k=top_k)
            if souvenirs:
                typer.secho(
                    f"[{len(souvenirs)} souvenir(s) pertinent(s) injecté(s)]",
                    fg=typer.colors.MAGENTA,
                )

        # Construction du prompt pour CE tour
        history = [
            {"role": "system", "content": _build_system_with_memory(souvenirs)},
            {"role": "user", "content": user_input},
        ]

        try:
            if stream:
                typer.echo("Atlas > ", nl=False)
                full_response = []
                for chunk in client.chat_stream(history):
                    typer.echo(chunk, nl=False)
                    full_response.append(chunk)
                typer.echo("")
                assistant_msg = "".join(full_response)
            else:
                response = client.chat(history)
                assistant_msg = response["message"]["content"]
                typer.echo(f"Atlas > {assistant_msg}")
        except Exception as e:  # noqa: BLE001
            typer.secho(f"Erreur : {e}", fg=typer.colors.RED, err=True)
            continue

        # Mémorisation de la paire Q/R
        memory.remember(user_input, assistant_msg, session_id=session_id)

    typer.echo("À bientôt.")


if __name__ == "__main__":
    app()