"""Skill alias resolution."""

from backend.semantic_foundation.config_loader import load_yaml_config


class SkillAliasResolver:
    """Resolves skill aliases to canonical names."""

    def __init__(self) -> None:
        """Initialize by loading aliases from config."""
        config = load_yaml_config("aliases.yaml")
        self._aliases: dict[str, str] = {}

        aliases_map = config.get("skill_aliases", {})
        for alias, canonical in aliases_map.items():
            self._aliases[alias.lower()] = canonical

    def resolve(self, skill: str) -> str:
        """Resolve a skill name to its canonical form if an alias exists.

        Args:
            skill: The raw skill name.

        Returns:
            The canonical skill name, or the original if no alias matches.
        """
        if not skill:
            return skill

        cleaned = skill.strip().lower()
        return self._aliases.get(cleaned, skill.strip())
