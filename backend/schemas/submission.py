"""Pydantic schema for the final XML submission.

Defines XMLSubmission, which wraps a ranked list of candidates and provides
a to_xml() method for serialising the submission to the required XML format.
"""

import xml.etree.ElementTree as ET
from datetime import datetime

from pydantic import BaseModel, Field

from backend.schemas.ranking import RankedCandidate


class XMLSubmission(BaseModel):
    """Full submission payload containing ranked candidates for a job."""

    job_id: str = Field(..., description="Job identifier this submission is for.")
    generated_at: datetime = Field(
        ..., description="Timestamp when this submission was generated."
    )
    candidates: list[RankedCandidate] = Field(
        default_factory=list, description="Ordered list of ranked candidates."
    )

    def to_xml(self) -> str:
        """Serialise the submission to the required XML format.

        Returns:
            A UTF-8 encoded XML string conforming to the submission spec.
        """
        root = ET.Element("submission")

        job_id_el = ET.SubElement(root, "job_id")
        job_id_el.text = self.job_id

        generated_at_el = ET.SubElement(root, "generated_at")
        generated_at_el.text = self.generated_at.isoformat()

        candidates_el = ET.SubElement(root, "candidates")
        for candidate in self.candidates:
            cand_el = ET.SubElement(candidates_el, "candidate")

            rank_el = ET.SubElement(cand_el, "rank")
            rank_el.text = str(candidate.rank)

            cid_el = ET.SubElement(cand_el, "candidate_id")
            cid_el.text = candidate.candidate_id

            sem_el = ET.SubElement(cand_el, "semantic_score")
            sem_el.text = str(candidate.semantic_score)

            beh_el = ET.SubElement(cand_el, "behaviour_score")
            beh_el.text = str(candidate.behaviour_score)

            conf_el = ET.SubElement(cand_el, "confidence")
            conf_el.text = str(candidate.confidence)

            reason_el = ET.SubElement(cand_el, "reasoning")
            reason_el.text = candidate.reasoning

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        body = ET.tostring(root, encoding="unicode")
        return xml_declaration + body
