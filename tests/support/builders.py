from __future__ import annotations

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Generic, Self, TypeVar

T = TypeVar("T")

class Builder(ABC, Generic[T]):
    DEFAULTS: ClassVar[dict[str, Any]] = {}

    def __init__(self, **values: Any) -> None:
        unknown = set(values) - set(self.DEFAULTS)
        if unknown:
            raise TypeError(f"{type(self).__name__} has no field(s): {sorted(unknown)}")
        self._values = {**self.DEFAULTS, **values}

    def with_(self, **overrides: Any) -> Self:
        return type(self)(**{**self._values, **overrides})

    def values(self) -> dict[str, Any]:
        return dict(self._values)

    @abstractmethod
    def build(self) -> T:
        ...
