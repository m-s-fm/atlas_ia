"""Configuration centrale d'Atlas (Sprint 4 N1).

- Lecture YAML via pyyaml
- Validation via Pydantic v2 (erreurs claires si config invalide)
- Interface unique pour tous les modules qui ont besoin de paramètres
"""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import yaml
from pydantic import BaseModel, Field, ValidationError


class ModelConfig(BaseModel):
    name: str = "llama3.2:3b"
    temperature: Annotated[float, Field(ge=0.0, le=2.0)] = 0.3
    top_p: Annotated[float, Field(ge=0.0, le=1.0)] = 0.9
    num_ctx: Annotated[int, Field(ge=512, le=32768)] = 4096
    timeout_seconds: Annotated[float, Field(gt=0)] = 60.0


class PersonaConfig(BaseModel):
    name: str = "Atlas"
    system_prompt: str = (
        "Tu es Atlas, assistant IA interne d'ATLAS Consulting. "
        "Réponds en français, de façon concise et précise."
    )


class MemoryConfig(BaseModel):
    path: str = "./data/memory"
    top_k: Annotated[int, Field(ge=1, le=50)] = 3
    min_similarity: Annotated[float, Field(ge=0.0, le=1.0)] = 0.3


class GuardrailsConfig(BaseModel):
    enabled: bool = True
    config_path: str = "config/guardrails.yaml"


class MonitoringConfig(BaseModel):
    log_path: str = "./logs/traces.jsonl"


class AtlasConfig(BaseModel):
    """Schéma global. Toute clé inconnue est rejetée pour éviter les fautes de frappe."""

    model_config = {"extra": "forbid"}   # « extra fields forbidden » : sécurise la config

    model: ModelConfig = Field(default_factory=ModelConfig)
    persona: PersonaConfig = Field(default_factory=PersonaConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    guardrails: GuardrailsConfig = Field(default_factory=GuardrailsConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)


def load_atlas_config(path: str | Path = "config/atlas.yaml") -> AtlasConfig:
    """Charge et valide la config. Lève des erreurs claires si invalide."""
    p = Path(path)
    if not p.exists():
        # On autorise l'absence du fichier : valeurs par défaut utilisées
        return AtlasConfig()

    with p.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    try:
        return AtlasConfig(**raw)
    except ValidationError as e:
        msg_lines = [f"Config invalide dans {p} :"]
        for err in e.errors():
            loc = " → ".join(str(x) for x in err["loc"])
            msg_lines.append(f"  - {loc} : {err['msg']} (reçu : {err.get('input')!r})")
        raise ValueError("\n".join(msg_lines)) from e