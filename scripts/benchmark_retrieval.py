"""Benchmarking script for the retrieval pipeline."""

import os
import time

import numpy as np
import psutil

from backend.embeddings.encoder import TextEncoder
from backend.retrieval.index import VectorIndex
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def get_memory_usage_mb() -> float:
    """Return the current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def main() -> None:
    """Run retrieval benchmarks."""
    logger.info("Starting Retrieval Benchmarks...")

    # 1. Encoding Throughput
    logger.info("--- 1. Encoding Throughput ---")
    encoder = TextEncoder()
    dummy_texts = ["This is a sample resume text used for benchmarking."] * 1000

    start_mem = get_memory_usage_mb()
    start_time = time.perf_counter()

    _ = encoder.encode(dummy_texts)

    end_time = time.perf_counter()
    end_mem = get_memory_usage_mb()

    elapsed = end_time - start_time
    throughput = len(dummy_texts) / elapsed

    logger.info(f"Encoded {len(dummy_texts)} texts in {elapsed:.4f}s")
    logger.info(f"Throughput: {throughput:.2f} texts/sec")
    logger.info(f"Memory overhead during encoding: {end_mem - start_mem:.2f} MB")

    # 2. Index Build Time
    logger.info("--- 2. Index Build Time ---")
    dim = encoder.dimension
    num_vectors = 10000

    # Generate random normalized vectors for FAISS benchmark
    np.random.seed(42)
    vectors = np.random.rand(num_vectors, dim).astype(np.float32)
    # normalize
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = vectors / norms

    ids = np.arange(num_vectors, dtype=np.int64)

    index = VectorIndex(dim)

    start_time = time.perf_counter()
    index.add(vectors, ids)
    elapsed_build = time.perf_counter() - start_time

    logger.info(f"Added {num_vectors} vectors to index in {elapsed_build:.4f}s")

    # 3. Search Latency
    logger.info("--- 3. Search Latency ---")
    query_vector = vectors[0:1]  # using the first vector as query

    start_time = time.perf_counter()
    distances, indices = index.search(query_vector, top_k=50)
    elapsed_search = time.perf_counter() - start_time

    logger.info(
        f"Single query search latency (top_k=50): {elapsed_search * 1000:.2f} ms"
    )

    # Batch search
    batch_queries = vectors[:100]
    start_time = time.perf_counter()
    _, _ = index.search(batch_queries, top_k=50)
    elapsed_batch_search = time.perf_counter() - start_time

    logger.info(
        f"Batch query (n=100) search latency (top_k=50): "
        f"{elapsed_batch_search * 1000:.2f} ms"
    )
    logger.info(
        f"Per-query batch latency: {(elapsed_batch_search / 100) * 1000:.2f} ms"
    )

    logger.info("Benchmarks completed.")


if __name__ == "__main__":
    main()
