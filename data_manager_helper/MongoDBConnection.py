import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError


# Handles the connection to MongoDB Atlas
class MongoDBConnection:
    
    def __init__(self):
        load_dotenv()

        self.__uri = os.getenv("MONGODB_URI")

        if not self.__uri:
            raise ValueError(
                "MONGODB_URI is not configured in the .env file."
            )

        self.__client = MongoClient(
            self.__uri,
            serverSelectionTimeoutMS=5000
        )

        self.__database = self.__client["student_wellbeing_db"]

    def test_connection(self):
        try:
            self.__client.admin.command("ping")
            print("Successfully connected to MongoDB Atlas!")
            return True

        except PyMongoError as error:
            print(f"MongoDB connection failed: {error}")
            return False

    def get_collection(self, collection_name):
        return self.__database[collection_name]

    def close(self):
        self.__client.close()