# Gouvernance

## Guardrails en entrée

Quatre règles tournent à chaque message utilisateur, dans cet ordre :

1. **Longueur** — refuse les messages au-delà d'un seuil (défaut 500 mots)
2. **Prompt injection** — refuse les patterns connus (`"ignore previous instructions"`, `"tu es maintenant"`, etc.)
3. **Sujets bloqués** — refuse les thèmes configurés (politique, religion, armes)
4. **Détection PII** — masque (ne bloque pas) les numéros de CB, emails, IBAN, numéros de sécu

Les trois premières **refusent** l'interaction : aucun appel au LLM n'est fait.
La quatrième **masque** le contenu sensible par un placeholder
(`[CREDIT_CARD_REDACTED]`, `[EMAIL_REDACTED]`, etc.) avant d'envoyer la
requête au modèle. L'utilisateur voit sa question traitée, mais le modèle
ne voit jamais les PII.

Toutes les règles sont activables/désactivables individuellement via
`config/guardrails.yaml`.

## Politique RGPD

### Qu'est-ce qui est stocké ?

| Donnée | Où | Durée |
|---|---|---|
| Message utilisateur brut | Nulle part | Jamais stocké en clair |
| Preview tronqué à 80 caractères (après masquage PII) | `logs/traces.jsonl` | Jusqu'à purge manuelle |
| Paire question/réponse (après masquage PII) | `data/memory/` (ChromaDB) | Jusqu'à `/forget` ou purge |
| Hash complet du message | Non implémenté | — |

Le `user_preview` dans les logs est toujours produit à partir du message
**après passage dans les guardrails**. Si l'utilisateur tape un numéro de CB,
seul `[CREDIT_CARD_REDACTED]` apparaît dans les logs et en mémoire.

### Droit à l'oubli

Trois actions selon le niveau d'effacement voulu :

| Action | Effacement |
|---|---|
| `/forget` dans la CLI | Mémoire longue (ChromaDB) vidée |
| `del logs\traces.jsonl` | Traces d'usage purgées |
| `rmdir /s /q data` et `del logs\traces.jsonl` | Tout effacé |

La commande `/forget` ne purge pas les traces : c'est un choix délibéré
pour conserver les métriques d'usage anonymisées. Une purge totale
nécessite une action manuelle.

### Pas de télémétrie externe

Aucune donnée ne sort de la machine. Pas de tracker analytics, pas d'envoi
vers un SaaS, pas de télémétrie vers un fournisseur de modèle. C'est le
principe fondateur du projet et la raison pour laquelle la direction a
validé son usage sur des dossiers clients.

## Limites connues

- La détection PII repose sur des regex. Un utilisateur motivé peut
  contourner le masquage (par exemple en espaçant les chiffres d'une CB
  de façon non standard, ou en utilisant des formats internationaux rares).
- La validation de sortie n'est pas implémentée : en théorie, le modèle
  pourrait régurgiter des PII apprises ailleurs. À durcir pour un usage
  production.
- Aucun chiffrement sur `data/memory/` ni sur `logs/`. Si la machine est
  compromise, ces contenus sont lisibles.
- La liste des sujets bloqués est limitée. Un sujet rédigé autrement
  (synonyme, paraphrase) passe à travers.

## Rôles et responsabilités

| Rôle | Responsabilité |
|---|---|
| Consultant utilisateur | Respecte les règles de confidentialité client, utilise `/forget` en fin de mission |
| Admin poste | Ne modifie pas `config/guardrails.yaml` sans validation |
| Dev projet | Ajoute des règles métier si un nouveau risque est identifié |
| Direction | Valide l'évolution du modèle de menaces |