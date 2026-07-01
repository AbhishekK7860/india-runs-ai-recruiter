"""Counter metrics module."""

from collections import defaultdict


class MetricsCounter:
    """Tracks counts of events during pipeline execution."""

    def __init__(self) -> None:
        """Initialize counters."""
        self._counts: dict[str, int] = defaultdict(int)

    def increment(self, event_name: str, amount: int = 1) -> None:
        """Increment the count for an event.

        Args:
            event_name: Name of the event (e.g., 'records_processed').
            amount: Amount to increment by.
        """
        self._counts[event_name] += amount

    def get_count(self, event_name: str) -> int:
        """Get the current count for an event."""
        return self._counts.get(event_name, 0)

    def reset(self) -> None:
        """Reset all counters."""
        self._counts.clear()


# Global counter instance
counters = MetricsCounter()
