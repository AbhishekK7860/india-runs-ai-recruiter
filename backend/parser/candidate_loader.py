"""Streaming candidate loader."""

from pathlib import Path
from typing import Iterator

import orjson
from pydantic import ValidationError

from backend.interfaces.parser import CandidateParser
from backend.profiling.candidate_profiler import CandidateProfiler
from backend.schemas.candidate import CandidateProfile
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class StreamingCandidateLoader(CandidateParser):
    """Loads candidates from a JSONL file using a memory-efficient generator."""

    def __init__(self, profiler: CandidateProfiler | None = None) -> None:
        """Initialize the loader.

        Args:
            profiler: Optional profiler to track statistics during parsing.
        """
        self.profiler = profiler
        from backend.parser.candidate_mapper import CandidateMapper
        self.mapper = CandidateMapper()

    def parse(self, source_path: str | Path) -> Iterator[CandidateProfile]:
        """Parse the candidate data file line by line.

        Args:
            source_path: The path to the JSONL data file.

        Yields:
            Validated CandidateProfile objects.
        """
        path = Path(source_path)
        if not path.exists():
            logger.error(f"Candidate source file not found: {path}")
            return

        with open(path, "rb") as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = orjson.loads(line)
                    mapped_data = self.mapper.map(data)
                    candidate = CandidateProfile(**mapped_data)

                    if self.profiler:
                        self.profiler.profile_raw(candidate)

                    yield candidate

                except orjson.JSONDecodeError as e:
                    logger.warning(f"JSON decoding error at line {line_number}: {e}")
                    if self.profiler:
                        self.profiler.record_malformed()

                except ValidationError as e:
                    logger.warning(f"Validation error at line {line_number}: {e}")
                    if self.profiler:
                        self.profiler.record_malformed()

                except Exception as e:
                    logger.exception(f"Unexpected error at line {line_number}: {e}")
                    if self.profiler:
                        self.profiler.record_skipped()
