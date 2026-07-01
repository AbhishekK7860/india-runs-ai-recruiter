"""Security filter module.

Provides a mandatory checkpoint to scrub PII and prevent prompt injection
before data reaches the LLM evaluator, satisfying global security requirements.
"""

import re
from dataclasses import dataclass

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SecurityViolation(Exception):
    """Raised when a candidate profile triggers a security or safety violation."""

    pass


@dataclass
class ScrubResult:
    """Result of scrubbing text for PII."""

    clean_text: str
    redacted_categories: list[str]


class SecurityFilter:
    """Security checkpoint for LLM agents."""

    # Basic regex patterns for PII detection
    # In a real production system, these would be much more comprehensive
    # or rely on dedicated DLP (Data Loss Prevention) APIs.
    SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    # Matches common 16-digit credit card formats
    CC_PATTERN = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")

    # Common prompt injection triggers
    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+previous\s+instructions", re.IGNORECASE),
        re.compile(r"disregard\s+all\s+prior", re.IGNORECASE),
        re.compile(r"system\s+prompt", re.IGNORECASE),
        re.compile(r"you\s+are\s+now", re.IGNORECASE),
        re.compile(r"new\s+rule:", re.IGNORECASE),
        re.compile(r"bypass\s+security", re.IGNORECASE),
    ]

    def scrub_text(self, text: str) -> ScrubResult:
        """Scrub PII from text.

        Args:
            text: The raw text string.

        Returns:
            ScrubResult containing the cleaned text and list of redacted categories.
        """
        redacted = set()
        clean = text

        if self.SSN_PATTERN.search(clean):
            clean = self.SSN_PATTERN.sub("[REDACTED_SSN]", clean)
            redacted.add("SSN")

        if self.CC_PATTERN.search(clean):
            clean = self.CC_PATTERN.sub("[REDACTED_CREDIT_CARD]", clean)
            redacted.add("CREDIT_CARD")

        return ScrubResult(clean_text=clean, redacted_categories=sorted(list(redacted)))

    def detect_injection(self, text: str) -> bool:
        """Detect potential prompt injection in text.

        Args:
            text: The text to scan.

        Returns:
            True if injection patterns are detected, False otherwise.
        """
        for pattern in self.INJECTION_PATTERNS:
            if pattern.search(text):
                return True
        return False

    def verify_safe(self, text: str, context_id: str) -> str:
        """Perform full security check on text, raising exception if unsafe.

        Args:
            text: The text to verify and scrub.
            context_id: Identifier (e.g., candidate_id) for logging purposes.

        Returns:
            The scrubbed, safe text.

        Raises:
            SecurityViolation: If prompt injection is detected.
        """
        if self.detect_injection(text):
            logger.warning(
                f"SECURITY ALERT: Prompt injection detected for ID: {context_id}"
            )
            raise SecurityViolation("Prompt injection attempt detected.")

        scrub_result = self.scrub_text(text)
        if scrub_result.redacted_categories:
            logger.info(
                f"Scrubbed PII ({', '.join(scrub_result.redacted_categories)}) "
                f"from ID: {context_id}"
            )

        return scrub_result.clean_text
