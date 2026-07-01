"""XML Generator utility — Phase 2+ implementation.

Provides a standalone utility for converting a submission dict (as produced
by the Pipeline) into the required XML string format. Wraps the to_xml()
method on XMLSubmission with additional error handling and logging.
"""

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class XMLGenerator:
    """Generates the submission XML string from a ranked pipeline output dict."""

    def generate(self, submission: dict) -> str:
        """Serialise a submission dict into a valid XML string.

        Args:
            submission: A dict conforming to the XMLSubmission schema fields:
                job_id, generated_at, and candidates list.

        Returns:
            A UTF-8 XML string ready to be written to disk or posted to the
            submission endpoint.

        Raises:
            NotImplementedError: Until Phase 2 is implemented.
        """
        raise NotImplementedError("Implemented in Phase 2")
