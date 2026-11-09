from data_manager_helper.MongoDBConnection import MongoDBConnection
from data_manager_helper.MongoDBStorage import MongoDBStorage
from data_manager_helper.UserManager import UserManager
from data_manager_helper.AssessmentManager import AssessmentManager

# Main Interface for managing user accounts and assessment records
class DataManager:

    def __init__(self):

        self.__connection = MongoDBConnection()

        if not self.__connection.test_connection():
            self.__connection.close()
            raise ConnectionError("Unable to connect to MongoDB Atlas.")

        user_collection = self.__connection.get_collection("user_records")
        assessment_collection = self.__connection.get_collection("assessment_records")

        self.__user_storage = MongoDBStorage(
            user_collection, unique_fields=["username"]
        )

        self.__assessment_storage = MongoDBStorage(
            assessment_collection
        )

        self.__user_manager = UserManager(
            self.__user_storage
        )

        self.__assessment_manager = AssessmentManager(
            self.__assessment_storage
        )

    # ==========================================
    # USER MANAGEMENT
    # ==========================================

    def create_user(self, username, password):
        return self.__user_manager.create_user(
            username,
            password
        )

    def get_users(self):
        return self.__user_manager.get_users()

    def get_user_by_id(self, user_id):
        return self.__user_manager.get_user_by_id(user_id)

    def get_user_by_username(self, username):
        return self.__user_manager.get_user_by_username(username)

    def update_user(self, user_id, updates):
        return self.__user_manager.update_user(
            user_id,
            updates
        )

    def delete_user(self, user_id):
        user = self.__user_manager.get_user_by_id(user_id)

        if not user:
            return False

        # Delete all assessment records belonging to user
        assessment_deleted = self.__assessment_manager.delete_user_records(
            user_id
        )

        if not assessment_deleted:
            return False

        # Delete the user
        return self.__user_manager.delete_user(user_id)


    # ==========================================
    # ASSESSMENT MANAGEMENT
    # ==========================================

    def load_records(self):
        return self.__assessment_manager.load_records()

    def merge_record(self, user_input, ai_output, logic_output):
        return self.__assessment_manager.merge_record(
            user_input,
            ai_output,
            logic_output
        )

    def save(self, record):
        return self.__assessment_manager.save(record)

    def get_records(self):
        return self.__assessment_manager.get_records()

    def get_user_records(self, user_id):
        return self.__assessment_manager.get_user_records(user_id)

    def get_latest_user_record(self, user_id):
        return self.__assessment_manager.get_latest_user_record(
            user_id
        )

    def get_user_int_records(self, records, user_id):
        return self.__assessment_manager.get_user_int_records(
            records,
            user_id
        )

    def replace_user_record(self, user_id, record):
        return self.__assessment_manager.replace_user_record(
            user_id,
            record
        )

    def get_previous_attempts(self, user_id):
        return self.__assessment_manager.get_previous_attempts(
            user_id
        )

    # ==========================================
    # CONNECTION MANAGEMENT
    # ==========================================

    def close(self):
        self.__connection.close()