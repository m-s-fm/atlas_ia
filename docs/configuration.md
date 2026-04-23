# Configuration

Le comportement d'Atlas est piloté par deux fichiers YAML. Aucun paramètre
n'est codé en dur dans l'applicatif.

- `config/atlas.yaml` : config principale (modèle, persona, mémoire, monitoring)
- `config/guardrails.yaml` : règles de filtrage en entrée

Le premier est validé par un schéma Pydantic. Toute valeur hors borne ou
toute clé inconnue produit une erreur explicite au démarrage.

## config/atlas.yaml

Exemple commenté :

```yaml
model:
  name: "atlas"            # nom du modèle Ollama (notre dérivé du Modelfile)
  temperature: 0.3         # 0 = déterministe, 1 = créatif, 2 = chaotique
  top_p: 0.9               # nucleus sampling
  num_ctx: 4096            # taille de la fenêtre de contexte en tokens
  timeout_seconds: 60      # timeout HTTP des requêtes Ollama

persona:
  name: "Atlas"            # affiché dans la bannière et le prompt
  system_prompt: |
    Tu es Atlas, assistant IA interne d'ATLAS Consulting.
    Tu réponds en français de façon concise et précise.

memory:
  path: "./data/memory"    # où ChromaDB persiste les souvenirs
  top_k: 5                 # nombre de souvenirs injectés par question
  min_similarity: 0.3      # seuil de pertinence (0 à 1)

guardrails:
  enabled: true
  config_path: "config/guardrails.yaml"

monitoring:
  log_path: "./logs/traces.jsonl"
```

### Ce que pilote chaque clé

| Section | Clé | Effet |
|---|---|---|
| model | name | Modèle Ollama à appeler. Doit exister dans `ollama list`. |
| model | temperature | Plus c'est haut, plus les réponses sont variées. Au-delà de 1, le modèle a tendance à perdre le fil. |
| model | top_p | Probabilité cumulée pour le nucleus sampling. Laisser à 0.9 dans la majorité des cas. |
| model | num_ctx | Fenêtre de contexte. Plus c'est grand, plus on tient d'historique, mais plus c'est lent. |
| persona | name | Nom affiché dans la CLI (`Atlas > ...`). |
| persona | system_prompt | Instructions système envoyées à chaque requête. |
| memory | top_k | Nombre maximum de souvenirs injectés dans le prompt. |
| memory | min_similarity | En dessous de ce seuil, un souvenir est jugé non pertinent et rejeté. Empirique, autour de 0.3 fonctionne bien sur le modèle d'embedding par défaut. |
| guardrails | enabled | Désactivable pour les tests ou le développement. |
| monitoring | log_path | Fichier JSONL de traces (voir [monitoring.md](monitoring.md)). |

### Validation

| Cas | Erreur levée |
|---|---|
| `temperature: 5` | Input should be less than or equal to 2 |
| `top_k: -1` | Input should be greater than or equal to 1 |
| `modl: {...}` (typo) | Extra inputs are not permitted |
| Fichier absent | Valeurs par défaut utilisées (pas d'erreur) |

## config/guardrails.yaml

Règles activables indépendamment. Exemple :

```yaml
pii_detection:
  enabled: true            # masque CB, email, IBAN, numéro de sécu

blocked_topics:
  enabled: true
  topics: [politique, religion, armes]

length_limit:
  enabled: true
  max_words: 500

prompt_injection:
  enabled: true
  patterns:
    - "ignore previous instructions"
    - "tu es maintenant"
    - "<|system|>"
```


## Overrides en ligne de commande

Certains paramètres sont surchargeables au lancement sans toucher au YAML :

```bash
atlas-chat --model atlas --temperature 0.7
atlas-chat --config autre/config.yaml
```

Les flags CLI gagnent toujours sur le YAML.

## Tester un changement

La méthode la plus rapide pour vérifier qu'un changement est bien pris en
compte :

```bash
atlas-chat
Vous > /config
```

`/config` affiche la config active telle que Pydantic l'a chargée.