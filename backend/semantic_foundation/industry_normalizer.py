"""Industry normalizer module."""

from backend.interfaces.normalizer import Normalizer
from backend.semantic_foundation.config_loader import load_yaml_config


class IndustryNormalizer(Normalizer[str, str | None]):
    """Normalizes industry names using configuration-driven aliases."""

    def __init__(self) -> None:
        """Initialize the normalizer by loading industry configurations."""
        config = load_yaml_config("industries.yaml")
        self._mapping: dict[str, str] = {}
        canonical_industries = config.get("canonical_industries", {})

        for canonical, aliases in canonical_industries.items():
            self._mapping[canonical.lower()] = canonical
            for alias in aliases:
                self._mapping[alias.lower()] = canonical

    def normalize(self, data: str) -> str | None:
        """Normalize a raw industry name to its canonical form.

        Args:
            data: Raw industry string.

        Returns:
            The canonical industry, or None if no match is found.
        """
        if not data:
            return None

        cleaned = data.strip().lower()
        return self._mapping.get(cleaned)
