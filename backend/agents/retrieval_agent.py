"""Retrieval Agent module."""

from backend.domain.normalized_job import NormalizedJob
from backend.retrieval.searcher import SearchResult, SemanticSearcher
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class RetrievalAgent:
    """Agent responsible for finding top candidates for a job description."""

    def __init__(self, searcher: SemanticSearcher) -> None:
        """Initialize the agent with a semantic searcher.

        Args:
            searcher: The SemanticSearcher instance connected to the FAISS index.
        """
        self.searcher = searcher

    def find_candidates(
        self, job: NormalizedJob, top_k: int = 500
    ) -> list[SearchResult]:
        """Find the top-K candidates that match the given job requirement.

        Args:
            job: The normalized job to search against.
            top_k: The number of candidates to retrieve.

        Returns:
            A list of SearchResult objects (candidate_id, score) sorted by relevance.
        """
        logger.info(f"Retrieving top {top_k} candidates for job {job.job_id}...")
        results = self.searcher.search(job, top_k=top_k)
        logger.info(f"Retrieved {len(results)} candidates.")
        return results
