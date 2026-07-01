"""Tests for the retrieval pipeline."""

from pathlib import Path

import numpy as np

from backend.cache.disk_cache import DiskCache
from backend.embeddings.encoder import TextEncoder, generate_content_hash
from backend.retrieval.index import VectorIndex
from backend.retrieval.metadata_store import MetadataStore


def test_generate_content_hash():
    """Test consistent hashing."""
    hash1 = generate_content_hash("Hello World")
    hash2 = generate_content_hash("Hello World")
    assert hash1 == hash2
    assert hash1 != generate_content_hash("hello world")


def test_text_encoder_caching(tmp_path: Path):
    """Test encoder retrieves from cache when available."""
    cache = DiskCache(tmp_path / "cache")
    encoder = TextEncoder(cache=cache)

    texts = ["Sample text 1", "Sample text 2"]

    # First encode (cache miss)
    emb1 = encoder.encode(texts)
    assert emb1.shape == (2, encoder.dimension)

    # Check cache was populated
    h1 = generate_content_hash(texts[0])
    assert cache.read(h1) is not None

    # Second encode (cache hit)
    emb2 = encoder.encode(texts)
    assert np.allclose(emb1, emb2)


def test_vector_index(tmp_path: Path):
    """Test FAISS wrapper operations."""
    dim = 32
    index = VectorIndex(dimension=dim)

    # Add vectors
    vectors = np.random.rand(5, dim).astype(np.float32)
    ids = np.array([10, 20, 30, 40, 50], dtype=np.int64)

    index.add(vectors, ids)
    assert index.count() == 5

    # Save and load
    index_path = tmp_path / "test.index"
    index.save(index_path)

    loaded_index = VectorIndex(dimension=dim, index_path=index_path)
    assert loaded_index.count() == 5

    # Search
    query = vectors[0:1].copy()
    distances, indices = loaded_index.search(query, top_k=2)

    assert indices.shape == (1, 2)
    assert indices[0][0] == 10  # Closest should be itself


def test_metadata_store(tmp_path: Path):
    """Test integer ID mapping."""
    store = MetadataStore()

    id1 = store.add("candidate_A")
    id2 = store.add("candidate_B")
    id3 = store.add("candidate_A")  # Should return existing

    assert id1 != id2
    assert id1 == id3

    assert store.get_candidate_id(id2) == "candidate_B"

    # Save and load
    store_path = tmp_path / "metadata.json"
    store.save(store_path)

    loaded_store = MetadataStore(store_path)
    assert loaded_store.get_candidate_id(id1) == "candidate_A"
