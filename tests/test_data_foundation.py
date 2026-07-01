"""Tests for the data foundation layer."""

import json
from pathlib import Path

import pytest

from backend.cache.cache_manager import CacheManager
from backend.parser.candidate_loader import StreamingCandidateLoader
from backend.profiling.candidate_profiler import CandidateProfiler
from backend.semantic_foundation.aliases import SkillAliasResolver
from backend.semantic_foundation.title_normalizer import TitleNormalizer
from backend.services.data_pipeline import DataPipeline


@pytest.fixture
def mock_dataset(tmp_path: Path) -> Path:
    """Fixture to create a dummy JSONL dataset."""
    dataset_file = tmp_path / "candidates.jsonl"
    candidates = [
        {
            "candidate_id": "c1",
            "name": "Alice",
            "skills": ["ML", "Python"],
            "experience_years": 5.0,
            "current_role": "SDE",
            "projects": [],
            "education": "B.Tech",
            "resume_text": "Experienced software engineer",
        },
        {
            "candidate_id": "c2",
            "name": "Bob",
            "skills": [],
            "experience_years": 2.0,
            "current_role": "",
            "projects": [],
            "education": "",
            "resume_text": "",
        },
        # Malformed record (missing candidate_id)
        {"name": "Charlie", "skills": ["Java"]},
    ]
    with open(dataset_file, "w") as f:
        for c in candidates:
            f.write(json.dumps(c) + "\n")
    return dataset_file


def test_skill_alias_resolver():
    """Test skill alias resolution."""
    resolver = SkillAliasResolver()
    # Assuming config is loaded, "ML" -> "Machine Learning"
    assert resolver.resolve("ML") == "Machine Learning"
    # Unknown skill remains unknown
    assert resolver.resolve("UnknownSkill") == "UnknownSkill"


def test_title_normalizer():
    """Test title normalization."""
    normalizer = TitleNormalizer()
    # Assuming config is loaded, "SDE" -> "Software Engineer"
    assert normalizer.normalize("SDE") == "Software Engineer"
    assert normalizer.normalize("Unknown Title") is None


def test_streaming_loader(mock_dataset: Path):
    """Test candidate loader."""
    profiler = CandidateProfiler()
    loader = StreamingCandidateLoader(profiler=profiler)

    candidates = list(loader.parse(mock_dataset))
    assert len(candidates) == 3
    assert candidates[0].candidate_id == "c1"

    # 3 total records, 2 valid, 1 malformed
    assert profiler.stats.total_records == 3

    assert candidates[0].candidate_id == "c1"


def test_data_pipeline(tmp_path: Path, mock_dataset: Path):
    """Test the end-to-end data pipeline with dummy data."""
    cache_manager = CacheManager(
        dataset_hash="dummy_hash", base_dir=tmp_path / ".cache"
    )
    job_dir = tmp_path / "jobs"
    job_dir.mkdir()

    pipeline = DataPipeline(cache_manager, mock_dataset, job_dir)

    normalized = list(pipeline.stream_candidates())
    assert len(normalized) == 3

    # The first candidate might be the malformed one (c1)
    # Let's find Alice and Bob by ID
    alice = next(c for c in normalized if c.candidate_id == "c1")
    bob = next(c for c in normalized if c.candidate_id == "c2")

    assert alice.canonical_title == "Software Engineer"
    assert bob.canonical_title is None
    assert "Machine Learning" in alice.canonical_skills
    assert alice.quality_score > bob.quality_score

    # Check cache
    alice_key = cache_manager.get_key("c1")
    cached = cache_manager.normalized.read(alice_key)
    assert cached is not None
    assert cached["canonical_title"] == "Software Engineer"
