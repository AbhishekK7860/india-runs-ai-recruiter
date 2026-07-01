"""Pytest tests for Pydantic schema correctness.

Covers: valid instantiation, to_xml() output format, missing required
field validation, and invalid enum value validation.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from backend.schemas.candidate import CandidateProfile
from backend.schemas.job import JobRequirement
from backend.schemas.ranking import RankedCandidate
from backend.schemas.submission import XMLSubmission

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_JOB_DATA: dict = {
    "job_id": "JOB_001",
    "title": "Senior Data Engineer",
    "description": "Looking for a senior data engineer with 5+ years of experience.",
    "required_skills": ["Python", "Spark", "SQL"],
    "preferred_skills": ["Airflow", "dbt"],
    "min_experience_years": 5,
    "seniority_level": "senior",
    "created_at": datetime(2026, 1, 1, 0, 0, 0),
}

VALID_CANDIDATE_DATA: dict = {
    "candidate_id": "CAND_0000001",
    "name": "Ira Vora",
    "skills": ["Python", "Spark", "SQL", "Airflow"],
    "experience_years": 6.9,
    "current_role": "Backend Engineer",
    "projects": ["Real-time pipeline", "Warehouse redesign"],
    "education": "B.E. Computer Science, LPU",
    "resume_text": "Experienced backend engineer with data pipeline expertise.",
}


# ---------------------------------------------------------------------------
# Task 8: Schema tests
# ---------------------------------------------------------------------------


def test_candidate_profile_valid() -> None:
    """CandidateProfile instantiates without error given valid data."""
    profile = CandidateProfile(**VALID_CANDIDATE_DATA)
    assert profile.candidate_id == "CAND_0000001"
    assert profile.experience_years == 6.9
    assert "Python" in profile.skills


def test_job_requirement_valid() -> None:
    """JobRequirement instantiates without error given valid data."""
    job = JobRequirement(**VALID_JOB_DATA)
    assert job.job_id == "JOB_001"
    assert job.seniority_level == "senior"
    assert job.min_experience_years == 5


def test_xml_submission_to_xml() -> None:
    """to_xml() returns a string containing required top-level XML tags."""
    candidate = RankedCandidate(
        rank=1,
        candidate_id="CAND_0000001",
        semantic_score=0.92,
        behaviour_score=0.85,
        reasoning="Strong match on required skills and experience.",
        confidence=0.88,
    )
    submission = XMLSubmission(
        job_id="JOB_001",
        generated_at=datetime(2026, 6, 1, 12, 0, 0),
        candidates=[candidate],
    )
    result = submission.to_xml()

    assert isinstance(result, str)
    assert "<submission>" in result
    assert "<candidates>" in result
    assert "JOB_001" in result


def test_candidate_profile_missing_required_field() -> None:
    """Missing a required field on CandidateProfile raises ValidationError."""
    data = {k: v for k, v in VALID_CANDIDATE_DATA.items() if k != "candidate_id"}
    with pytest.raises(ValidationError):
        CandidateProfile(**data)


def test_job_requirement_missing_required_field() -> None:
    """Missing a required field on JobRequirement raises ValidationError."""
    data = {k: v for k, v in VALID_JOB_DATA.items() if k != "title"}
    with pytest.raises(ValidationError):
        JobRequirement(**data)


def test_job_requirement_invalid_seniority() -> None:
    """An invalid seniority_level value raises ValidationError."""
    data = {**VALID_JOB_DATA, "seniority_level": "executive"}
    with pytest.raises(ValidationError):
        JobRequirement(**data)
