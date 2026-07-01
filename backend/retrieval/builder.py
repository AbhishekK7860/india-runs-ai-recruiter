"""Retrieval index builder."""

from pathlib import Path
from typing import Iterator

import numpy as np

from backend.domain.normalized_candidate import NormalizedCandidate
from backend.interfaces.embedding import EmbeddingProvider
from backend.metrics.timers import timers
from backend.retrieval.index import VectorIndex
from backend.retrieval.metadata_store import MetadataStore
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class RetrievalBuilder:
    """Builds the FAISS index by orchestrating encoding and storing."""

    def __init__(
        self,
        encoder: EmbeddingProvider,
        index_dir: str | Path,
    ) -> None:
        """Initialize the builder.

        Args:
            encoder: The EmbeddingProvider to encode candidate text.
            index_dir: Directory where the index and metadata will be saved.
        """
        self.encoder = encoder
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.index_path = self.index_dir / "faiss.index"
        self.metadata_path = self.index_dir / "metadata.json"

        self.index = VectorIndex(self.encoder.dimension)
        self.metadata_store = MetadataStore()

    def build_from_stream(
        self, candidate_stream: Iterator[NormalizedCandidate], batch_size: int = 100
    ) -> None:
        """Consume a candidate stream, encode in batches, and build the index.

        Args:
            candidate_stream: Generator yielding NormalizedCandidate objects.
            batch_size: Number of candidates to process at a time.
        """
        batch_texts = []
        batch_faiss_ids = []

        def _process_batch():
            if not batch_texts:
                return

            with timers.measure("encode_batch"):
                embeddings = self.encoder.encode(batch_texts)

            with timers.measure("index_add"):
                faiss_ids_np = np.array(batch_faiss_ids, dtype=np.int64)
                self.index.add(embeddings, faiss_ids_np)

            batch_texts.clear()
            batch_faiss_ids.clear()

        count = 0
        for candidate in candidate_stream:
            # We encode the full resume text for semantic retrieval
            text_to_encode = candidate.resume_text

            faiss_id = self.metadata_store.add(candidate.candidate_id)
            batch_texts.append(text_to_encode)
            batch_faiss_ids.append(faiss_id)

            count += 1
            if len(batch_texts) >= batch_size:
                _process_batch()
                logger.info(f"Indexed {count} candidates...")

        # Process remaining
        _process_batch()
        logger.info(f"Finished building index with {count} total candidates.")

    def save(self) -> None:
        """Save the index and metadata to the configured directory."""
        self.index.save(self.index_path)
        self.metadata_store.save(self.metadata_path)
        logger.info(f"Index and metadata saved to {self.index_dir}")
