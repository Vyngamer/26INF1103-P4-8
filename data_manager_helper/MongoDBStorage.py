from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError, PyMongoError
from data_manager_helper.StorageInterface import StorageInterface
from typing import Any
from pymongo.collection import Collection

'''
Implements StorageInterface using a MongoDB collection
'''

class MongoDBStorage(StorageInterface):
    def __init__(self, collection: Collection, unique_fields: list[str] | None = None):
        self.__collection: Collection = collection

        # create a unique index on each listed field if any
        if unique_fields:
            try:
                for field in unique_fields:
                    self.__collection.create_index(
                        [(field, ASCENDING)],
                        unique=True
                    )

            except PyMongoError as error:
                print(f"Error creating unique index: {error}")

    # returns all documents in the collection
    def load(self) -> list[dict[str, Any]]:
        try:
            return list(self.__collection.find())

        except PyMongoError as error:
            print(f"Error loading records: {error}")
            return []

    # inserts a document into db
    def save(self, data: dict[str, Any]) -> str | None:
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary.")

        try:
            result = self.__collection.insert_one(data)
            return str(result.inserted_id)

        except DuplicateKeyError:
            print("Error: A record with the same unique value already exists.")
            return None

        except PyMongoError as error:
            print(f"Error saving record: {error}")
            return None

    # return first matching document
    def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        try:
            return self.__collection.find_one(query)

        except PyMongoError as error:
            print(f"Error finding record: {error}")
            return None

    # set the given fields based no the first matching document
    def update(self, query: dict[str, Any], updates: dict[str, Any]) -> bool:
        if not isinstance(query, dict) or not isinstance(updates, dict):
            raise ValueError("Query and updates must be dictionaries.")

        try:
            result = self.__collection.update_one(
                query,
                {"$set": updates}
            )

            return result.matched_count > 0

        except DuplicateKeyError:
            print("Error: Update violates a unique field constraint.")
            return False

        except PyMongoError as error:
            print(f"Error updating record: {error}")
            return False

    # delete the first matching document
    def delete(self, query: dict[str, Any]) -> bool:
        if not isinstance(query, dict):
            raise ValueError("Query must be a dictionary.")

        try:
            result = self.__collection.delete_one(query)
            return result.deleted_count > 0

        except PyMongoError as error:
            print(f"Error deleting record: {error}")
            return False

    # replace user record based on today date
    def replace_today(self, user_id: str, today: str, new_record: dict[str, Any]) -> bool:
        if not isinstance(new_record, dict):
            raise ValueError("New record must be a dictionary.")

        try:
            result = self.__collection.replace_one(
                {
                    "user_input.user_id": user_id,
                    "date": today
                },
                new_record,
                upsert=True
            )

            return (
                result.matched_count > 0
                or result.upserted_id is not None
            )

        except PyMongoError as error:
            print(f"Error replacing today's record: {error}")
            return False

    # delete all matching documents and give number of deleted items
    def delete_many(self, query: dict[str, Any]) -> int | None:

        try:
            if not isinstance(query, dict):
                return None

            result = self.__collection.delete_many(query)

            return result.deleted_count

        except PyMongoError as error:
            print(f"Error deleting documents: {error}")
            return None