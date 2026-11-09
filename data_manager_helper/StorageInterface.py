from abc import ABC, abstractmethod

# Abstract interface defining the standard storage operations.
class StorageInterface(ABC):

    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def save(self, data):
        pass

    @abstractmethod
    def update(self, query, updates):
        pass

    @abstractmethod
    def delete(self, query):
        pass

    @abstractmethod
    def find_one(self, query):
        pass

    @abstractmethod
    def replace_today(self, user_id, today, new_record):
        pass

    @abstractmethod
    def delete_many(self, query):
        pass