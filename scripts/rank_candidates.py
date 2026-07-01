"""Candidate ranking orchestrator for Phase 3."""

import argparse
import sys
from pathlib import Path

from backend.agents.behaviour_analyst import BehaviourAnalystAgent
from backend.agents.critic_agent import CriticAgent
from backend.agents.jd_analyst import JDAnalystAgent
from backend.agents.ranking_agent import RankingAgent
from backend.agents.ranking_strategy import WeightedFusionStrategy
from backend.agents.recruiter_agent import RecruiterAgent
from backend.agents.security_filter import SecurityFilter, SecurityViolation
from backend.cache.cache_manager import CacheManager
from backend.domain.normalized_candidate import NormalizedCandidate
from backend.embeddings.encoder import TextEncoder
from backend.llm.client import LLMClient
from backend.repositories.candidate_repository import FileCandidateRepository
from backend.retrieval.searcher import SemanticSearcher
from backend.schemas.candidate import CandidateProfile
from backend.schemas.llm import EvidencePackage
from backend.services.data_pipeline import DataPipeline
from backend.services.evidence_builder import EvidenceBuilder
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def _load_top_profiles(
    dataset_path: Path, top_ids: set[str]
) -> dict[str, CandidateProfile]:
    """Stream dataset and only return the CandidateProfiles that match top_ids."""
    repo = FileCandidateRepository(dataset_path)
    matched = {}
    for profile in repo.get_all():
        if profile.candidate_id in top_ids:
            matched[profile.candidate_id] = profile
            if len(matched) == len(top_ids):
                break
    return matched


def main():
    """Run the complete LLM ranking pipeline."""
    from backend.core.settings import get_settings
    settings = get_settings()
    
    parser = argparse.ArgumentParser(description="Phase 3 LLM Candidate Ranking")
    parser.add_argument("--dataset", type=str, required=True, help="JSONL dataset")
    parser.add_argument("--job-dir", type=str, required=True, help="Jobs directory")
    parser.add_argument(
        "--job-id", type=str, required=True, help="Job ID to rank against"
    )
    parser.add_argument(
        "--index-dir", type=str, default="data/index", help="FAISS index dir"
    )
    parser.add_argument(
        "--top-k", type=int, default=settings.MAX_CANDIDATES_FAISS, help="Retrieval Top-K"
    )
    parser.add_argument("--top-n", type=int, default=settings.MAX_CANDIDATES_LLM, help="Critic Top-N to review")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    job_dir = Path(args.job_dir)

    # Initialize Core Services
    cache_manager = CacheManager(dataset_hash="manual_run")
    pipeline = DataPipeline(cache_manager, dataset_path, job_dir)
    encoder = TextEncoder(cache=cache_manager.embeddings)
    searcher = SemanticSearcher(encoder, args.index_dir)
    llm_client = LLMClient()

    # Initialize Agents
    jd_analyst = JDAnalystAgent(llm_client)
    security_filter = SecurityFilter()
    evidence_builder = EvidenceBuilder()
    recruiter = RecruiterAgent(llm_client)
    critic = CriticAgent(llm_client)
    behaviour_analyst = BehaviourAnalystAgent()
    ranking_agent = RankingAgent(WeightedFusionStrategy())

    # 1. Process Job
    logger.info(f"Processing job {args.job_id}...")
    job = pipeline.process_job(args.job_id)

    # 2. Extract JD via LLM
    job_reqs = jd_analyst.analyze(job.description)

    # 3. Retrieve Top-K from FAISS
    logger.info(f"Retrieving top {args.top_k} candidates from FAISS...")
    search_results = searcher.search(job, top_k=args.top_k)
    top_ids = {res.candidate_id for res in search_results}

    if not top_ids:
        logger.error("No candidates retrieved. Did you build the index?")
        sys.exit(1)

    # 4. Load Raw Profiles & Normalized Data
    logger.info("Extracting raw profiles and normalized domain objects...")
    raw_profiles = _load_top_profiles(dataset_path, top_ids)

    candidates_data = []
    for res in search_results:
        cid = res.candidate_id
        # Get NormalizedCandidate from cache
        cache_key = cache_manager.get_key(cid)
        cached_data = cache_manager.normalized.read(cache_key)
        if not cached_data:
            logger.warning(f"Cache miss for {cid}. Skipping.")
            continue

        norm_cand = NormalizedCandidate.model_validate(cached_data)
        raw_prof = raw_profiles.get(cid)
        if not raw_prof:
            continue

        candidates_data.append((norm_cand, raw_prof, res.score))

    # 5. Evaluate (Security -> Evidence -> Recruiter)
    evaluations = []
    for norm_cand, raw_prof, semantic_score in candidates_data:
        try:
            safe_text = security_filter.verify_safe(
                norm_cand.resume_text, norm_cand.candidate_id
            )
        except SecurityViolation:
            continue

        b_score = behaviour_analyst.analyze(raw_prof)
        evidence = evidence_builder.build_package(
            norm_cand, semantic_score, b_score, safe_text
        )

        # We parse the evidence dict into a proper EvidencePackage pydantic model
        evidence_pkg = EvidencePackage.model_validate(evidence)

        logger.debug(f"Evaluating candidate {norm_cand.candidate_id}...")
        rec_eval = recruiter.evaluate(evidence_pkg, job_reqs)
        evaluations.append((evidence_pkg, rec_eval))

    # 6. Critic Review (Only top-N)
    # Sort initially by recruiter fit_score to find top N
    evaluations.sort(key=lambda x: x[1].fit_score, reverse=True)

    final_candidates_for_ranking = []
    for i, (evidence_pkg, rec_eval) in enumerate(evaluations):
        if i < args.top_n:
            logger.debug(f"Critic reviewing candidate {evidence_pkg.candidate_id}...")
            critic_rev = critic.review(rec_eval, evidence_pkg, job_reqs)
            final_candidates_for_ranking.append((evidence_pkg, critic_rev))
        else:
            # Fallback to empty critic review, but score is based solely on semantic/behaviour + 0 LLM score
            # Or we can just drop candidates outside the top N? The funnel says "Critic review of Top-100".
            # For this script, we'll just not include them in the final ranked list.
            pass

    # 7. Final Ranking Fusion
    ranked = ranking_agent.rank(final_candidates_for_ranking)

    logger.info("=== FINAL RANKING ===")
    for cand in ranked:
        logger.info(
            f"Rank {cand['rank']}: ID={cand['candidate_id']} | "
            f"Final={cand['final_score']} (Sem={cand['semantic_score']:.2f}, "
            f"Beh={cand['behaviour_score']:.2f}, LLM={cand['llm_fit_score']})"
        )


if __name__ == "__main__":
    main()
