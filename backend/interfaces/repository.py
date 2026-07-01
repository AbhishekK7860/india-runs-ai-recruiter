"""Repository interfaces."""

from abc import ABC, abstractmethod
from typing import Iterator

from backend.schemas.candidate import CandidateProfile
from backend.schemas.job import JobRequirement


class CandidateRepository(ABC):
    """Abstract base class for candidate data access."""

    @abstractmethod
    def get_all(self) -> Iterator[CandidateProfile]:
        """Retrieve all candidates as a stream.

        Yields:
            Validated CandidateProfile objects.
        """
        pass


class JobRepository(ABC):
    """Abstract base class for job requirement data access."""

    @abstractmethod
    def get(self, job_id: str) -> JobRequirement:
        """Retrieve a specific job requirement.

        Args:
            job_id: The ID of the job to retrieve.

        Returns:
            The requested JobRequirement.
        """
        pass
