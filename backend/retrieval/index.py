"""FAISS index wrapper."""

from pathlib import Path

import faiss
import numpy as np

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class VectorIndex:
    """Wraps FAISS index operations."""

    def __init__(self, dimension: int, index_path: str | Path | None = None) -> None:
        """Initialize the vector index.

        Args:
            dimension: Dimensionality of the embeddings.
            index_path: Optional path to load an existing index from disk.
        """
        self.dimension = dimension
        if index_path and Path(index_path).exists():
            logger.info(f"Loading FAISS index from {index_path}")
            self.index = faiss.read_index(str(index_path))
        else:
            # Using IndexFlatIP for cosine similarity (assuming normalized vectors)
            self.index = faiss.IndexFlatIP(dimension)
            # To maintain mapping, we use an IDMap
            self.index = faiss.IndexIDMap(self.index)

    def add(self, embeddings: np.ndarray, ids: np.ndarray) -> None:
        """Add embeddings to the index.

        Args:
            embeddings: 2D numpy array of embeddings (float32).
            ids: 1D numpy array of integer IDs corresponding to the embeddings.
        """
        if embeddings.shape[0] == 0:
            return

        # Normalize vectors for cosine similarity if using IP index
        faiss.normalize_L2(embeddings)
        self.index.add_with_ids(embeddings, ids)

    def search(self, query: np.ndarray, top_k: int) -> tuple[np.ndarray, np.ndarray]:
        """Search the index for nearest neighbors.

        Args:
            query: 2D numpy array of query embeddings (float32).
            top_k: Number of nearest neighbors to retrieve.

        Returns:
            Tuple of (distances, indices). Both are 2D arrays of shape
            (len(query), top_k).
        """
        if self.index.ntotal == 0:
            return np.array([]), np.array([])

        # Query must also be normalized for cosine similarity
        query_copy = query.copy()
        faiss.normalize_L2(query_copy)
        distances, indices = self.index.search(query_copy, top_k)
        return distances, indices

    def save(self, path: str | Path) -> None:
        """Save the index to disk.

        Args:
            path: File path to save the index.
        """
        faiss.write_index(self.index, str(path))

    def count(self) -> int:
        """Return the number of vectors in the index."""
        return self.index.ntotal
