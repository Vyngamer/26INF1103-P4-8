from typing import Any

from data_manager_helper.AssessmentRecord import AssessmentRecord
from data_manager_helper.MongoDBConnection import MongoDBConnection
from data_manager_helper.MongoDBStorage import MongoDBStorage
from data_manager_helper.UserManager import UserManager
from data_manager_helper.UserRecord import UserRecord
from data_manager_helper.AssessmentManager import AssessmentManager

"""Single entry point for user accounts and assessment records.

    The rest of the app talks only to this class. It creates the database
    connection, the storage objects and the two managers, and forwards each
    call to the right manager.
"""

class DataManager:

    def __init__(self) -> None:

        # open the connection and stop early if database cannot be reached
        self.__connection: MongoDBConnection = MongoDBConnection()

        if not self.__connection.test_connection():
            self.__connection.close()
            raise ConnectionError("Unable to connect to MongoDB Atlas.")

        # indicate the exact collection name
        user_collection = self.__connection.get_collection("user_records")
        assessment_collection = self.__connection.get_collection("assessment_records")

        self.__user_storage: MongoDBStorage = MongoDBStorage(
            user_collection, unique_fields=["username"]
        )

        self.__assessment_storage: MongoDBStorage = MongoDBStorage(
            assessment_collection
        )

        self.__user_manager: UserManager = UserManager(
            self.__user_storage
        )

        self.__assessment_manager: AssessmentManager = AssessmentManager(
            self.__assessment_storage
        )

    # ==========================================
    # USER MANAGEMENT
    # ==========================================

    # create an acccount
    def create_user(self, username:str, password: str) -> str | None:
        return self.__user_manager.create_user(
            username,
            password
        )

    # get all user accounts
    def get_users(self)-> list[UserRecord]:
        return self.__user_manager.get_users()

    # return the account with this id
    def get_user_by_id(self, user_id:str) -> UserRecord | None:
        return self.__user_manager.get_user_by_id(user_id)

    # return the account with this username
    def get_user_by_username(self, username:str) -> UserRecord | None:
        return self.__user_manager.get_user_by_username(username)

    # Change username or password
    def update_user(self, user_id: str, updates: dict[str, str]) -> bool:
        return self.__user_manager.update_user(
            user_id,
            updates
        )

    # Delete the account and all of its records
    def delete_user(self, user_id: str) -> bool:
        user = self.__user_manager.get_user_by_id(user_id)

        if not user:
            return False

        # Delete all assessment records belonging to user
        assessment_deleted: bool = self.__assessment_manager.delete_user_records(
            user_id
        )

        if not assessment_deleted:
            return False

        # Delete the user
        return self.__user_manager.delete_user(user_id)


    # ==========================================
    # ASSESSMENT MANAGEMENT
    # ==========================================

    # load all assessment records
    def load_records(self) -> list[AssessmentRecord]:
        return self.__assessment_manager.load_records()

    # combine into single record
    def merge_record(self, user_input: dict[str, Any], ai_output:dict[str, Any], logic_output:dict[str, Any]) -> AssessmentRecord:
        return self.__assessment_manager.merge_record(
            user_input,
            ai_output,
            logic_output
        )

    # save the record
    def save(self, record: AssessmentRecord) -> bool:
        return self.__assessment_manager.save(record)

    # return all the records
    def get_records(self)-> list[AssessmentRecord]:
        return self.__assessment_manager.get_records()

    # return records for that user
    def get_user_records(self, user_id: str) -> list[AssessmentRecord]:
        return self.__assessment_manager.get_user_records(user_id)

    # return latest record for that user
    def get_latest_user_record(self, user_id: str) -> AssessmentRecord | None:
        return self.__assessment_manager.get_latest_user_record(
            user_id
        )

    # return numeric records for that user
    def get_user_int_records(self, records: list[AssessmentRecord], user_id: str) -> list[dict[str, Any]]:
        return self.__assessment_manager.get_user_int_records(
            records,
            user_id
        )

    # replace a record for today 
    def replace_user_record(self, user_id:str, record: AssessmentRecord) -> bool:
        return self.__assessment_manager.replace_user_record(
            user_id,
            record
        )

    # return user past attempts excluding today
    def get_previous_attempts(self, user_id: str) -> list[dict[str, Any]]:
        return self.__assessment_manager.get_previous_attempts(
            user_id
        )

    # ==========================================
    # CONNECTION MANAGEMENT
    # ==========================================

    # Close the database connection.
    def close(self) -> None:
        self.__connection.close()