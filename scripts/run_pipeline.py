"""End-to-End Orchestrator for the India Runs AI Recruiter Pipeline."""

import argparse
import sys
import time
from pathlib import Path

# Add psutil for peak memory measurement if available
try:
    import psutil
except ImportError:
    psutil = None

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
from backend.evaluation.benchmark_suite import PipelineBenchmarkSuite
from backend.llm.client import LLMClient
from backend.reporting.explainer import RankingExplainer
from backend.repositories.candidate_repository import FileCandidateRepository
from backend.retrieval.searcher import SemanticSearcher
from backend.schemas.candidate import CandidateProfile
from backend.schemas.llm import EvidencePackage
from backend.services.data_pipeline import DataPipeline
from backend.services.evidence_builder import EvidenceBuilder
from backend.submission.validator import SubmissionValidationError, SubmissionValidator
from backend.submission.xml_generator import XMLGenerator
from backend.utils.logger import get_logger
from backend.utils.checkpointer import Checkpointer
from backend.schemas.llm import RecruiterEvaluation, CriticReview

logger = get_logger(__name__)


def _load_top_profiles(dataset_path: Path, top_ids: set[str]) -> dict[str, CandidateProfile]:
    """Stream dataset and only return CandidateProfiles that match top_ids."""
    repo = FileCandidateRepository(dataset_path)
    matched = {}
    for profile in repo.get_all():
        if profile.candidate_id in top_ids:
            matched[profile.candidate_id] = profile
            if len(matched) == len(top_ids):
                break
    return matched


def _get_memory_usage() -> float:
    """Return memory usage in MB if psutil is available."""
    if psutil:
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    return 0.0


