"""Offline Ranking Entrypoint for Redrob Submission.

This script executes purely offline using precomputed checkpoints.
It satisfies the < 5 minute runtime and no-network requirement.
"""

import argparse
import sys
import time
from pathlib import Path

# Add psutil for peak memory measurement if available
try:
    import psutil
except ImportError:
    psutil = None

from backend.agents.ranking_agent import RankingAgent
from backend.agents.ranking_strategy import WeightedFusionStrategy
from backend.schemas.llm import EvidencePackage, CriticReview
from backend.submission.csv_generator import CSVGenerator
from backend.submission.xlsx_generator import XLSXGenerator
from backend.submission.xml_generator import XMLGenerator
from backend.utils.checkpointer import Checkpointer
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def _get_memory_usage() -> float:
    """Return memory usage in MB if psutil is available."""
    if psutil:
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    return 0.0


def main():
    parser = argparse.ArgumentParser(description="Offline Ranking (Redrob Submission)")
    parser.add_argument("--output-dir", type=str, default="output", help="Output directory containing checkpoints")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    checkpoints_dir = output_dir / "checkpoints"
    
    if not (checkpoints_dir / "recruiter_evals.jsonl").exists() or not (checkpoints_dir / "critic_evals.jsonl").exists():
        logger.error(f"Precomputed checkpoints not found in {checkpoints_dir}. You must run precomputation first.")
        sys.exit(1)

    t_start = time.perf_counter()
    peak_memory = _get_memory_usage()

    # Load Checkpoints
    logger.info("Loading precomputed artifacts...")
    checkpointer = Checkpointer(output_dir)
    recruiter_evals = checkpointer.load_recruiter_evals()
    critic_evals = checkpointer.load_critic_evals()

    # Validate Critic loaded exactly Top 100
    if len(critic_evals) != 100:
        logger.warning(f"Expected exactly 100 critic evaluations, found {len(critic_evals)}. CSV requires exactly 100 rows.")

    # Reconstruct Candidates for Ranking
    candidates = []
    critic_reviews = []
    
    for cid, crit_data in critic_evals.items():
        try:
            rev = CriticReview.model_validate(crit_data["critic_review"])
            ev = EvidencePackage.model_validate(recruiter_evals[cid]["evidence"])
            candidates.append((ev, rev))
            critic_reviews.append(rev)
        except Exception as e:
            logger.error(f"Failed to reconstruct {cid} from checkpoints: {e}")
            sys.exit(1)

    peak_memory = max(peak_memory, _get_memory_usage())

    # Offline Ranking
    logger.info("Executing offline fusion ranking...")
    ranking_agent = RankingAgent(WeightedFusionStrategy())
    ranked = ranking_agent.rank(candidates)
    
    # We must export exactly 100 candidates to the CSV.
    final_100 = ranked[:100]

    # Generate CSV (Official)
    logger.info("Exporting submission artifacts...")
    csv_generator = CSVGenerator()
    csv_path = csv_generator.generate(final_100, critic_reviews, output_dir)
    
    # Generate XLSX (Official Excel format for Redrob Portal)
    xlsx_generator = XLSXGenerator()
    xlsx_path = xlsx_generator.generate(final_100, critic_reviews, output_dir)
    
    # Generate XML (Backward compatibility/existing workflow)
    # XML generator only requires the candidate dicts.
    # To ensure XML output works exactly as before, we output the Top-50 candidates only.
    xml_generator = XMLGenerator()
    xml_path = xml_generator.generate(ranked[:50], output_dir)
    
    t_end = time.perf_counter()
    peak_memory = max(peak_memory, _get_memory_usage())
    
    logger.info(f"Offline ranking completed in {t_end - t_start:.4f} seconds.")
    logger.info(f"Peak memory usage: {peak_memory:.2f} MB")
    logger.info("SUCCESS: submission.csv and submission.xlsx generated successfully.")


if __name__ == "__main__":
    main()
