"""Tests for CandidateMapper."""

import pytest

from backend.parser.candidate_mapper import CandidateMapper


@pytest.fixture
def mapper():
    return CandidateMapper()


def test_valid_candidate_mapping(mapper):
    raw = {
        "candidate_id": "C123",
        "profile": {
            "anonymized_name": "John Doe",
            "years_of_experience": 5.5,
            "current_title": "Software Engineer",
            "summary": "Experienced dev"
        },
        "skills": [{"name": "Python"}, {"name": "Go"}],
        "education": [{"degree": "B.Sc", "field_of_study": "CS"}],
        "career_history": [{"title": "Dev", "company": "Tech Corp", "start_date": "2020", "end_date": "2023"}],
        "redrob_signals": {"github_activity_score": 85.0}
    }
    
    result = mapper.map(raw)
    
    assert result["candidate_id"] == "C123"
    assert result["name"] == "John Doe"
    assert result["experience_years"] == 5.5
    assert result["current_role"] == "Software Engineer"
    assert result["skills"] == ["Python", "Go"]
    assert "B.Sc CS" in result["education"]
    assert "Experienced dev" in result["resume_text"]
    assert "Dev at Tech Corp (2020 to 2023)" in result["resume_text"]
    assert result["behaviour_signals"]["github_activity_score"] == 85.0


def test_missing_optional_fields(mapper):
    raw = {"candidate_id": "C124"}
    result = mapper.map(raw)
    
    assert result["candidate_id"] == "C124"
    assert result["name"] == "Unknown Candidate"
    assert result["experience_years"] == 0.0
    assert result["skills"] == []
    assert result["education"] == "No education provided"


def test_missing_required_fields(mapper):
    raw = {}
    result = mapper.map(raw)
    
    assert result["candidate_id"] == "UNKNOWN_ID"
    assert result["name"] == "Unknown Candidate"
    assert result["experience_years"] == 0.0


def test_malformed_skills(mapper):
    raw = {
        "candidate_id": "C125",
        "skills": [{"wrong_key": "val"}, "Valid String", None, {"name": None}]
    }
    result = mapper.map(raw)
    
    assert result["skills"] == ["Valid String"]


def test_malformed_education(mapper):
    raw = {
        "candidate_id": "C126",
        "education": ["Not a dict", None, {"degree": "B.A"}]
    }
    result = mapper.map(raw)
    
    assert result["education"] == "B.A"


def test_malformed_career_history(mapper):
    raw = {
        "candidate_id": "C127",
        "career_history": ["Not a dict", None, {"title": "Dev"}]
    }
    result = mapper.map(raw)
    
    assert "Dev at Unknown Company ( to Present)" in result["resume_text"]


def test_malformed_json_types(mapper):
    raw = {
        "candidate_id": "C128",
        "profile": "Not a dict",
        "skills": "Not a list",
        "education": "Not a list",
        "career_history": "Not a list",
        "redrob_signals": "Not a dict"
    }
    result = mapper.map(raw)
    
    assert result["name"] == "Unknown Candidate"
    assert result["experience_years"] == 0.0
    assert result["skills"] == []
    assert result["education"] == "No education provided"
    assert result["behaviour_signals"]["github_activity_score"] == -1.0
