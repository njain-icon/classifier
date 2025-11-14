from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml

from classifier.entity_classifier.core.config import CountryConfig
from classifier.log import get_logger

logger = get_logger(__name__)

def _default_entities_dir() -> Path:
    # Prefer env override; else try repo-root/pebblo_config/entities
    override = os.getenv("PEBBLO_CONFIG_DIR")
    # Path of the current file
    logger
    CURRENT_DIR = Path(__file__).resolve().parent.parent
    if override:
        return Path(override)
    # Fallback to CWD-based relative path
    return CURRENT_DIR  / "entities_config" / "entities"


def load_country_config(country: str, base_dir: Optional[str] = None) -> CountryConfig:
    
    base =  _default_entities_dir()
    cfg_path = base / f"{country}.yaml"
    if not cfg_path:
        # Fallback to GLOBAL
        global_candidates = [base / "GLOBAL.yaml", base / "GLOBAL.yml"]
        cfg_path = next((p for p in global_candidates if p.exists()), None)
    if not cfg_path:
        raise FileNotFoundError(f"No config found for country '{country}' in {base}")
    with cfg_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return CountryConfig.parse_obj(data)


