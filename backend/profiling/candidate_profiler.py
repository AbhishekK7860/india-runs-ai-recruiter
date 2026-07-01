"""Candidate profiler module."""

from backend.domain.normalized_candidate import NormalizedCandidate
from backend.profiling.dataset_statistics import DatasetProfile
from backend.schemas.candidate import CandidateProfile


class CandidateProfiler:
    """Profiles a stream of candidates to generate dataset statistics."""

    def __init__(self) -> None:
        """Initialize the profiler."""
        self.stats = DatasetProfile()

    def record_malformed(self) -> None:
        """Record a malformed record."""
        self.stats.malformed_records += 1

    def record_skipped(self) -> None:
        """Record a skipped record."""
        self.stats.skipped_records += 1

    def profile_raw(self, candidate: CandidateProfile) -> None:
        """Profile raw candidate data."""
        self.stats.total_records += 1

        # Check missing values
        if not candidate.current_role:
            self.stats.missing_values["current_role"] += 1
        if not candidate.skills:
            self.stats.missing_values["skills"] += 1
        if not candidate.education:
            self.stats.missing_values["education"] += 1
        if not candidate.resume_text:
            self.stats.missing_values["resume_text"] += 1

    def profile_normalized(self, candidate: NormalizedCandidate) -> None:
        """Profile normalized candidate data."""
        if candidate.canonical_title:
            self.stats.title_frequencies[candidate.canonical_title] += 1
        else:
            self.stats.unknown_values["title"] += 1

        if candidate.canonical_industry:
            self.stats.industry_frequencies[candidate.canonical_industry] += 1

        for skill in candidate.canonical_skills:
            self.stats.skill_frequencies[skill] += 1

    def generate_report(self, output_path: str) -> None:
        """Generate and save the profiling report.

        Args:
            output_path: The file path to save the JSON report.
        """
        self.stats.save(output_path)
