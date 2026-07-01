"""Explainability reporting module."""

from pathlib import Path
from typing import Any

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class RankingExplainer:
    """Generates explainability reports from existing LLM reasoning."""

    def generate_report(self, ranked_candidates: list[dict[str, Any]], output_dir: Path) -> None:
        """Generate a human-readable markdown report for the top candidates.

        Args:
            ranked_candidates: List of candidate dictionaries with ranks and reasoning.
            output_dir: Directory to output the report.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "explainability_report.md"
        
        lines = [
            "# AI Recruiter - Explainability Report",
            "This report justifies the ranking of the top candidates using insights from the AI evaluators.",
            ""
        ]
        
        for cand in ranked_candidates:
            lines.append(f"## Rank {cand.get('rank', 'N/A')} - Candidate `{cand['candidate_id']}`")
            lines.append(f"- **Final Score:** {cand.get('final_score', 0):.4f}")
            lines.append(f"- **Semantic Score (FAISS):** {cand.get('semantic_score', 0):.4f}")
            lines.append(f"- **Behaviour Score:** {cand.get('behaviour_score', 0):.4f}")
            
            if 'recruiter_evaluation' in cand:
                rec_eval = cand['recruiter_evaluation']
                lines.append(f"- **Recruiter Fit Score:** {rec_eval.fit_score}")
                lines.append(f"  - *Reasoning:* {rec_eval.reasoning}")
                lines.append(f"  - *Strengths:* {', '.join(rec_eval.strengths)}")
                lines.append(f"  - *Gaps:* {', '.join(rec_eval.gaps)}")
                
            if 'critic_review' in cand and cand['critic_review']:
                critic = cand['critic_review']
                lines.append(f"- **Critic Adjusted Score:** {critic.adjusted_fit_score}")
                lines.append(f"  - *Critic Reasoning:* {critic.adjustment_reasoning}")
                if critic.is_hallucination_detected:
                    lines.append("  - ⚠️ **Hallucination Detected by Critic!** Penalty applied.")
            
            lines.append("---\n")
            
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
            
        logger.info(f"Explainability report generated at {report_path}")
