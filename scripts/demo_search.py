"""Standalone script to demo a semantic search."""

import argparse
import sys
from pathlib import Path

from backend.agents.retrieval_agent import RetrievalAgent
from backend.domain.normalized_job import NormalizedJob
from backend.embeddings.encoder import TextEncoder
from backend.retrieval.searcher import SemanticSearcher
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    """Run a demo semantic search against the built index."""
    parser = argparse.ArgumentParser(description="Demo Semantic Search")
    parser.add_argument(
        "--index-dir",
        type=str,
        default="data/index",
        help="Path to FAISS index directory",
    )
    parser.add_argument(
        "--query", type=str, required=True, help="Job description query string"
    )
    parser.add_argument(
        "--top-k", type=int, default=5, help="Number of results to retrieve"
    )
    args = parser.parse_args()

    index_dir = Path(args.index_dir)
    if not index_dir.exists():
        logger.error(
            f"Index directory not found: {index_dir}. Did you run build_index.py?"
        )
        sys.exit(1)

    logger.info("Loading encoder and index...")
    encoder = TextEncoder()
    searcher = SemanticSearcher(encoder, index_dir)
    agent = RetrievalAgent(searcher)

    # Create a dummy NormalizedJob for the query
    dummy_job = NormalizedJob(
        job_id="demo_job",
        canonical_title=None,
        canonical_required_skills=[],
        canonical_preferred_skills=[],
        canonical_industry=None,
        min_experience_years=0,
        seniority_level="mid",
        raw_title="Demo Query",
        raw_required_skills=[],
        raw_preferred_skills=[],
        description=args.query,
    )

    logger.info(f"Executing search for query: '{args.query}' (top_k={args.top_k})")
    results = agent.find_candidates(dummy_job, top_k=args.top_k)

    print("\n--- Search Results ---")
    if not results:
        print("No results found. (Index might be empty)")
    for i, res in enumerate(results, start=1):
        print(f"{i}. Candidate ID: {res.candidate_id} (Score: {res.score:.4f})")
    print("----------------------\n")


if __name__ == "__main__":
    main()
