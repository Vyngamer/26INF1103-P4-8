from abc import ABC, abstractmethod
from ..CurrentAttempt import CurrentAttempt

class WarningRule(ABC):
    """Contract for rules that may produce a routing warning."""
    @abstractmethod
    def evaluate(self, current: CurrentAttempt) -> str | None:
        pass