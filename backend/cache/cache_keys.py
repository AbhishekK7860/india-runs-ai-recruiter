"""Cache key generation helpers."""

import hashlib


def generate_cache_key(identifier: str, version: str) -> str:
    """Generate a deterministic cache key.

    Args:
        identifier: The unique ID of the object (e.g., candidate_id).
        version: The schema or cache version.

    Returns:
        A SHA-256 hex string used as the cache file name.
    """
    raw_key = f"{identifier}::{version}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
