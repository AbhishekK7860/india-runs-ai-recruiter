"""Parser interfaces."""

from abc import ABC, abstractmethod
from typing import Iterator

from backend.schemas.candidate import CandidateProfile
from backend.schemas.job import JobRequirement


class CandidateParser(ABC):
    """Abstract base class for candidate parsing."""

    @abstractmethod
    def parse(self, source_path: str) -> Iterator[CandidateProfile]:
        """Parse the candidate source file into a stream of profiles.

        Args:
            source_path: The path to the candidate data file.

        Yields:
            Parsed CandidateProfile objects.
        """
        pass


class JobParser(ABC):
    """Abstract base class for job parsing."""

    @abstractmethod
    def parse(self, source_path: str) -> JobRequirement:
        """Parse the job description source file into a requirement object.

        Args:
            source_path: The path to the job description file.

        Returns:
            The parsed JobRequirement.
        """
        pass
