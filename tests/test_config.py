"""Tests de la configuration YAML + validation Pydantic."""
import pytest
import yaml

from atlas.config import AtlasConfig, load_atlas_config


def test_defaults_loaded_when_file_missing(tmp_path):
    """Si le fichier n'existe pas, on a une config par défaut valide."""
    cfg = load_atlas_config(tmp_path / "nope.yaml")
    assert cfg.model.name == "llama3.2:3b"
    assert cfg.persona.name == "Atlas"


def test_yaml_loaded_correctly(tmp_path):
    path = tmp_path / "atlas.yaml"
    path.write_text(yaml.dump({
        "model": {"name": "gemma3:1b", "temperature": 0.7},
        "persona": {"name": "Artemis"},
        "memory": {"top_k": 10, "min_similarity": 0.5},
    }))
    cfg = load_atlas_config(path)
    assert cfg.model.name == "gemma3:1b"
    assert cfg.model.temperature == 0.7
    assert cfg.persona.name == "Artemis"
    assert cfg.memory.top_k == 10


def test_invalid_temperature_raises(tmp_path):
    """Temperature hors [0, 2] => erreur claire."""
    path = tmp_path / "atlas.yaml"
    path.write_text(yaml.dump({"model": {"temperature": 5.0}}))
    with pytest.raises(ValueError, match="temperature"):
        load_atlas_config(path)


def test_unknown_section_raises(tmp_path):
    """Faute de frappe (p. ex. 'modl' au lieu de 'model') = erreur immédiate."""
    path = tmp_path / "atlas.yaml"
    path.write_text(yaml.dump({"modl": {"name": "test"}}))
    with pytest.raises(ValueError):
        load_atlas_config(path)


def test_invalid_top_k_raises(tmp_path):
    path = tmp_path / "atlas.yaml"
    path.write_text(yaml.dump({"memory": {"top_k": -1}}))
    with pytest.raises(ValueError):
        load_atlas_config(path)