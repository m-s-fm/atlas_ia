# Sécurité

## Modèle de menaces

Atlas tourne sur le poste d'un consultant qui manipule potentiellement des
données clients confidentielles. Les menaces identifiées :

| Menace | Couverte ? | Commentaire |
|---|---|---|
| Fuite de données vers un cloud tiers | ✅ | Tout est local, aucun appel réseau sortant |
| PII stockées en clair dans les logs | ✅ | Masquage avant écriture, previews uniquement |
| Prompt injection via l'entrée utilisateur | ✅ partiellement | Patterns connus détectés, pas les variantes créatives |
| Utilisateur qui bypass la CLI via `ollama run` | ⚠️ | Le Modelfile embarque un persona de défense, mais moins strict que l'applicatif |
| Régurgitation de PII par le modèle | ❌ | Pas de validation de la sortie |
| Poste compromis (accès fichier) | ❌ | La mémoire ChromaDB est en clair sur disque |
| Attaque réseau locale | ❌ | Ollama écoute sur localhost sans authentification |
| DoS par prompts très longs | ✅ | Guardrail de longueur (500 mots par défaut) |
| Injection via contenu web copié-collé | ⚠️ | Patterns courants couverts, pas exhaustif |

Légende : ✅ couvert · ⚠️ partiellement couvert · ❌ non couvert (assumé)

## Décisions de sécurité

### Tout est local

Aucun appel réseau sortant en fonctionnement normal. C'est le point de
départ du projet et la raison pour laquelle la direction a validé son
usage sur des dossiers clients. Toute évolution (fine-tuning, monitoring
externe, évaluation LLM-as-a-judge) doit soit préserver cette propriété,
soit passer par une décision explicite.

### Secrets

Aucun secret n'est requis en local. Pour les extensions futures
(Langfuse, Colab, fine-tuning), les secrets passeront par un fichier
`.env` déjà inscrit dans `.gitignore`.

### Dépendances

Les dépendances sont pinnées dans `pyproject.toml`. Pas de
`requirements.txt` flottant. Audit possible via `pip-audit`.

### Séparation des données

| Chemin | Contenu | Sensibilité |
|---|---|---|
| `data/memory/` | Souvenirs ChromaDB | Haute (contient du contenu utilisateur masqué) |
| `logs/traces.jsonl` | Métriques d'usage | Moyenne (previews 80 caractères) |
| `config/` | Paramétrage | Faible (versionné dans Git) |
| `atlas/`, `tests/`, `scripts/` | Code source | Faible (versionné dans Git) |

`data/` et `logs/` sont dans `.gitignore` et ne doivent jamais être
commités.

## Ce qui serait à faire pour la production

Ce projet est un prototype. Pour un déploiement réel, les points suivants
devraient être traités :

1. Chiffrement au repos de `data/memory/` (filesystem chiffré ou vault)
2. Validation de sortie : vérifier que le modèle ne régurgite pas les
   PII masquées en entrée
3. Rate limiting pour éviter les abus ou les boucles infinies
4. Audit log séparé, append-only, pour les événements de sécurité
5. Authentification sur l'API Ollama si elle est exposée hors localhost
6. Durcissement des regex PII pour les formats internationaux
7. Rotation automatique des traces (taille ou durée)
8. Test de pénétration sur les guardrails (red teaming léger)

## Contacts

En cas d'incident suspecté (fuite de données, comportement anormal du
modèle, tentative d'intrusion), suivre la procédure interne
d'ATLAS Consulting. Ne pas tenter de corriger soi-même en production.