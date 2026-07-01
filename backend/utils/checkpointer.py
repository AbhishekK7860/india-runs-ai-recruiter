import json
import os
import hashlib
from pathlib import Path
from typing import Dict, Any

from backend.utils.logger import get_logger

logger = get_logger(__name__)

class Checkpointer:
    """Manages pipeline state and incremental checkpointing of LLM evaluations."""
    
    def __init__(self, output_dir: Path):
        self.checkpoints_dir = output_dir / "checkpoints"
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.checkpoints_dir / "pipeline_state.json"
        self.recruiter_file = self.checkpoints_dir / "recruiter_evals.jsonl"
        self.critic_file = self.checkpoints_dir / "critic_evals.jsonl"

    def _hash_file(self, filepath: Path) -> str:
        """Compute SHA-256 hash of a file for state verification."""
        if not filepath.exists():
            return ""
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def generate_state(self, dataset_path: Path, faiss_dir: Path, prompts_yaml: Path, provider: str, model: str) -> dict:
        """Generate the current pipeline state hash mapping."""
        return {
            "dataset_hash": self._hash_file(dataset_path),
            "faiss_hash": self._hash_file(faiss_dir / "metadata.json"),
            "prompts_hash": self._hash_file(prompts_yaml),
            "provider": provider,
            "model": model
        }

    def verify_state(self, current_state: dict) -> bool:
        """Check if existing pipeline state matches current execution exactly."""
        if not self.state_file.exists():
            return True
            
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                saved_state = json.load(f)
                
            for key in ["dataset_hash", "faiss_hash", "prompts_hash", "provider", "model"]:
                if saved_state.get(key) != current_state.get(key):
                    logger.warning(f"State mismatch on {key}: saved={saved_state.get(key)}, current={current_state.get(key)}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Failed to read pipeline state: {e}")
            return False

    def save_state(self, state: dict):
        """Atomically write pipeline state."""
        temp_file = self.state_file.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
        # Atomic rename (overwrites if exists on POSIX, might need replace on Windows)
        os.replace(temp_file, self.state_file)

    def load_jsonl(self, filepath: Path) -> Dict[str, Any]:
        """Safely load JSONL, ignoring corrupted lines."""
        results = {}
        if not filepath.exists():
            return results
            
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if "candidate_id" in data:
                        results[data["candidate_id"]] = data
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted record at {filepath.name}:{line_no} - ignoring.")
        return results

    def append_jsonl(self, filepath: Path, candidate_id: str, payload: dict):
        """Safely append a single record to JSONL."""
        record = {"candidate_id": candidate_id, **payload}
        line = json.dumps(record) + "\n"
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())

    def load_recruiter_evals(self) -> Dict[str, dict]:
        return self.load_jsonl(self.recruiter_file)
        
    def append_recruiter_eval(self, candidate_id: str, evidence: dict, evaluation: dict):
        self.append_jsonl(self.recruiter_file, candidate_id, {
            "evidence": evidence,
            "evaluation": evaluation
        })

    def load_critic_evals(self) -> Dict[str, dict]:
        return self.load_jsonl(self.critic_file)
        
    def append_critic_eval(self, candidate_id: str, critic_review: dict):
        self.append_jsonl(self.critic_file, candidate_id, {
            "critic_review": critic_review
        })
