"""Metadata store for vector retrieval."""

import json
from pathlib import Path


class MetadataStore:
    """Manages the mapping between FAISS integer IDs and candidate string IDs."""

    def __init__(self, store_path: str | Path | None = None) -> None:
        """Initialize the metadata store.

        Args:
            store_path: Optional path to load existing metadata from JSON.
        """
        self._id_to_candidate: dict[int, str] = {}
        self._candidate_to_id: dict[str, int] = {}
        self._next_id = 0

        if store_path and Path(store_path).exists():
            self.load(store_path)

    def add(self, candidate_id: str) -> int:
        """Add a candidate ID and return its assigned integer ID."""
        if candidate_id in self._candidate_to_id:
            return self._candidate_to_id[candidate_id]

        current_id = self._next_id
        self._id_to_candidate[current_id] = candidate_id
        self._candidate_to_id[candidate_id] = current_id
        self._next_id += 1
        return current_id

    def get_candidate_id(self, faiss_id: int) -> str | None:
        """Retrieve a candidate string ID by its FAISS integer ID."""
        return self._id_to_candidate.get(faiss_id)

    def save(self, path: str | Path) -> None:
        """Save the metadata store to disk."""
        data = {"id_to_candidate": self._id_to_candidate, "next_id": self._next_id}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def load(self, path: str | Path) -> None:
        """Load the metadata store from disk."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # JSON keys are strings, convert back to int
        self._id_to_candidate = {int(k): v for k, v in data["id_to_candidate"].items()}
        self._next_id = data["next_id"]
        self._candidate_to_id = {v: k for k, v in self._id_to_candidate.items()}
