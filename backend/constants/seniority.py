"""Seniority constants."""

from enum import StrEnum


class SeniorityLevel(StrEnum):
    """Standardized seniority levels."""

    ENTRY = "Entry"
    JUNIOR = "Junior"
    MID_LEVEL = "Mid-level"
    SENIOR = "Senior"
    STAFF = "Staff"
    PRINCIPAL = "Principal"
    DIRECTOR = "Director"
    VP = "VP"
    EXECUTIVE = "Executive"
