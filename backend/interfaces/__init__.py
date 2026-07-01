"""Interfaces package."""

from backend.interfaces.embedding import EmbeddingProvider
from backend.interfaces.normalizer import Normalizer
from backend.interfaces.parser import CandidateParser, JobParser
from backend.interfaces.repository import CandidateRepository, JobRepository

__all__ = [
    "CandidateParser",
    "CandidateRepository",
    "EmbeddingProvider",
    "JobParser",
    "JobRepository",
    "Normalizer",
]
