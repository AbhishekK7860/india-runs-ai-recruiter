"""Job repository implementation."""

from pathlib import Path

from backend.interfaces.repository import JobRepository
from backend.parser.job_loader import DocxJobLoader
from backend.schemas.job import JobRequirement


class FileJobRepository(JobRepository):
    """File-backed job repository for extracting requirements from DOCX files."""

    def __init__(self, data_dir: str | Path) -> None:
        """Initialize the repository.

        Args:
            data_dir: Directory containing job DOCX files.
        """
        self.data_dir = Path(data_dir)

    def get(self, job_id: str) -> JobRequirement:
        """Load a specific job requirement from its DOCX file.

        Args:
            job_id: The ID (filename without extension) of the job.

        Returns:
            The parsed JobRequirement object.
        """
        # Assume job files are named `{job_id}.docx`
        job_file = self.data_dir / f"{job_id}.docx"

        loader = DocxJobLoader(job_id=job_id, title=job_id.replace("_", " ").title())
        return loader.parse(job_file)
