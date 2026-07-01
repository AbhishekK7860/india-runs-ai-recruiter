"""FAISS Vector Store — Phase 2+ implementation.

Manages a FAISS flat-IP index built from candidate résumé embeddings.
Supports adding embeddings, persisting the index to disk, and performing
approximate nearest-neighbour search to retrieve the top-K candidates
given a query embedding.
"""

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class FAISSStore:
    """Manages a FAISS index for approximate-nearest-neighbour candidate retrieval."""

    def search(self, embedding: list[float], top_k: int) -> list[dict]:
        """Search the FAISS index and return the top-K nearest neighbours.

        Args:
            embedding: Query embedding vector (dense float list).
            top_k: Number of nearest neighbours to return.

        Returns:
            A list of dicts, each containing 'candidate_id' and 'score'.

        Raises:
            NotImplementedError: Until Phase 2 is implemented.
        """
        raise NotImplementedError("Implemented in Phase 2")
