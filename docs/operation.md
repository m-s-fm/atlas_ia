# Runbook opérations

Actions courantes pour maintenir Atlas en service.

## Démarrer

```bash
# 1. Vérifier qu'Ollama tourne
curl http://localhost:11434/api/tags

# 2. Activer le venv
.venv\Scripts\Activate.ps1          # Windows
source .venv/bin/activate           # macOS/Linux

# 3. Lancer
atlas-chat
```

## Arrêter

Dans la CLI : `/quit` ou `Ctrl+C`. Ollama continue de tourner en tâche de
fond, c'est normal. Pour l'arrêter complètement :

| OS | Commande |
|---|---|
| macOS, Windows | Quitter l'application Ollama depuis la barre de menu / systray |
| Linux | `systemctl stop ollama` ou tuer le processus `ollama serve` |

## Purger la mémoire longue

Depuis la CLI :

```bash
atlas-chat
Vous > /forget
Vous > /quit
```

Par suppression directe du dossier :

```bash
rmdir /s /q data\memory             # Windows
rm -rf data/memory                  # macOS/Linux
```

Le dossier sera recréé automatiquement au prochain lancement.

## Purger les traces

```bash
del logs\traces.jsonl               # Windows
rm logs/traces.jsonl                # macOS/Linux
```

Fichier recréé automatiquement au prochain lancement.

## Archiver les traces

Avant purge, garder une copie horodatée :

```bash
# Windows
move logs\traces.jsonl logs\traces-%DATE%.jsonl

# macOS/Linux
mv logs/traces.jsonl logs/traces-$(date +%Y-%m-%d).jsonl
```

## Recréer le modèle Ollama

Si `atlas` est supprimé ou corrompu :

```bash
ollama rm atlas
ollama create atlas -f Modelfile
```

## Changer de modèle de base

Éditer `Modelfile`, remplacer la ligne `FROM llama3.2:3b` par le modèle
voulu (ex : `FROM qwen3:4b`), puis :

```bash
ollama pull qwen3:4b
ollama create atlas -f Modelfile
```

Aucun changement dans le code applicatif.

## Rollback d'une config cassée

La config est versionnée dans Git. En cas de mauvaise modification :

```bash
git checkout -- config/atlas.yaml
```

Ou pour revenir deux commits en arrière :

```bash
git log --oneline config/atlas.yaml
git checkout <commit-sha> -- config/atlas.yaml
```

## Vérifier la santé du système

```bash
# Ollama répond
curl http://localhost:11434/api/tags

# Les tests passent
pytest tests/ -v

# Les métriques sont cohérentes
python scripts/analyze_traces.py
```

Trois signaux que quelque chose dérive :

- Latence médiane > 10 s → modèle trop gros pour la machine, passer sur
  un plus petit (`gemma3:1b`)
- Mémoire qui grandit sans plafond → programmer une purge régulière
- Fichier `traces.jsonl` > 100 Mo → archiver

## Dépannage

### "Connection refused" sur le port 11434

Ollama ne tourne pas.

```bash
ollama serve                        # Linux, dans un terminal dédié
```

Sur macOS/Windows, relancer l'app Ollama depuis les applications.

### La mémoire ne retrouve rien

Vérifier `min_similarity` dans `config/atlas.yaml`. Une valeur de 0.7 est
souvent trop stricte avec le modèle d'embedding par défaut de ChromaDB.
Baisser à 0.3 pour valider que le pipeline marche, puis ajuster.

### Les réponses sont incohérentes

Vérifier `temperature` dans `config/atlas.yaml`. Au-dessus de 1.0 le modèle
devient trop créatif et perd le contexte. Valeur recommandée : 0.3.

### Le modèle `atlas` n'existe pas

```bash
ollama list                         # vérifier
ollama create atlas -f Modelfile    # créer si absent
```

### ChromaDB râle au premier lancement

Supprimer `data/memory/`, relancer. Le dossier sera recréé.

```bash
rmdir /s /q data\memory             # Windows
rm -rf data/memory                  # macOS/Linux
```

### La CLI lit un mauvais fichier de config

`config/atlas.yaml` est résolu relativement au dossier de lancement.
Toujours lancer `atlas-chat` depuis la racine du projet, ou utiliser
le flag explicite :

```bash
atlas-chat --config <chemin-absolu>/config/atlas.yaml
```