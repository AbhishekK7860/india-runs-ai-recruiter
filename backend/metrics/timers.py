"""Timer metrics module."""

import time
from collections import defaultdict
from contextlib import contextmanager
from typing import Iterator


class MetricsTimer:
    """Tracks execution time of various pipeline stages."""

    def __init__(self) -> None:
        """Initialize timers."""
        self._totals: dict[str, float] = defaultdict(float)
        self._counts: dict[str, int] = defaultdict(int)

    @contextmanager
    def measure(self, stage_name: str) -> Iterator[None]:
        """Context manager to measure execution time of a block of code.

        Args:
            stage_name: Name of the stage being measured (e.g., 'parsing').
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self._totals[stage_name] += elapsed
            self._counts[stage_name] += 1

    def get_total(self, stage_name: str) -> float:
        """Get the total elapsed time for a stage."""
        return self._totals.get(stage_name, 0.0)

    def get_average(self, stage_name: str) -> float:
        """Get the average elapsed time per call for a stage."""
        count = self._counts.get(stage_name, 0)
        if count == 0:
            return 0.0
        return self._totals.get(stage_name, 0.0) / count

    def reset(self) -> None:
        """Reset all timers."""
        self._totals.clear()
        self._counts.clear()


# Global timer instance
timers = MetricsTimer()
