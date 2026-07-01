import sys
import os
import time
from pathlib import Path
from unittest.mock import patch

# Mock the LLM to avoid quota/credit errors during demonstration
def mock_generate_structured(*args, **kwargs):
    time.sleep(0.1) # Simulate network delay
    schema = args[2] if len(args) > 2 else kwargs.get('response_schema')
    if schema.__name__ == "JobRequirements":
        return schema(
            required_skills=["python"], 
            preferred_skills=["aws"],
            seniority="Mid",
            experience_band_min=3.0,
            experience_band_max=5.0,
            core_responsibilities=["dev"]
        )
    elif schema.__name__ == "RecruiterEvaluation":
        # Extract candidate_id from args[1] (which is the user_prompt containing the resume)
        # For simplicity, we just grab it from kwargs if possible, or use a dummy
        return schema(
            candidate_id="mock_id", # This gets overridden by the agent using evidence_pkg.candidate_id anyway
            fit_score=85.0,
            strengths=["coding"],
            gaps=["none"],
            reasoning="great fit"
        )
    elif schema.__name__ == "CriticReview":
        return schema(
            candidate_id="mock_id",
            original_fit_score=85.0,
            adjusted_fit_score=82.0,
            adjustment_reasoning="adjusted",
            is_hallucination_detected=False
        )
    return None

def run_demo():
    print("=== Production Fault Tolerance Upgrade Demonstration ===")
    import shutil
    out_dir = Path("output/checkpoints")
    if out_dir.exists():
        shutil.rmtree(out_dir)
        
    print("\n1. Fresh Execution (Interrupted after 2 candidates)")
    evals_completed = 0
    def mock_crashing_structured(*args, **kwargs):
        nonlocal evals_completed
        schema = args[2] if len(args) > 2 else kwargs.get('response_schema')
        if schema.__name__ == "RecruiterEvaluation":
            evals_completed += 1
            if evals_completed == 3:
                print("\n[SIMULATED FATAL ERROR] System crashing after 2 candidates completed!")
                raise KeyboardInterrupt("Simulated Crash")
        return mock_generate_structured(*args, **kwargs)

    with patch('backend.llm.client.LLMClient.generate_structured', side_effect=mock_crashing_structured):
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scripts.run_pipeline import main
        
        # Override sys.argv
        sys.argv = [
            "run_pipeline.py",
            "--dataset", "data/raw/candidates.jsonl",
            "--job-dir", "data/raw",
            "--job-id", "job_description",
            "--index-dir", "data/index",
            "--output-dir", "output",
            "--top-k", "4",
            "--top-n", "3"
        ]
        
        try:
            main()
        except KeyboardInterrupt:
            print("Pipeline interrupted successfully.")
            
    print("\nVerifying Checkpoints exist...")
    print(f"- pipeline_state.json exists: {Path('output/checkpoints/pipeline_state.json').exists()}")
    print(f"- recruiter_evals.jsonl exists: {Path('output/checkpoints/recruiter_evals.jsonl').exists()}")
    
    print("\n2. Resuming Execution...")
    with patch('backend.llm.client.LLMClient.generate_structured', side_effect=mock_generate_structured):
        try:
            main()
            print("Pipeline finished successfully.")
        except Exception as e:
            print(f"Error during resume: {e}")
            
    print("\n3. Validation Results:")
    xml_exists = Path('output/submission.xml').exists()
    bench_exists = Path('output/benchmark_report.json').exists()
    print(f"- Final XML generated: {xml_exists}")
    print(f"- Benchmark report generated: {bench_exists}")
    
    print("\nCheckpoints state:")
    import json
    with open("output/checkpoints/recruiter_evals.jsonl") as f:
        print(f"Total recruiter evaluations saved: {len(f.readlines())}")
    with open("output/checkpoints/critic_evals.jsonl") as f:
        print(f"Total critic evaluations saved: {len(f.readlines())}")
        
    print("\nArchitecture remains frozen. Only execution reliability was added.")

if __name__ == "__main__":
    run_demo()
