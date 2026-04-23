"""Analyse des traces. 3 métriques minimum (critère S3)."""
import json
from pathlib import Path
import pandas as pd


def main(path: str = "./logs/traces.jsonl") -> None:
    lines = Path(path).read_text(encoding="utf-8").strip().split("\n")
    df = pd.DataFrame([json.loads(l) for l in lines if l])

    if df.empty:
        print("Aucune trace. Lance atlas-chat d'abord.")
        return

    print(f"=== {len(df)} interactions ===\n")

    # 1. Latence
    if "latency_ms" in df:
        lat = df["latency_ms"].dropna()
        print(f"📊 Latence  médiane={lat.median():.0f}ms  p95={lat.quantile(0.95):.0f}ms  max={lat.max():.0f}ms")

    # 2. Tokens + coût estimé GPT-4o
    if "prompt_tokens" in df:
        tin = df["prompt_tokens"].fillna(0).sum()
        tout = df["completion_tokens"].fillna(0).sum()
        # Prix GPT-4o : $2.50/M input, $10/M output
        cost = (tin / 1e6) * 2.50 + (tout / 1e6) * 10.00
        print(f"🔢 Tokens   input={tin:.0f}  output={tout:.0f}")
        print(f"💰 Coût GPT-4o évité : ${cost:.4f}  (on-premise : $0.00)")

    # 3. Guardrails
    if "guardrails" in df:
        triggers = df["guardrails"].explode().dropna()
        if not triggers.empty:
            print(f"\n🛡️  Guardrails déclenchés :")
            print(triggers.value_counts().to_string())


if __name__ == "__main__":
    main()