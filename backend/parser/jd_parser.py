"""JD Parser — Phase 2+ implementation.

Provides pre-processing utilities that convert raw job description text
(e.g., from a DOCX or plain-text file) into a clean, normalised string
ready for JDAnalystAgent. Handles encoding issues, whitespace normalisation,
and section extraction.
"""

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class JDParser:
    """Parses and normalises raw job description text for downstream processing."""

    def parse(self, raw_text: str) -> dict:
        """Parse raw job description text into a structured dict.

        Args:
            raw_text: The raw, unprocessed job description string.

        Returns:
            A dict with at minimum a 'cleaned_text' key and optional
            section keys such as 'responsibilities', 'requirements', etc.

        Raises:
            NotImplementedError: Until Phase 2 is implemented.
        """
        raise NotImplementedError("Implemented in Phase 2")
