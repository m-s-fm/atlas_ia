# Installation

Guide pour relancer Atlas sur une machine vierge en environ 15 minutes.

## Prérequis

- Windows 10+, macOS 12+ ou Linux
- Python 3.10 ou supérieur
- Git
- 8 Go de RAM minimum (16 Go recommandés)
- Environ 3 Go d'espace disque pour le modèle

## 1. Installer Ollama

Télécharger depuis https://ollama.com/download et installer.

Vérifier que le service tourne :

```bashcurl http://localhost:11434/api/tags

Doit répondre avec un JSON, même vide : `{"models":[]}`.

## 2. Télécharger un modèle

```bashollama pull llama3.2:3b

Comptez 5 à 15 min selon la connexion (environ 2 Go).

Vérifier :

```bashollama list

## 3. Cloner le projet

```bashgit clone https://github.com/m-s-fm/atlas_ia.git
cd atlas_ia

## 4. Environnement Python

Windows PowerShell :

```powershellpython -m venv .venv
.venv\Scripts\Activate.ps1

macOS / Linux :

```bashpython -m venv .venv
source .venv/bin/activate

Le prompt doit maintenant commencer par `(.venv)`.

## 5. Installer les dépendances

```bashpip install -e .

## 6. Créer le modèle dérivé Atlas

```bashollama create atlas -f Modelfile

Vérifier :

```bashollama list

Vous devez voir `atlas` à côté de `llama3.2:3b`.

## 7. Lancer

```bashatlas-chat

La bannière doit afficher :Atlas prêt — modèle: atlas, T=0.3, top_k mémoire=5, session: ..., souvenirs: 0

Commandes disponibles :

- `/quit` — sortir
- `/memory` — voir combien de souvenirs sont stockés
- `/forget` — purger la mémoire
- `/config` — afficher la config active

## Vérification

```bashpytest tests/ -v

Doit afficher tous les tests verts.

## En cas de problème

Voir [operations.md](operations.md) section "Dépannage".