def main():
    """Execute the end-to-end pipeline."""
    from backend.core.settings import get_settings
    settings = get_settings()
    
    parser = argparse.ArgumentParser(description="End-to-End AI Recruiter Pipeline")
    parser.add_argument("--dataset", type=str, required=True, help="JSONL dataset")
    parser.add_argument("--job-dir", type=str, required=True, help="Jobs directory")
    parser.add_argument("--job-id", type=str, required=True, help="Job ID to rank against")
    parser.add_argument("--index-dir", type=str, default="data/index", help="FAISS index dir")
    parser.add_argument("--output-dir", type=str, default="output", help="Output directory")
    parser.add_argument("--top-k", type=int, default=settings.MAX_CANDIDATES_FAISS, help="Retrieval Top-K")
    parser.add_argument("--top-n", type=int, default=settings.MAX_CANDIDATES_LLM, help="Critic Top-N to review")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    job_dir = Path(args.job_dir)
    output_dir = Path(args.output_dir)
    
    # Checkpointer and Resume Logic
    checkpointer = Checkpointer(output_dir)
    current_state = checkpointer.generate_state(
        dataset_path=dataset_path,
        faiss_dir=Path(args.index_dir),
        prompts_yaml=Path("configs/prompts.yaml"),
        provider=settings.LLM_PROVIDER,
        model=settings.OPENROUTER_MODEL if settings.LLM_PROVIDER == "openrouter" else settings.GOOGLE_MODEL
    )
    if not checkpointer.verify_state(current_state):
        logger.error("FATAL: Pipeline state mismatch. Cannot resume. Please clear output/checkpoints/ to start a fresh run.")
        sys.exit(1)
    
    recruiter_checkpoints = checkpointer.load_recruiter_evals()
    critic_checkpoints = checkpointer.load_critic_evals()
    
    # Initialize benchmark suite
    benchmark = PipelineBenchmarkSuite()
    t_start_total = time.perf_counter()
    peak_memory = _get_memory_usage()
    
    # Initialize Core Services
    cache_manager = CacheManager(dataset_hash="manual_build", base_dir=Path("data/.cache"))
    pipeline = DataPipeline(cache_manager, dataset_path, job_dir)
    encoder = TextEncoder(cache=cache_manager.embeddings)
    searcher = SemanticSearcher(encoder, args.index_dir)
    llm_client = LLMClient()
    
    # Initialize Agents & Output Formats
    jd_analyst = JDAnalystAgent(llm_client)
    security_filter = SecurityFilter()
    evidence_builder = EvidenceBuilder()
    recruiter = RecruiterAgent(llm_client)
    critic = CriticAgent(llm_client)
    behaviour_analyst = BehaviourAnalystAgent()
    ranking_agent = RankingAgent(WeightedFusionStrategy())
    explainer = RankingExplainer()
    xml_generator = XMLGenerator()
    validator = SubmissionValidator()
    
    # --- Pipeline Execution ---
    
    # 1. Parsing and Normalization
    logger.info(f"Processing job {args.job_id}...")
    t_parse_start = time.perf_counter()
    job = pipeline.process_job(args.job_id)
    benchmark.update("parsing_time_sec", time.perf_counter() - t_parse_start)
    peak_memory = max(peak_memory, _get_memory_usage())
    
    # 2. JD Extraction (Embedding / Analysis)
    t_jd_start = time.perf_counter()
    job_reqs = jd_analyst.analyze(job.description)
    benchmark.update("embedding_time_sec", time.perf_counter() - t_jd_start)
    peak_memory = max(peak_memory, _get_memory_usage())
    
    # 3. Retrieval
    logger.info(f"Retrieving top {args.top_k} candidates from FAISS...")
    t_retrieval_start = time.perf_counter()
    search_results = searcher.search(job, top_k=args.top_k)
    benchmark.update("retrieval_latency_sec", time.perf_counter() - t_retrieval_start)
    peak_memory = max(peak_memory, _get_memory_usage())
    
    top_ids = {res.candidate_id for res in search_results}
    if not top_ids:
        logger.error("No candidates retrieved. Pipeline halted.")
        sys.exit(1)
        
    benchmark.update("total_candidates_processed", len(top_ids))
        
    # 4. Load Raw Profiles & Normalized Data
    logger.info("Extracting raw profiles and normalized domain objects...")
    raw_profiles = _load_top_profiles(dataset_path, top_ids)
    
    candidates_data = []
    for res in search_results:
        cid = res.candidate_id
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
        
    # 5. LLM Evaluation Phase
    t_llm_start = time.perf_counter()
    evaluations = []
    for norm_cand, raw_prof, semantic_score in candidates_data:
        try:
            safe_text = security_filter.verify_safe(norm_cand.resume_text, norm_cand.candidate_id)
        except SecurityViolation:
            continue
            
        b_score = behaviour_analyst.analyze(raw_prof)
        evidence = evidence_builder.build_package(norm_cand, semantic_score, b_score, safe_text)
        evidence_pkg = EvidencePackage.model_validate(evidence)
        
        cid = norm_cand.candidate_id
        if cid in recruiter_checkpoints:
            rec_eval = RecruiterEvaluation.model_validate(recruiter_checkpoints[cid]["evaluation"])
            evaluations.append((evidence_pkg, rec_eval))
            logger.debug(f"Loaded recruiter evaluation for {cid} from checkpoint.")
            continue
            
        logger.debug(f"Evaluating candidate {cid}...")
        rec_eval = recruiter.evaluate(evidence_pkg, job_reqs)
        
        # Checkpoint and save state
        checkpointer.append_recruiter_eval(cid, evidence_pkg.model_dump(), rec_eval.model_dump())
        checkpointer.save_state(current_state)
        
        evaluations.append((evidence_pkg, rec_eval))
        peak_memory = max(peak_memory, _get_memory_usage())
        
    # 6. Critic Review (Top-N)
    evaluations.sort(key=lambda x: x[1].fit_score, reverse=True)
    
    final_candidates_for_ranking = []
    for i, (evidence_pkg, rec_eval) in enumerate(evaluations):
        if i < args.top_n:
            cid = evidence_pkg.candidate_id
            if cid in critic_checkpoints:
                critic_rev = CriticReview.model_validate(critic_checkpoints[cid]["critic_review"])
                final_candidates_for_ranking.append((evidence_pkg, critic_rev))
                logger.debug(f"Loaded critic review for {cid} from checkpoint.")
                continue
                
            logger.debug(f"Critic reviewing candidate {cid}...")
            critic_rev = critic.review(rec_eval, evidence_pkg, job_reqs)
            
            # Checkpoint and save state
            checkpointer.append_critic_eval(cid, critic_rev.model_dump())
            checkpointer.save_state(current_state)
            
            final_candidates_for_ranking.append((evidence_pkg, critic_rev))
        
    # Update LLM latency average
    total_llm_calls = len(evaluations) + min(len(evaluations), args.top_n) + 1 # +1 for JD Analyst
    if total_llm_calls > 0:
        avg_llm_time = (time.perf_counter() - t_llm_start) / total_llm_calls
        benchmark.update("average_llm_latency_sec", avg_llm_time)
        
    # 7. Final Ranking Fusion
    ranked = ranking_agent.rank(final_candidates_for_ranking)
    
    # We must submit exactly MAX_CANDIDATES_FINAL candidates as per rules
    final_n = ranked[:settings.MAX_CANDIDATES_FINAL]
    benchmark.update("final_shortlisted_candidates", len(final_n))
    
    # Re-inject the raw evaluation strings into the final dictionaries for the Explainer
    for cand_dict in final_n:
        cid = cand_dict["candidate_id"]
        # Find matching evaluation and critic review
        for pkg, rev in final_candidates_for_ranking:
            if pkg.candidate_id == cid:
                cand_dict["recruiter_evaluation"] = next(e for p, e in evaluations if p.candidate_id == cid)
                cand_dict["critic_review"] = rev
                break
    
    # 8. Report & XML Generation
    explainer.generate_report(final_n, output_dir)
    xml_path = xml_generator.generate(final_n, output_dir)
    
    # 9. Validation
    try:
        validator.validate(xml_path)
    except SubmissionValidationError as e:
        logger.error(f"FATAL: Final submission validation failed! {e}")
        sys.exit(1)
        
    # Finalize benchmarks
    t_end_total = time.perf_counter()
    benchmark.update("total_execution_time_sec", t_end_total - t_start_total)
    benchmark.update("peak_memory_usage_mb", peak_memory)
    benchmark.generate_report(output_dir)
    
    logger.info("Pipeline execution completed successfully.")

if __name__ == "__main__":
    main()
