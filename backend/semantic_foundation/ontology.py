"""Ontology orchestration."""

from backend.semantic_foundation.industry_normalizer import IndustryNormalizer
from backend.semantic_foundation.skill_taxonomy import SkillNormalizer
from backend.semantic_foundation.title_normalizer import TitleNormalizer


class OntologyManager:
    """Central manager for all semantic normalization engines."""

    def __init__(self) -> None:
        """Initialize all normalizers."""
        self.title_normalizer = TitleNormalizer()
        self.industry_normalizer = IndustryNormalizer()
        self.skill_normalizer = SkillNormalizer()

    def normalize_title(self, title: str) -> str | None:
        """Normalize a title."""
        return self.title_normalizer.normalize(title)

    def normalize_industry(self, industry: str) -> str | None:
        """Normalize an industry."""
        return self.industry_normalizer.normalize(industry)

    def normalize_skills(self, skills: list[str]) -> list[str]:
        """Normalize a list of skills."""
        return self.skill_normalizer.normalize(skills)


# Global singleton for use across the pipeline
ontology = OntologyManager()
