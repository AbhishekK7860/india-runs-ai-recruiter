"""High-level cache manager."""

import json
from datetime import datetime, timezone
from pathlib import Path

from backend.cache.cache_keys import generate_cache_key
from backend.cache.disk_cache import DiskCache
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Assuming cache lives in project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CACHE_DIR = PROJECT_ROOT / "data" / ".cache"


class CacheManager:
    """Manages cache directories, metadata, and invalidation."""

    def __init__(
        self,
        dataset_hash: str,
        schema_version: str = "1.0",
        cache_version: str = "1.0",
        base_dir: Path = DEFAULT_CACHE_DIR,
    ) -> None:
        """Initialize the cache manager and automatically handle staleness."""
        self.dataset_hash = dataset_hash
        self.schema_version = schema_version
        self.cache_version = cache_version
        self.base_dir = base_dir

        self.metadata_path = self.base_dir / "metadata.json"
        self._ensure_cache_validity()

        # Initialize specific namespace caches
        self.embeddings = DiskCache(self.base_dir / "embeddings")
        self.normalized = DiskCache(self.base_dir / "normalized")
        self.parsed = DiskCache(self.base_dir / "parsed")
        self.rankings = DiskCache(self.base_dir / "rankings")

    def _ensure_cache_validity(self) -> None:
        """Check if cache is stale based on metadata, clear if needed."""
        self.base_dir.mkdir(parents=True, exist_ok=True)

        is_stale = True
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)

                if (
                    meta.get("dataset_hash") == self.dataset_hash
                    and meta.get("schema_version") == self.schema_version
                    and meta.get("cache_version") == self.cache_version
                ):
                    is_stale = False
            except Exception:
                logger.warning("Failed to read cache metadata. Invalidating cache.")

        if is_stale:
            logger.info("Cache is stale or missing. Clearing cache.")
            self._clear_all_caches()
            self._write_metadata()
        else:
            logger.debug("Cache is valid.")

    def _clear_all_caches(self) -> None:
        """Remove all subdirectories and files in the cache base dir."""
        for item in self.base_dir.rglob("*"):
            if item.is_file() and item.name != "metadata.json":
                try:
                    item.unlink()
                except OSError:
                    pass
        # Note: directories are kept, just emptied.

    def _write_metadata(self) -> None:
        """Write current metadata to file."""
        metadata = {
            "dataset_hash": self.dataset_hash,
            "schema_version": self.schema_version,
            "cache_version": self.cache_version,
            "creation_timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    def get_key(self, identifier: str) -> str:
        """Generate a cache key bound to current cache version."""
        return generate_cache_key(identifier, self.cache_version)
