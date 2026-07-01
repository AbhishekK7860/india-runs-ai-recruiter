"""Semantic searcher module."""

from pathlib import Path

from backend.domain.normalized_job import NormalizedJob
from backend.interfaces.embedding import EmbeddingProvider
from backend.metrics.timers import timers
from backend.retrieval.index import VectorIndex
from backend.retrieval.metadata_store import MetadataStore
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SearchResult:
    """Data class representing a single search result."""

    def __init__(self, candidate_id: str, score: float):
        self.candidate_id = candidate_id
        self.score = score


class SemanticSearcher:
    """High-level semantic search API."""

    def __init__(
        self,
        encoder: EmbeddingProvider,
        index_dir: str | Path,
    ) -> None:
        """Initialize the searcher by loading the index.

        Args:
            encoder: The EmbeddingProvider for query encoding.
            index_dir: Directory where the index and metadata are stored.
        """
        self.encoder = encoder
        self.index_dir = Path(index_dir)

        index_path = self.index_dir / "faiss.index"
        metadata_path = self.index_dir / "metadata.json"

        self.index = VectorIndex(self.encoder.dimension, index_path)
        self.metadata_store = MetadataStore(metadata_path)

    def search(self, job: NormalizedJob, top_k: int = 50) -> list[SearchResult]:
        """Perform a semantic search against the index using a job description.

        Args:
            job: The normalized job object containing the description.
            top_k: Number of results to return.

        Returns:
            A list of SearchResult objects containing candidate IDs and
            similarity scores.
        """
        with timers.measure("query_encoding"):
            query_embedding = self.encoder.encode([job.description])

        with timers.measure("index_search"):
            distances, indices = self.index.search(query_embedding, top_k)

        results = []
        if distances.size > 0:
            # Extract the top-k for our single query
            for dist, idx in zip(distances[0], indices[0]):
                if idx == -1:  # FAISS returns -1 for empty slots
                    continue
                candidate_id = self.metadata_store.get_candidate_id(idx)
                if candidate_id:
                    results.append(SearchResult(candidate_id, float(dist)))

        return results
