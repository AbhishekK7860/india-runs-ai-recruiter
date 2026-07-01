"""Skill taxonomy module."""

from backend.interfaces.normalizer import Normalizer
from backend.semantic_foundation.aliases import SkillAliasResolver
from backend.semantic_foundation.config_loader import load_yaml_config


class SkillNormalizer(Normalizer[list[str], list[str]]):
    """Normalizes a list of skills using canonical taxonomy and alias resolution."""

    def __init__(self) -> None:
        """Initialize the skill normalizer."""
        self.alias_resolver = SkillAliasResolver()

        config = load_yaml_config("skills.yaml")
        self._canonical_skills = {
            s.lower(): s for s in config.get("canonical_skills", [])
        }

    def normalize(self, data: list[str]) -> list[str]:
        """Normalize a list of raw skills.

        Args:
            data: List of raw skill strings.

        Returns:
            List of canonical skill strings.
        """
        if not data:
            return []

        normalized = set()
        for skill in data:
            resolved = self.alias_resolver.resolve(skill)
            # If the resolved skill matches a canonical skill (case-insensitive),
            # use the canonical case
            canonical = self._canonical_skills.get(resolved.lower())
            if canonical:
                normalized.add(canonical)
            else:
                # If it's an unknown skill, we might still keep it but cleaned up,
                # or we could filter it out. For now, keep it as is (resolved).
                if resolved:
                    normalized.add(resolved)

        return sorted(list(normalized))
