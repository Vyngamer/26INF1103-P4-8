from abc import ABC, abstractmethod
from ..CurrentAttempt import CurrentAttempt
from ..PreviousAttempts import PreviousAttempts

class ComparisonRule(ABC):
    """Contract for feedback that compares current and previous attempts."""

    @abstractmethod
    def evaluate(
        self,
        current: CurrentAttempt,
        history: PreviousAttempts,
    ) -> str | None:
        pass