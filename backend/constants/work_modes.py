"""Work mode constants."""

from enum import StrEnum


class WorkMode(StrEnum):
    """Work location modes."""

    REMOTE = "Remote"
    ONSITE = "On-site"
    HYBRID = "Hybrid"
