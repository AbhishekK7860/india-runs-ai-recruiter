"""Low-level disk cache operations."""

from pathlib import Path
from typing import Any

import orjson


class DiskCache:
    """Handles raw file system reads and writes for the cache."""

    def __init__(self, base_dir: Path) -> None:
        """Initialize the disk cache.

        Args:
            base_dir: The root directory for the cache.
        """
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def write(self, key: str, data: dict[str, Any]) -> None:
        """Write JSON data to the cache.

        Args:
            key: The cache key (filename).
            data: The dictionary to write.
        """
        file_path = self.base_dir / f"{key}.json"
        with open(file_path, "wb") as f:
            f.write(orjson.dumps(data))

    def read(self, key: str) -> dict[str, Any] | None:
        """Read JSON data from the cache.

        Args:
            key: The cache key (filename).

        Returns:
            The parsed JSON dict, or None if it doesn't exist.
        """
        file_path = self.base_dir / f"{key}.json"
        if not file_path.exists():
            return None

        try:
            with open(file_path, "rb") as f:
                return orjson.loads(f.read())
        except orjson.JSONDecodeError:
            return None

    def clear(self) -> None:
        """Delete all cached files in the base directory."""
        for file_path in self.base_dir.glob("*.json"):
            try:
                file_path.unlink()
            except OSError:
                pass
