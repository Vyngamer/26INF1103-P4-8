import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from pymongo.collection import Collection
from pymongo.database import Database

'''
Manages the connection to MongoDB Atlas
'''
# Handles the connection to MongoDB Atlas
class MongoDBConnection:
    
    def __init__(self) -> None:
        load_dotenv() # load environment variables

        self.__uri: str | None = os.getenv("MONGODB_URI")

        if not self.__uri:
            raise ValueError(
                "MONGODB_URI is not configured in the .env file."
            )

        self.__client: MongoClient = MongoClient(
            self.__uri,
            serverSelectionTimeoutMS=5000
        )

        self.__database: Database = self.__client["student_wellbeing_db"]

    # ping the server to test for connection
    def test_connection(self) -> bool:
        try:
            self.__client.admin.command("ping")
            print("Successfully connected to MongoDB Atlas!")
            return True

        except PyMongoError as error:
            print(f"MongoDB connection failed: {error}")
            return False

    # return the collection with the name from the database
    def get_collection(self, collection_name) -> Collection:
        return self.__database[collection_name]

    # close the client connection
    def close(self) -> None:
        self.__client.close()