"""Standalone script to build the FAISS index."""

import argparse
import sys
from pathlib import Path

from backend.cache.cache_manager import CacheManager
from backend.embeddings.encoder import TextEncoder
from backend.metrics.timers import timers
from backend.retrieval.builder import RetrievalBuilder
from backend.services.data_pipeline import DataPipeline
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    """Build the FAISS index from the candidate dataset."""
    parser = argparse.ArgumentParser(description="Build FAISS index for AI Recruiter")
    parser.add_argument(
        "--dataset", type=str, required=True, help="Path to JSONL dataset"
    )
    parser.add_argument(
        "--job-dir", type=str, required=True, help="Path to jobs directory"
    )
    parser.add_argument(
        "--index-dir", type=str, default="data/index", help="Output dir for FAISS index"
    )
    parser.add_argument(
        "--batch-size", type=int, default=100, help="Batch size for encoding"
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        logger.error(f"Dataset not found: {dataset_path}")
        sys.exit(1)

    # Initialize components
    cache_manager = CacheManager(
        dataset_hash="manual_build", base_dir=Path("data/.cache")
    )
    pipeline = DataPipeline(cache_manager, dataset_path, Path(args.job_dir))

    # TextEncoder uses the shared embeddings cache
    encoder = TextEncoder(cache=cache_manager.embeddings)
    builder = RetrievalBuilder(encoder, args.index_dir)

    logger.info(f"Starting index build into {args.index_dir}...")

    with timers.measure("total_build_time"):
        # Stream candidates, normalize them via pipeline, and build index
        candidate_stream = pipeline.stream_candidates()
        builder.build_from_stream(candidate_stream, batch_size=args.batch_size)
        builder.save()

    logger.info(f"Total build time: {timers.get_total('total_build_time'):.2f} seconds")
    logger.info("Done.")


if __name__ == "__main__":
    main()
