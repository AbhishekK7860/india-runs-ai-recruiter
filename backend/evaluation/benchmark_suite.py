"""Benchmark suite for tracking pipeline performance."""

import json
from pathlib import Path
from typing import Any

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class PipelineBenchmarkSuite:
    """Collects and reports end-to-end pipeline metrics."""

    def __init__(self) -> None:
        self.metrics: dict[str, Any] = {
            "total_execution_time_sec": 0.0,
            "parsing_time_sec": 0.0,
            "embedding_time_sec": 0.0,
            "retrieval_latency_sec": 0.0,
            "average_llm_latency_sec": 0.0,
            "peak_memory_usage_mb": 0.0,
            "cache_hit_rate": 0.0,
            "total_candidates_processed": 0,
            "final_shortlisted_candidates": 0,
        }

    def update(self, key: str, value: Any) -> None:
        """Update a specific metric."""
        if key in self.metrics:
            self.metrics[key] = value
        else:
            logger.warning(f"Unknown metric key: {key}")

    def generate_report(self, output_dir: Path) -> None:
        """Generate the benchmark_report.json file."""
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "benchmark_report.json"
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.metrics, f, indent=2)
            
        logger.info(f"Benchmark report generated at {report_path}")
