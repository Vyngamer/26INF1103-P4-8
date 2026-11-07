from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError, PyMongoError
from StorageInterface import StorageInterface

# Implements database storage operations using MongoDB
class MongoDBStorage(StorageInterface):
    def __init__(self, collection, unique_fields=None):
        self.__collection = collection

        if unique_fields:
            try:
                for field in unique_fields:
                    self.__collection.create_index(
                        [(field, ASCENDING)],
                        unique=True
                    )

            except PyMongoError as error:
                print(f"Error creating unique index: {error}")

    def load(self):
        try:
            return list(self.__collection.find())

        except PyMongoError as error:
            print(f"Error loading records: {error}")
            return []

    def save(self, data):
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
    
    def find_one(self, query):
        try:
            return self.__collection.find_one(query)

        except PyMongoError as error:
            print(f"Error finding record: {error}")
            return None

    def update(self, query, updates):
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

    def delete(self, query):
        if not isinstance(query, dict):
            raise ValueError("Query must be a dictionary.")

        try:
            result = self.__collection.delete_one(query)
            return result.deleted_count > 0

        except PyMongoError as error:
            print(f"Error deleting record: {error}")
            return False

    def replace_today(self, user_id, today, new_record):
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