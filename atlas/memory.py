"""Mémoire longue persistante via ChromaDB.

Stratégie retenue (à défendre devant le formateur) :
- Unité stockée : paire Q/R complète (la réponse seule n'a pas de sens en recherche)
- Déclenchement de la recherche : messages courts (<30 chars) ou contenant des
  mots-clés de rappel ("hier", "avant", "projet", "tu m'avais dit", "rappelle")
- Top-K injecté : 3 souvenirs max, seuil de similarité 0.3
- Résolution des conflits : on trie par timestamp décroissant (plus récent d'abord)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import chromadb

RECALL_KEYWORDS = {
    "hier", "avant", "projet", "rappelle", "souviens", "précédemment",
    "tu m'avais dit", "on avait dit", "la dernière fois",
    "travaille", "client", "bosse", "comment je", "qui je", "age", "ans", "je suis",
}


def should_search_memory(user_message: str) -> bool:
    """Décide si une recherche en mémoire longue est pertinente.

    Heuristique simple :
    - message court (probablement question de suivi)
    - OU contient un mot-clé de rappel
    """
    msg = user_message.lower().strip()
    if len(msg) < 30:
        return True
    return any(kw in msg for kw in RECALL_KEYWORDS)


class LongTermMemory:
    """Mémoire vectorielle persistante.

    Chaque souvenir = une paire (question utilisateur, réponse assistant).
    L'embedding est calculé par ChromaDB (all-MiniLM-L6-v2 par défaut).
    """

    def __init__(self, path: str = "./data/memory", collection_name: str = "conversations") -> None:
        Path(path).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=path)
        self._collection = self._client.get_or_create_collection(name=collection_name)

    def remember(self, user_message: str, assistant_message: str, session_id: str) -> None:
        """Stocke une paire Q/R avec un timestamp."""
        document = f"Q: {user_message}\nR: {assistant_message}"
        self._collection.add(
            ids=[str(uuid.uuid4())],
            documents=[document],
            metadatas=[
                {
                    "session_id": session_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "user_message": user_message,
                    "assistant_message": assistant_message,
                }
            ],
        )

    def recall(
        self,
        query: str,
        top_k: int = 3,
        min_similarity: float = 0.1,
    ) -> list[dict]:
        """Retrouve les souvenirs les plus pertinents.

        Chroma renvoie une "distance" (plus c'est petit, plus c'est proche).
        On convertit en similarité approximative (1 - distance) et on filtre.
        En cas de score équivalent, on privilégie les souvenirs récents.
        """
        if self._collection.count() == 0:
            return []

        results = self._collection.query(
            query_texts=[query],
            n_results=min(top_k, self._collection.count()),
        )

        souvenirs = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            similarity = 1.0 - dist
            if similarity < min_similarity:
                continue
            souvenirs.append(
                {
                    "document": doc,
                    "similarity": similarity,
                    "timestamp": meta.get("timestamp", ""),
                    "session_id": meta.get("session_id", ""),
                }
            )

        # Tri : similarité desc, puis timestamp desc (plus récent d'abord)
        souvenirs.sort(key=lambda s: (s["similarity"], s["timestamp"]), reverse=True)
        return souvenirs

    def forget_all(self) -> None:
        """Vide la mémoire. Utile pour les tests et la démo."""
        # On supprime et on recrée la collection
        name = self._collection.name
        self._client.delete_collection(name)
        self._collection = self._client.get_or_create_collection(name=name)

    def count(self) -> int:
        return self._collection.count()