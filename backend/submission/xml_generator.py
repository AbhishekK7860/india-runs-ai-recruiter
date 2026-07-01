"""XML Generator for final competition submission."""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class XMLGenerator:
    """Generates the required submission.xml file."""

    def generate(self, ranked_candidates: list[dict[str, Any]], output_dir: Path) -> Path:
        """Convert the ranked list into the competition XML format.
        
        Args:
            ranked_candidates: List of candidate dictionaries.
            output_dir: Directory to save submission.xml.
            
        Returns:
            Path to the generated XML file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        xml_path = output_dir / "submission.xml"
        
        root = ET.Element("submission")
        candidates_elem = ET.SubElement(root, "candidates")
        
        for cand in ranked_candidates:
            # Create candidate element with attributes
            cand_elem = ET.SubElement(
                candidates_elem, 
                "candidate", 
                id=str(cand["candidate_id"]), 
                rank=str(cand["rank"])
            )
            # Add score as text or child (assuming simple challenge schema)
            score_elem = ET.SubElement(cand_elem, "score")
            score_elem.text = f"{cand.get('final_score', 0):.4f}"

        # Write formatting
        tree = ET.ElementTree(root)
        try:
            # We indent for readability using ET.indent if available (Python 3.9+)
            ET.indent(tree, space="  ", level=0)
        except AttributeError:
            pass  # Fallback for older Pythons
            
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        logger.info(f"XML Submission generated at {xml_path}")
        return xml_path
