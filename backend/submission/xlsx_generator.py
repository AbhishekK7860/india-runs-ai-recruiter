"""XLSX Generator for final competition submission."""

from pathlib import Path
from typing import Any
import openpyxl

from backend.utils.logger import get_logger
from backend.schemas.llm import CriticReview

logger = get_logger(__name__)

class XLSXGenerator:
    """Generates the required submission.xlsx file."""

    def generate(self, ranked_candidates: list[dict[str, Any]], critic_reviews: list[CriticReview], output_dir: Path) -> Path:
        """Convert the ranked list into the competition XLSX format.
        
        Args:
            ranked_candidates: List of candidate dictionaries.
            critic_reviews: List of CriticReview objects containing the reasoning.
            output_dir: Directory to save submission.xlsx.
            
        Returns:
            Path to the generated XLSX file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        xlsx_path = output_dir / "submission.xlsx"
        
        # Enforce deterministic tie-breaking: score descending, candidate_id ascending
        sorted_candidates = sorted(
            ranked_candidates,
            key=lambda x: (-x.get("final_score", 0), x["candidate_id"])
        )
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Submission"
        
        # Header
        ws.append(["candidate_id", "rank", "score", "reasoning"])
        
        for i, cand in enumerate(sorted_candidates, 1):
            cid = cand["candidate_id"]
            # Map CriticReview.adjustment_reasoning directly to the XLSX reasoning column
            # without any transformation, summarization, truncation, or regeneration.
            reasoning = ""
            for rev in critic_reviews:
                if rev.candidate_id == cid:
                    reasoning = rev.adjustment_reasoning
                    break
                    
            ws.append([
                cid, 
                i, 
                f"{cand.get('final_score', 0):.4f}", 
                reasoning
            ])
            
        wb.save(xlsx_path)
        logger.info(f"XLSX Submission generated at {xlsx_path}")
        return xlsx_path
