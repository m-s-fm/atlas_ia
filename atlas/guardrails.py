"""4 guardrails activables via YAML. Retourne (allowed, message_nettoyé, règles_déclenchées, raison)."""
import re
from pathlib import Path
import yaml

# Regex PII
PII = {
    "credit_card": re.compile(r"\b(?:\d[ -]?){13,19}\b"),
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "iban": re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"),
    "ssn_fr": re.compile(r"\b[12]\d{14}\b"),
}


def mask_pii(message: str) -> tuple[str, list[str]]:
    """Retourne (message masqué, types détectés)."""
    found = []
    masked = message
    for kind, pattern in PII.items():
        if pattern.search(masked):
            found.append(kind)
            masked = pattern.sub(f"[{kind.upper()}_REDACTED]", masked)
    return masked, found


def load_config(path: str = "config/guardrails.yaml") -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def check(message: str, config: dict) -> tuple[bool, str, list[str], str]:
    """Applique les 4 règles. Retourne (allowed, message_final, règles, raison)."""
    triggered = []

    # 1. Longueur
    cfg = config.get("length_limit", {})
    if cfg.get("enabled") and len(message.split()) > cfg.get("max_words", 500):
        return False, message, ["length_limit"], f"Message trop long (> {cfg['max_words']} mots)."

    # 2. Prompt injection
    cfg = config.get("prompt_injection", {})
    if cfg.get("enabled"):
        msg_low = message.lower()
        for p in cfg.get("patterns", []):
            if p.lower() in msg_low:
                return False, message, ["prompt_injection"], f"Injection détectée : {p}"

    # 3. Sujets bloqués
    cfg = config.get("blocked_topics", {})
    if cfg.get("enabled"):
        msg_low = message.lower()
        for topic in cfg.get("topics", []):
            if topic.lower() in msg_low:
                return False, message, ["blocked_topics"], f"Sujet non autorisé : {topic}"

    # 4. PII (masquage, pas blocage)
    cfg = config.get("pii_detection", {})
    if cfg.get("enabled"):
        masked, kinds = mask_pii(message)
        if kinds:
            triggered.append("pii_detection")
            return True, masked, triggered, ""

    return True, message, [], ""