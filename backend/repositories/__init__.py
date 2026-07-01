"""Repositories package."""

from backend.repositories.candidate_repository import FileCandidateRepository
from backend.repositories.job_repository import FileJobRepository

__all__ = [
    "FileCandidateRepository",
    "FileJobRepository",
]
