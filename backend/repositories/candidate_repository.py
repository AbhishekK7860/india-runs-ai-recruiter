"""Candidate repository implementation."""

from pathlib import Path
from typing import Iterator

from backend.interfaces.repository import CandidateRepository
from backend.parser.candidate_loader import StreamingCandidateLoader
from backend.profiling.candidate_profiler import CandidateProfiler
from backend.schemas.candidate import CandidateProfile


class FileCandidateRepository(CandidateRepository):
    """File-backed candidate repository that yields a stream of profiles."""

    def __init__(
        self, data_path: str | Path, profiler: CandidateProfiler | None = None
    ) -> None:
        """Initialize the repository.

        Args:
            data_path: Path to the JSONL dataset.
            profiler: Optional profiler instance.
        """
        self.data_path = Path(data_path)
        self.loader = StreamingCandidateLoader(profiler=profiler)

    def get_all(self) -> Iterator[CandidateProfile]:
        """Stream all candidates from the data source.

        Yields:
            Validated CandidateProfile objects.
        """
        yield from self.loader.parse(self.data_path)
