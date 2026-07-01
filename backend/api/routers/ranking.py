"""Ranking router (Phase 1 stub).

Provides POST /rank (mounted under /api/v1 by main.py) which accepts a
job description and a list of candidate profiles. In Phase 2+ this endpoint
will invoke the full multi-agent ranking pipeline and return a ranked list.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.schemas.candidate import CandidateProfile
from backend.schemas.job import JobRequirement
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["ranking"])

RANK_ROUTE = "/rank"


class RankingRequest(BaseModel):
    """Request body for the ranking endpoint."""

    job: JobRequirement
    candidates: list[CandidateProfile]


@router.post(RANK_ROUTE)
async def rank_candidates(request: RankingRequest) -> dict:
    """Accept a job and candidate list; return a Phase 2 not-implemented stub.

    Args:
        request: RankingRequest containing one JobRequirement and N CandidateProfiles.

    Returns:
        A dict indicating the endpoint is not yet implemented.
    """
    try:
        logger.info(
            "Ranking request received",
            route=RANK_ROUTE,
            candidate_count=len(request.candidates),
            job_id=request.job.job_id,
        )
        return {"message": "not implemented", "phase": 2}
    except Exception:
        logger.exception(
            "Unexpected error in rank_candidates",
            route=RANK_ROUTE,
        )
        raise
