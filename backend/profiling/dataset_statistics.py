"""Dataset statistics models."""

from collections import Counter
from pathlib import Path

from pydantic import BaseModel, Field


class DatasetProfile(BaseModel):
    """Statistics about the dataset."""

    total_records: int = 0
    malformed_records: int = 0
    skipped_records: int = 0
    missing_values: Counter[str] = Field(default_factory=Counter)
    title_frequencies: Counter[str] = Field(default_factory=Counter)
    skill_frequencies: Counter[str] = Field(default_factory=Counter)
    industry_frequencies: Counter[str] = Field(default_factory=Counter)
    country_frequencies: Counter[str] = Field(default_factory=Counter)
    unknown_values: Counter[str] = Field(default_factory=Counter)

    def to_json(self) -> str:
        """Convert statistics to a JSON string."""
        return self.model_dump_json(indent=2)

    def save(self, output_path: str | Path) -> None:
        """Save the profile to a JSON file."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
