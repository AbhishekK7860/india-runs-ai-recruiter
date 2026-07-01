"""Sentence Encoder — Phase 2 implementation.

Wraps the sentence-transformers library to encode free-text strings into dense
float vectors. Implements the EmbeddingProvider interface and supports content
caching to avoid recomputing embeddings.
"""

import hashlib

import numpy as np
from sentence_transformers import SentenceTransformer

from backend.cache.disk_cache import DiskCache
from backend.interfaces.embedding import EmbeddingProvider
from backend.semantic_foundation.config_loader import load_yaml_config
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def generate_content_hash(text: str) -> str:
    """Generate a SHA-256 hash for a given text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class TextEncoder(EmbeddingProvider):
    """Encodes text into dense sentence embeddings using sentence-transformers."""

    def __init__(self, cache: DiskCache | None = None) -> None:
        """Initialize the encoder and load the configured model.

        Args:
            cache: Optional DiskCache instance to store/retrieve embeddings
                by content hash.
        """
        config = load_yaml_config("embedding.yaml")
        model_name = config.get("model_name", "sentence-transformers/all-MiniLM-L6-v2")
        self.device = config.get("device", "cpu")
        self.batch_size = config.get("batch_size", 32)

        logger.info(f"Loading embedding model: {model_name} on {self.device}")
        self._model = SentenceTransformer(model_name, device=self.device)
        self._dimension = self._model.get_embedding_dimension()

        self.cache = cache

    @property
    def dimension(self) -> int:
        """Return the dimension of the embeddings produced by this provider."""
        return self._dimension

    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode a list of texts into dense vectors.

        Args:
            texts: List of strings to encode.

        Returns:
            A 2D numpy array of shape (len(texts), dimension) of float32.
        """
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        results = []
        texts_to_encode = []
        indices_to_encode = []

        # Check cache for existing embeddings
        for i, text in enumerate(texts):
            # Normalise text slightly for consistent hashing
            clean_text = text.strip()
            if not clean_text:
                # Handle empty strings gracefully
                results.append(np.zeros(self.dimension, dtype=np.float32))
                continue

            cached_emb = None
            if self.cache:
                content_hash = generate_content_hash(clean_text)
                cached_data = self.cache.read(content_hash)
                if cached_data and "vector" in cached_data:
                    cached_emb = np.array(cached_data["vector"], dtype=np.float32)

            if cached_emb is not None:
                results.append(cached_emb)
            else:
                results.append(None)  # Placeholder
                texts_to_encode.append(clean_text)
                indices_to_encode.append(i)

        # Encode remaining texts
        if texts_to_encode:
            logger.debug(f"Encoding {len(texts_to_encode)} new texts...")
            encoded_vectors = self._model.encode(
                texts_to_encode,
                batch_size=self.batch_size,
                convert_to_numpy=True,
                show_progress_bar=False,
            )

            # Put them in results and cache them
            for idx, text, vector in zip(
                indices_to_encode, texts_to_encode, encoded_vectors
            ):
                results[idx] = vector.astype(np.float32)
                if self.cache:
                    content_hash = generate_content_hash(text)
                    self.cache.write(content_hash, {"vector": vector.tolist()})

        return np.vstack(results).astype(np.float32)
