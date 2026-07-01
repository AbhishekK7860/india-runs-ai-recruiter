"""End-to-end data pipeline service."""

from pathlib import Path
from typing import Iterator

from backend.cache.cache_manager import CacheManager
from backend.domain.normalized_candidate import NormalizedCandidate, QualityScoreDetails
from backend.domain.normalized_job import NormalizedJob
from backend.metrics.counters import counters
from backend.metrics.timers import timers
from backend.profiling.candidate_profiler import CandidateProfiler
from backend.repositories.candidate_repository import FileCandidateRepository
from backend.repositories.job_repository import FileJobRepository
from backend.schemas.candidate import CandidateProfile
from backend.semantic_foundation.ontology import ontology
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class DataPipeline:
    """End-to-end pipeline for data processing."""

    def __init__(
        self,
        cache_manager: CacheManager,
        dataset_path: str | Path,
        job_dir: str | Path,
    ) -> None:
        """Initialize the data pipeline.

        Args:
            cache_manager: The central cache manager instance.
            dataset_path: Path to the raw JSONL candidate dataset.
            job_dir: Path to the directory containing job DOCX files.
        """
        self.cache_manager = cache_manager
        self.dataset_path = Path(dataset_path)
        self.job_dir = Path(job_dir)
        self.profiler = CandidateProfiler()
        self.candidate_repo = FileCandidateRepository(
            self.dataset_path, profiler=self.profiler
        )
        self.job_repo = FileJobRepository(self.job_dir)

    def _calculate_quality_score(
        self, candidate: CandidateProfile, norm_cand: NormalizedCandidate
    ) -> None:
        """Calculate the deterministic data quality score."""
        details = QualityScoreDetails()

        if not candidate.resume_text.strip():
            details.missing_summary = True
            details.total_penalty += 0.3

        if not candidate.education.strip():
            details.missing_education = True
            details.total_penalty += 0.2

        if not candidate.skills:
            details.empty_skills = True
            details.total_penalty += 0.3

        # Example penalty for parsing mismatch or missing canonical fields
        if not norm_cand.canonical_title:
            details.total_penalty += 0.1

        final_score = max(0.0, 1.0 - details.total_penalty)
        norm_cand.quality_details = details
        norm_cand.quality_score = final_score

    def stream_candidates(self) -> Iterator[NormalizedCandidate]:
        """Stream, normalize, and cache candidates end-to-end.

        Yields:
            NormalizedCandidate objects.
        """
        for raw_candidate in self.candidate_repo.get_all():
            with timers.measure("normalization_time"):
                # Normalize Title
                canonical_title = ontology.normalize_title(raw_candidate.current_role)
                # Normalize Skills
                canonical_skills = ontology.normalize_skills(raw_candidate.skills)

                # Currently schemas don't have industry, but if they did we'd map it.
                # Assuming industry is None for now until extracted from
                # resume_text in later AI phase.
                canonical_industry = None

                norm_cand = NormalizedCandidate(
                    candidate_id=raw_candidate.candidate_id,
                    canonical_title=canonical_title,
                    canonical_skills=canonical_skills,
                    canonical_industry=canonical_industry,
                    experience_years=raw_candidate.experience_years,
                    quality_score=1.0,  # placeholder
                    raw_title=raw_candidate.current_role,
                    raw_skills=raw_candidate.skills,
                    resume_text=raw_candidate.resume_text,
                )

                self._calculate_quality_score(raw_candidate, norm_cand)

                # Profile the normalized data
                self.profiler.profile_normalized(norm_cand)

            with timers.measure("cache_time"):
                cache_key = self.cache_manager.get_key(norm_cand.candidate_id)
                self.cache_manager.normalized.write(cache_key, norm_cand.model_dump())

            counters.increment("records_processed")
            yield norm_cand

    def process_job(self, job_id: str) -> NormalizedJob:
        """Process, normalize, and cache a single job description."""
        with timers.measure("job_parsing_time"):
            raw_job = self.job_repo.get(job_id)

        with timers.measure("normalization_time"):
            canonical_title = ontology.normalize_title(raw_job.title)

            norm_job = NormalizedJob(
                job_id=raw_job.job_id,
                canonical_title=canonical_title,
                canonical_required_skills=[],
                canonical_preferred_skills=[],
                canonical_industry=None,
                min_experience_years=raw_job.min_experience_years,
                seniority_level=raw_job.seniority_level,
                raw_title=raw_job.title,
                raw_required_skills=raw_job.required_skills,
                raw_preferred_skills=raw_job.preferred_skills,
                description=raw_job.description,
            )

        with timers.measure("cache_time"):
            cache_key = self.cache_manager.get_key(norm_job.job_id)
            self.cache_manager.normalized.write(cache_key, norm_job.model_dump())

        return norm_job

    def generate_report(self, report_path: str | Path) -> None:
        """Generate the profiling report.

        Args:
            report_path: Path to save the dataset_profile.json
        """
        self.profiler.generate_report(str(report_path))
