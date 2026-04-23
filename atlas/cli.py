"""CLI interactive pour Atlas."""
from __future__ import annotations

import sys

import typer

from atlas.llm import OllamaClient

app = typer.Typer(help="Atlas — assistant IA local d'ATLAS Consulting.")

SYSTEM_PROMPT = (
    "Tu es Atlas, assistant IA interne d'ATLAS Consulting. "
    "Réponds en français, de façon concise et précise."
)


@app.command()
def chat(
    model: str = typer.Option("llama3.2:3b", "--model", "-m", help="Modèle Ollama à utiliser."),
    timeout: float = typer.Option(60.0, "--timeout", "-t", help="Timeout HTTP (secondes)."),
    stream: bool = typer.Option(True, "--stream/--no-stream", help="Afficher la réponse au fil de l'eau."),
) -> None:
    """Ouvre une boucle interactive de chat avec le modèle local."""
    client = OllamaClient(model=model, timeout=timeout)
    history: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    typer.secho(f"Atlas prêt (modèle: {model}). Tape /quit pour sortir.", fg=typer.colors.CYAN)

    while True:
        try:
            user_input = input("\nVous > ").strip()
        except (EOFError, KeyboardInterrupt):
            typer.echo("\nÀ bientôt.")
            sys.exit(0)

        if not user_input:
            continue
        if user_input.lower() in {"/quit", "/exit", "/bye"}:
            typer.echo("À bientôt.")
            break

        history.append({"role": "user", "content": user_input})

        try:
            if stream:
                typer.echo("Atlas > ", nl=False)
                full_response = []
                for chunk in client.chat_stream(history):
                    typer.echo(chunk, nl=False)
                    full_response.append(chunk)
                typer.echo("")  # newline final
                assistant_msg = "".join(full_response)
            else:
                response = client.chat(history)
                assistant_msg = response["message"]["content"]
                typer.echo(f"Atlas > {assistant_msg}")
        except Exception as e:  # noqa: BLE001
            typer.secho(f"Erreur : {e}", fg=typer.colors.RED, err=True)
            history.pop()  # on retire le message user qui n'a pas eu de réponse
            continue

        history.append({"role": "assistant", "content": assistant_msg})


if __name__ == "__main__":
    app()