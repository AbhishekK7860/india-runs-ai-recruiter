"""Tests for the Final Phase components."""

from pathlib import Path

import pytest

from backend.reporting.explainer import RankingExplainer
from backend.schemas.llm import CriticReview, RecruiterEvaluation
from backend.submission.validator import SubmissionValidationError, SubmissionValidator
from backend.submission.xml_generator import XMLGenerator


def test_explainer(tmp_path: Path):
    """Test explainability report generation."""
    explainer = RankingExplainer()
    
    candidates = [
        {
            "candidate_id": "cand_1",
            "rank": 1,
            "final_score": 95.0,
            "semantic_score": 0.9,
            "behaviour_score": 1.0,
            "recruiter_evaluation": RecruiterEvaluation(
                candidate_id="cand_1",
                fit_score=95.0,
                strengths=["Python", "Leadership"],
                gaps=["None"],
                reasoning="Great fit."
            ),
            "critic_review": CriticReview(
                candidate_id="cand_1",
                original_fit_score=95.0,
                adjusted_fit_score=95.0,
                adjustment_reasoning="Accurate.",
                is_hallucination_detected=False
            )
        }
    ]
    
    explainer.generate_report(candidates, tmp_path)
    report_file = tmp_path / "explainability_report.md"
    assert report_file.exists()
    
    content = report_file.read_text(encoding="utf-8")
    assert "cand_1" in content
    assert "Great fit." in content
    assert "Accurate." in content


def test_xml_generation_and_validation(tmp_path: Path):
    """Test generating XML and validating it strictly."""
    generator = XMLGenerator()
    validator = SubmissionValidator()
    
    # We must generate exactly 50 candidates to pass validation
    candidates = []
    for i in range(1, 51):
        candidates.append({
            "candidate_id": f"cand_{i}",
            "rank": i,
            "final_score": 100.0 - i
        })
        
    xml_path = generator.generate(candidates, tmp_path)
    assert xml_path.exists()
    
    # Validation should pass
    assert validator.validate(xml_path) is True
    
    # Test validation failure with missing node
    missing_candidates = candidates[:-1]  # 49 candidates
    xml_path_fail = generator.generate(missing_candidates, tmp_path / "fail")
    
    with pytest.raises(SubmissionValidationError):
        validator.validate(xml_path_fail)
