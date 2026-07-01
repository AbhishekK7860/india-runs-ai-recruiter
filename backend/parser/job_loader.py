"""Job description DOCX loader."""

from datetime import datetime, timezone
from pathlib import Path

import docx

from backend.interfaces.parser import JobParser
from backend.schemas.job import JobRequirement
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class DocxJobLoader(JobParser):
    """Parses a job description from a DOCX file."""

    def __init__(self, job_id: str, title: str) -> None:
        """Initialize the loader with job metadata.

        Args:
            job_id: The ID of the job being loaded.
            title: The title of the job.
        """
        self.job_id = job_id
        self.title = title

    def parse(self, source_path: str | Path) -> JobRequirement:
        """Extract text from the DOCX file and construct a JobRequirement.

        Note: This is a deterministic parser that extracts text while preserving
        some formatting (newlines). It does not use AI for summarization.

        Args:
            source_path: Path to the DOCX file.

        Returns:
            A populated JobRequirement object.
        """
        path = Path(source_path)
        if not path.exists():
            logger.error(f"Job source file not found: {path}")
            raise FileNotFoundError(f"Job source file not found: {path}")

        try:
            doc = docx.Document(path)
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text.strip())

            description = "\n\n".join(full_text)

            # Creating a basic requirement with empty/default fields since
            # AI extraction is deferred to a later phase.
            return JobRequirement(
                job_id=self.job_id,
                title=self.title,
                description=description,
                required_skills=[],
                preferred_skills=[],
                min_experience_years=0,
                seniority_level="mid",
                created_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.exception(f"Error reading DOCX file {path}: {e}")
            raise
