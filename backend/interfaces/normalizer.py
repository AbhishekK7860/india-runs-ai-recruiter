"""Normalizer interfaces."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T_IN = TypeVar("T_IN")
T_OUT = TypeVar("T_OUT")


class Normalizer(ABC, Generic[T_IN, T_OUT]):
    """Abstract base class for data normalization."""

    @abstractmethod
    def normalize(self, data: T_IN) -> T_OUT:
        """Normalize the input data.

        Args:
            data: The raw or semi-processed data.

        Returns:
            The normalized output data.
        """
        pass
