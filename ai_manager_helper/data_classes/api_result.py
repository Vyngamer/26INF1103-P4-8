from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Any

@dataclass(frozen=True)
class APIResult(Generic[TypeVar('T'), TypeVar('E')]):
    success: bool
    data: Optional[T] = None
    error: Optional[E] = None

    @classmethod
    def ok(cls, data):
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error):
        return cls(success=False, error=error)

