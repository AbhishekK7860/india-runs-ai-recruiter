"""Title normalizer module."""

from backend.interfaces.normalizer import Normalizer
from backend.semantic_foundation.config_loader import load_yaml_config


class TitleNormalizer(Normalizer[str, str | None]):
    """Normalizes job titles using configuration-driven aliases."""

    def __init__(self) -> None:
        """Initialize the normalizer by loading title configurations."""
        config = load_yaml_config("titles.yaml")
        # Build a reverse lookup mapping: alias (lowercase) -> canonical title
        self._mapping: dict[str, str] = {}
        canonical_titles = config.get("canonical_titles", {})

        for canonical, aliases in canonical_titles.items():
            self._mapping[canonical.lower()] = canonical
            for alias in aliases:
                self._mapping[alias.lower()] = canonical

    def normalize(self, data: str) -> str | None:
        """Normalize a raw job title to its canonical form.

        Args:
            data: Raw job title string.

        Returns:
            The canonical title, or None if no match is found.
        """
        if not data:
            return None

        # Simple exact match (case-insensitive)
        cleaned = data.strip().lower()
        return self._mapping.get(cleaned)
