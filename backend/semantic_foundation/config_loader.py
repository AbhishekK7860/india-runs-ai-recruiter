"""Configuration loader for semantic foundation."""

from pathlib import Path
from typing import Any

import yaml

from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Assuming the project root is two levels up from this file's parent
# i.e., backend/semantic_foundation/config_loader.py -> backend -> project_root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "configs"


def load_yaml_config(filename: str) -> dict[str, Any]:
    """Load a YAML configuration file from the configs directory.

    Args:
        filename: Name of the YAML file (e.g., 'skills.yaml').

    Returns:
        The parsed YAML content as a dictionary. Returns empty dict if file not found.
    """
    filepath = CONFIG_DIR / filename
    if not filepath.exists():
        logger.warning(f"Configuration file not found: {filepath}")
        return {}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data or {}
    except Exception:
        logger.exception(f"Error loading configuration file: {filepath}")
        return {}
