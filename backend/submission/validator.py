"""Submission validator."""

import xml.etree.ElementTree as ET
from pathlib import Path

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SubmissionValidationError(Exception):
    """Raised when the submission XML violates the challenge specification."""
    pass


class SubmissionValidator:
    """Validates the generated submission.xml."""

    def validate(self, xml_path: Path) -> bool:
        """Validate the XML structure and constraints.
        
        Args:
            xml_path: Path to the submission.xml file.
            
        Returns:
            True if valid. Raises SubmissionValidationError otherwise.
        """
        if not xml_path.exists():
            raise SubmissionValidationError(f"Submission file {xml_path} does not exist.")
            
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except ET.ParseError as e:
            raise SubmissionValidationError(f"Invalid XML syntax: {e}")
            
        if root.tag != "submission":
            raise SubmissionValidationError("Root tag must be <submission>.")
            
        candidates_elem = root.find("candidates")
        if candidates_elem is None:
            raise SubmissionValidationError("Missing <candidates> tag.")
            
        candidate_nodes = candidates_elem.findall("candidate")
        if len(candidate_nodes) != 50:
            raise SubmissionValidationError(
                f"Submission must contain exactly 50 candidates, found {len(candidate_nodes)}."
            )
            
        seen_ranks = set()
        seen_ids = set()
        
        for node in candidate_nodes:
            cid = node.attrib.get("id")
            rank = node.attrib.get("rank")
            
            if not cid:
                raise SubmissionValidationError("Candidate node missing 'id' attribute.")
            if not rank:
                raise SubmissionValidationError("Candidate node missing 'rank' attribute.")
                
            if cid in seen_ids:
                raise SubmissionValidationError(f"Duplicate candidate ID found: {cid}")
            seen_ids.add(cid)
            
            try:
                rank_int = int(rank)
            except ValueError:
                raise SubmissionValidationError(f"Rank must be an integer, got '{rank}'.")
                
            if rank_int in seen_ranks:
                raise SubmissionValidationError(f"Duplicate rank found: {rank_int}")
            if not (1 <= rank_int <= 50):
                raise SubmissionValidationError(f"Rank {rank_int} is out of bounds (1-50).")
                
            seen_ranks.add(rank_int)
            
        logger.info("Submission.xml successfully passed all validation checks!")
        return True
