"""Embedding provider interfaces."""

from abc import ABC, abstractmethod

import numpy as np


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers.

    This allows swapping embedding models (e.g., SentenceTransformers, OpenAI)
    without altering retrieval logic.
    """

    @abstractmethod
    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode a list of texts into dense vectors.

        Args:
            texts: List of strings to encode.

        Returns:
            A 2D numpy array of shape (len(texts), embedding_dimension) containing
            the dense vectors of type float32.
        """
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimension of the embeddings produced by this provider."""
        pass
