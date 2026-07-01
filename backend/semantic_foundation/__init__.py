"""Semantic foundation package."""

from backend.semantic_foundation.aliases import SkillAliasResolver
from backend.semantic_foundation.industry_normalizer import IndustryNormalizer
from backend.semantic_foundation.ontology import OntologyManager, ontology
from backend.semantic_foundation.skill_taxonomy import SkillNormalizer
from backend.semantic_foundation.title_normalizer import TitleNormalizer

__all__ = [
    "IndustryNormalizer",
    "OntologyManager",
    "SkillAliasResolver",
    "SkillNormalizer",
    "TitleNormalizer",
    "ontology",
]
