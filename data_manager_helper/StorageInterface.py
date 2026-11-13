from abc import ABC, abstractmethod
from typing import Any

'''
Abstract interface for the storage operations the managers rely on.
MongoDBStorage implement these methods, so themanagers don't depend on a specific database.
'''
 
class StorageInterface(ABC):

    # return every document
    @abstractmethod
    def load(self) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def save(self, data: dict[str, Any]) -> str | None:
        pass

    @abstractmethod
    def update(self, query: dict[str, Any], updates: dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def delete(self, query: dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        pass

    @abstractmethod
    def replace_today(self, user_id: str, today: str, new_record: dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def delete_many(self, query: dict[str, Any]) -> int | None:
        pass