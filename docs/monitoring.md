# Monitoring

## Principe

Chaque interaction avec le LLM produit une ligne JSON dans
`logs/traces.jsonl`. Le format JSONL permet d'analyser facilement avec pandas
sans dépendance à un service externe.

Ce choix a été fait contre Langfuse pour garder zéro infrastructure. Une
migration vers Langfuse reste possible sans refonte grâce à l'abstraction
de la fonction `log_trace()`.

## Format des traces

Chaque ligne du fichier est un objet JSON indépendant.

| Champ | Type | Description |
|---|---|---|
| `timestamp` | ISO 8601 UTC | Date et heure de l'interaction |
| `session_id` | str | Identifiant de session (8 caractères) |
| `model` | str | Nom du modèle utilisé |
| `user_preview` | str | Message utilisateur tronqué à 80 caractères, PII déjà masquées |
| `assistant_preview` | str | Réponse du modèle tronquée à 120 caractères |
| `latency_ms` | int | Durée de l'appel LLM en millisecondes |
| `prompt_tokens` | int | Tokens en entrée (champ `prompt_eval_count` d'Ollama) |
| `completion_tokens` | int | Tokens en sortie (champ `eval_count`) |
| `memory_hits` | int | Nombre de souvenirs injectés dans le prompt |
| `guardrails` | list[str] | Règles déclenchées (ex : `["pii_detection"]`) |
| `blocked` | bool | True si un guardrail a refusé l'interaction |
| `reason` | str | Raison du blocage si applicable |

Exemple de ligne :

```json
{"timestamp": "2026-04-23T14:22:01+00:00", "session_id": "a3f2e1b9",
 "model": "atlas", "user_preview": "Ma CB est [CREDIT_CARD_REDACTED]",
 "latency_ms": 4520, "prompt_tokens": 87, "completion_tokens": 42,
 "memory_hits": 2, "guardrails": ["pii_detection"]}
```

Important : `user_preview` est **toujours** produit à partir du message
après masquage PII. Les numéros de CB, emails, IBAN et numéros de sécu
n'apparaissent jamais en clair dans les logs.

## Analyse

Le script `scripts/analyze_traces.py` produit 5 métriques agrégées :

1. Latence médiane, moyenne, p95, maximum
2. Top 5 des interactions les plus lentes
3. Sessions ayant utilisé la mémoire (combien, lesquelles)
4. Tokens consommés par jour (input / output)
5. Coût contrefactuel si on était passé par GPT-4o

Lancement :

```bash
python scripts/analyze_traces.py
```

Option : passer un autre fichier en argument :

```bash
python scripts/analyze_traces.py logs/old_traces.jsonl
```

