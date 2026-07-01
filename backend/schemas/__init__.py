"""Schemas package init."""

from backend.schemas.behaviour import BehaviourSignal
from backend.schemas.candidate import CandidateProfile
from backend.schemas.job import JobRequirement
from backend.schemas.ranking import RankedCandidate
from backend.schemas.submission import XMLSubmission

__all__ = [
    "BehaviourSignal",
    "CandidateProfile",
    "JobRequirement",
    "RankedCandidate",
    "XMLSubmission",
]
