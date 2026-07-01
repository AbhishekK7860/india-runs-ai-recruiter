"""CSV Generator for final competition submission."""

import csv
from pathlib import Path
from typing import Any

from backend.utils.logger import get_logger
from backend.schemas.llm import CriticReview

logger = get_logger(__name__)

class CSVGenerator:
    """Generates the required submission.csv file."""

    def generate(self, ranked_candidates: list[dict[str, Any]], critic_reviews: list[CriticReview], output_dir: Path) -> Path:
        """Convert the ranked list into the competition CSV format.
        
        Args:
            ranked_candidates: List of candidate dictionaries.
            critic_reviews: List of CriticReview objects containing the reasoning.
            output_dir: Directory to save submission.csv.
            
        Returns:
            Path to the generated CSV file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_path = output_dir / "submission.csv"
        
        # Enforce deterministic tie-breaking: score descending, candidate_id ascending
        sorted_candidates = sorted(
            ranked_candidates,
            key=lambda x: (-x.get("final_score", 0), x["candidate_id"])
        )
        
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["candidate_id", "rank", "score", "reasoning"])
            
            for i, cand in enumerate(sorted_candidates, 1):
                cid = cand["candidate_id"]
                # Map CriticReview.adjustment_reasoning directly to the CSV reasoning column
                # without any transformation, summarization, truncation, or regeneration.
                reasoning = ""
                for rev in critic_reviews:
                    if rev.candidate_id == cid:
                        reasoning = rev.adjustment_reasoning
                        break
                        
                writer.writerow([
                    cid, 
                    i, 
                    f"{cand.get('final_score', 0):.4f}", 
                    reasoning
                ])
                
        logger.info(f"CSV Submission generated at {csv_path}")
        return csv_path
