import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from zoneinfo import ZoneInfo
from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError, DuplicateKeyError
from dotenv import load_dotenv
from bson import ObjectId


# =========================================================
# 1. MONGODB CONNECTION
# =========================================================

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI is missing from .env")

client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=5000
)

try:
    client.admin.command("ping")
    print("Successfully connected to MongoDB Atlas!")

except PyMongoError as error:
    client.close()
    raise ConnectionError(f"MongoDB connection failed: {error}")

project_db = client["student_wellbeing_db"]

assessment_records = project_db["assessment_records"]
user_records = project_db["user_records"]

# =========================================================
# 2. ABSTRACT STORAGE INTERFACE
# =========================================================

class StorageInterface(ABC):

    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def save(self, data):
        pass

    @abstractmethod
    def update(self, identifier, updates):
        pass

    @abstractmethod
    def delete(self, identifier):
        pass

# =========================================================
# 3. MONGODB STORAGE
# =========================================================

class MongoDBStorage(StorageInterface):

    def __init__(self, collection, unique_fields=None):
        self.__collection = collection

        # Create unique indexes when needed
        if unique_fields:
            for field in unique_fields:
                self.__collection.create_index(
                    [(field, ASCENDING)],
                    unique=True
                )

    # Load all documents
    def load(self):
        try:
            documents = self.__collection.find({})
            return list(documents)

        except PyMongoError as error:
            print(f"Error loading records: {error}")
            return []

    # Insert a new document
    def save(self, data):
        try:
            result = self.__collection.insert_one(data)
            return str(result.inserted_id)

        except DuplicateKeyError:
            print("Duplicate record detected.")
            return None

        except PyMongoError as error:
            print(f"Error saving record: {error}")
            return None
    
    # Find one document
    def find_one(self, query):
        try:
            return self.__collection.find_one(query)

        except PyMongoError as error:
            print(f"Error retrieveing record: {error}")
            return None

    # Update an existing document
    def update(self, query, updates):
        try:
            result = self.__collection.update_one(
                query,
                {"$set": updates}
            )

            return result.matched_count > 0

        except DuplicateKeyError as error:
            print(f"Duplicate value: {error}")
            return False

        except (PyMongoError, ValueError) as error:
            print(f"Error updating record: {error}")
            return False

    # Delete a document
    def delete(self, query):
        try:
            result = self.__collection.delete_one(query)
            return result.deleted_count > 0

        except PyMongoError as error:
            print(f"Error deleting record: {error}")
            return False

    # Replace today's assessment record for a user
    def replace_today(self, user_id, today, new_record):
        try:
            self.__collection.replace_one(
                {
                    "user_input.user_id": user_id,
                    "date": today
                },
                new_record,
                upsert=True
            )

            return True

        except PyMongoError as error:
            print(f"Error replacing assessment record: {error}")
            return False

# =========================================================
# 4. USER RECORD
# =========================================================

class UserRecord:
    def __init__(self, username, password, user_id=None):
        if user_id is None:
            self.__user_id = str(uuid.uuid4())
        else:
            self.__user_id = user_id

        self.__username = username
        self.__password = password

    def get_user_id(self):
        return self.__user_id

    def get_username(self):
        return self.__username

    def get_password(self):
        return self.__password

    def to_dict(self):
        return {
            "user_id": self.__user_id,
            "username": self.__username,
            "password": self.__password
        }

# =========================================================
# 5. ASSESSMENT RECORD
# =========================================================

class AssessmentRecord:
    def __init__(self, user_input, ai_output, logic_output, record_id=None, date=None, time=None):
        now = datetime.now(ZoneInfo("Asia/Singapore"))

        if record_id is None:
            # New assessment
            self.__record_id = str(uuid.uuid4())
            self.__date = now.strftime("%d-%m-%Y")
            self.__time = now.strftime("%H:%M:%S")
        else:
            # Existing assessment
            self.__record_id = record_id
            self.__date = date
            self.__time = time

        self.__user_input = user_input
        self.__ai_output = ai_output
        self.__logic_output = logic_output

    def get_record_id(self):
        return self.__record_id

    def get_date(self):
        return self.__date

    def get_time(self):
        return self.__time

    def get_user_input(self):
        return self.__user_input

    def get_ai_output(self):
        return self.__ai_output

    def get_logic_output(self):
        return self.__logic_output

    # Convert assessment record into a dictionary
    def to_dict(self):
        return {
            "record_id": self.__record_id,
            "date": self.__date,
            "time": self.__time,
            "user_input": self.__user_input,
            "ai_output": self.__ai_output,
            "logic_output": self.__logic_output
        }
    
# =========================================================
# 6. USER DATA MANAGER
# =========================================================

class UserDataManager:

    def __init__(self, storage):
        self.__storage = storage
        self.__users = []

        self.load_users()

    # Load users from MongoDB
    def load_users(self):
        documents = self.__storage.load()
        self.__users = []

        for document in documents:
            user = UserRecord(
                username=document["username"],
                password=document["password"],
                user_id=str(document["user_id"])
            )

            self.__users.append(user)

        return self.__users

    def get_users(self):
        return self.__users.copy()

    def create_user(self, username, password):
        user = UserRecord(username, password)

        success = self.__storage.save(user.to_dict())

        if success is not None:
            self.__users.append(user)
            return user.get_user_id()

        return None

    def get_user_by_id(self, user_id):
        document = self.__storage.find_one({"user_id": user_id})

        if document is None:
            return None

        return UserRecord(
            username=document["username"],
            password=document["password"],
            user_id=document["user_id"]
        )

    def get_user_by_username(self, username):
        document = self.__storage.find_one({"username": username})

        if document is None:
            return None

        return UserRecord(
            username=document["username"],
            password=document["password"],
            user_id=document["user_id"]
        )

    def update_user(self, user_id, updates):
        allowed_fields = {"username", "password"}

        if not updates or not set(updates.keys()).issubset(allowed_fields):
            return False

        success = self.__storage.update(
            {"user_id": user_id},
            updates
        )

        if success:
            self.load_users()

        return success

    def delete_user(self, user_id):
        success = self.__storage.delete({"user_id": user_id})

        if success:
            self.load_users()

        return success

# =========================================================
# 7. ASSESSMENT DATA MANAGER
# =========================================================
class AssessmentDataManager:
    def __init__(self, storage):
        self.__storage = storage
        self.__records = []

        self.load_records()

    def load_records(self):
        documents = self.__storage.load()
        self.__records = []

        for document in documents:
            record = AssessmentRecord(
                user_input=document["user_input"],
                ai_output=document["ai_output"],
                logic_output=document["logic_output"],
                record_id=document["record_id"],
                date=document["date"],
                time=document["time"]
            )

            self.__records.append(record)

        return self.__records

    def save(self, record):
        if not isinstance(record, AssessmentRecord):
            return False

        record_data = record.to_dict()

        success = self.__storage.save(record_data)

        if success is not None:
            self.__records.append(record)
            return True

        return False

    def merge_record(self, user_input, ai_output, logic_output):
        return AssessmentRecord(
            user_input,
            ai_output,
            logic_output
        )

    def get_records(self):
        return self.__records.copy()

    def get_user_records(self, user_id):
        user_records = []

        for record in self.__records:
            user_input = record.get_user_input()

            if user_input.get("user_id") == user_id:
                user_records.append(record)

        user_records.sort(
            key=lambda record: datetime.strptime(
                record.get_date() + " " + record.get_time(),
                "%d-%m-%Y %H:%M:%S"
            ),
            reverse=True
        )

        return user_records

    def get_latest_user_record(self, user_id):
        records = self.get_user_records(user_id)

        if records:
            return records[0]

        return None

    def get_user_int_records(self, records, user_id):
        user_records = []

        for record in records:
            user_input = record.get_user_input()
            ai_output = record.get_ai_output()

            if user_input.get("user_id") == user_id:
                user_records.append({
                    "date": record.get_date(),
                    "sleep_duration": user_input.get("sleep_duration"),
                    "focus_level": user_input.get("focus_level"),
                    "stress_level": user_input.get("stress_level"),
                    "social_activity_level": user_input.get("social_activity_level"),
                    "mental_wellness_risk_score": ai_output.get("mental_wellness_risk_score"),
                    "burnout_risk_score": ai_output.get("burnout_risk_score")
                })

        return user_records

    def replace_user_record(self, user_id, record):
        if not isinstance(record, AssessmentRecord):
            return False

        if record.get_user_input().get("user_id") != user_id:
            return False

        today = datetime.now(
            ZoneInfo("Asia/Singapore")
        ).strftime("%d-%m-%Y")

        if record.get_date() != today:
            return False

        record_data = record.to_dict()

        success = self.__storage.replace_today(
            user_id,
            today,
            record_data
        )

        if success:
            updated_records = []

            for existing_record in self.__records:
                user_input = existing_record.get_user_input()

                if not (
                    user_input.get("user_id") == user_id
                    and existing_record.get_date() == today
                ):
                    updated_records.append(existing_record)

            updated_records.append(record)
            self.__records = updated_records

            return True

        return False

    def get_previous_attempts(self, user_id):
        records = self.get_user_records(user_id)

        today = datetime.now(
            ZoneInfo("Asia/Singapore")
        ).strftime("%d-%m-%Y")

        previous_attempts = []

        for record in records:
            if record.get_date() != today:
                previous_attempts.append({
                    **record.get_user_input(),
                    **record.get_ai_output()
                })

        return previous_attempts

# =========================================================
# 8. MAIN DATA MANAGER
# =========================================================

class DataManager:
    """
    Central manager that provides access to
    user and assessment data operations.
    """

    def __init__(self, user_collection, assessment_collection):

        # Create storage objects
        user_storage = MongoDBStorage(
            user_collection,
            unique_fields=["username"]
        )

        assessment_storage = MongoDBStorage(
            assessment_collection
        )

        # Create individual managers
        self.__user_manager = UserDataManager(
            user_storage
        )

        self.__assessment_manager = AssessmentDataManager(
            assessment_storage
        )

    # -------------------------
    # USER OPERATIONS
    # -------------------------

    def create_user(self, username, password):
        return self.__user_manager.create_user(
            username, password
        )

    def get_users(self):
        return self.__user_manager.get_users()

    def get_user_by_id(self, user_id):
        return self.__user_manager.get_user_by_id(
            user_id
        )

    def get_user_by_username(self, username):
        return self.__user_manager.get_user_by_username(
            username
        )

    def update_user(self, user_id, updates):
        return self.__user_manager.update_user(
            user_id, updates
        )

    def delete_user(self, user_id):
        return self.__user_manager.delete_user(user_id)

    # -------------------------
    # ASSESSMENT OPERATIONS
    # -------------------------

    def load_records(self):
        return self.__assessment_manager.load_records()

    def merge_record(self, user_input, ai_output, logic_output):
        return self.__assessment_manager.merge_record(
            user_input, ai_output, logic_output
        )

    def save(self, record):
        return self.__assessment_manager.save(record)

    def get_records(self):
        return self.__assessment_manager.get_records()

    def get_user_records(self, user_id):
        return self.__assessment_manager.get_user_records(
            user_id
        )

    def get_latest_user_record(self, user_id):
        return self.__assessment_manager.get_latest_user_record(
            user_id
        )

    def get_user_int_records(self, records, user_id):
        return self.__assessment_manager.get_user_int_records(
            records, user_id
        )

    def replace_user_record(self, user_id, record):
        return self.__assessment_manager.replace_user_record(
            user_id, record
        )

    def get_previous_attempts(self, user_id):
        return self.__assessment_manager.get_previous_attempts(
            user_id
        )


# =========================================================
# 9. TESTING
# =========================================================


if __name__ == "__main__":

    # Initialise DataManager
    data_manager = DataManager(user_records, assessment_records)

    print("\n========== USER TESTING ==========")

    # 1. Create a test user
    username = "test_user_" + str(uuid.uuid4())[:8]

    # Replace this with a properly hashed test password
    hashed_password = "test_hashed_password"

    user_id = data_manager.create_user(
        username,
        hashed_password
    )

    if user_id:
        print("User created successfully!")
        print("User ID:", user_id)
        print("Username:", username)
    else:
        print("Failed to create user.")

    # 2. Retrieve user by ID
    print("\n--- Retrieve User By ID ---")

    user = data_manager.get_user_by_id(user_id)

    if user:
        print("User ID:", user.get_user_id())
        print("Username:", user.get_username())
        print("Password:", user.get_password())
    else:
        print("User not found.")

    # 3. Retrieve user by username
    print("\n--- Retrieve User By Username ---")

    user = data_manager.get_user_by_username(username)

    if user:
        print("Found user:", user.get_username())
    else:
        print("User not found.")

    print("\n========== ASSESSMENT TESTING ==========")

    # 4. Create assessment input
    user_input = {
        "user_id": user_id,
        "sleep_duration": 7,
        "stress_level": 3,
        "focus_level": 4,
        "academic_workload": 3,
        "mood": "Good",
        "social_activity_level": 4,
        "reflection": "I feel quite productive today."
    }

    ai_output = {
        "mental_wellness_risk_score": 25,
        "sentiment": "Positive",
        "burnout_risk_score": 20,
        "crisis_alert": False,
        "primary_stressor": "Academic workload",
        "personalized_recommendations": [
            "Maintain a consistent sleep schedule.",
            "Take regular study breaks."
        ]
    }

    logic_output = {
        "mental_wellness_risk_tier": "Low",
        "warnings": None,
        "counselling_recommendation": False
    }

    # 5. Merge assessment data into an AssessmentRecord
    assessment = data_manager.merge_record(
        user_input,
        ai_output,
        logic_output
    )

    # 6. Save assessment record
    success = data_manager.save(assessment)

    if success:
        print("Assessment saved successfully!")
        print("Record ID:", assessment.get_record_id())
        print("User ID:", assessment.get_user_input()["user_id"])
        print("Date:", assessment.get_date())
        print("Time:", assessment.get_time())
    else:
        print("Failed to save assessment.")

    # 7. Retrieve all assessments belonging to this user
    print("\n--- User Assessment History ---")

    records = data_manager.get_user_records(user_id)

    for record in records:
        print("Record ID:", record.get_record_id())
        print("Date:", record.get_date())
        print("Stress Level:", record.get_user_input()["stress_level"])
        print("Risk Score:", record.get_ai_output()["mental_wellness_risk_score"])
        print("----------------------------")

    # 8. Retrieve latest assessment
    print("\n--- Latest Assessment ---")

    latest = data_manager.get_latest_user_record(user_id)

    if latest:
        print("Latest Record ID:", latest.get_record_id())
        print("Date:", latest.get_date())
        print("Risk Score:", latest.get_ai_output()["mental_wellness_risk_score"])
    else:
        print("No assessment found.")

    # 9. Retrieve previous attempts
    print("\n--- Previous Attempts ---")

    previous_attempts = data_manager.get_previous_attempts(user_id)

    print("Number of previous attempts:", len(previous_attempts))

    for attempt in previous_attempts:
        print(attempt)

    # 10. Update user
    print("\n========== UPDATE USER ==========")

    update_success = data_manager.update_user(
        user_id,
        {"username": username + "_updated"}
    )

    if update_success:
        print("Username updated successfully!")
    else:
        print("Failed to update username.")

    # Verify updated username
    updated_user = data_manager.get_user_by_id(user_id)

    if updated_user:
        print("Updated username:", updated_user.get_username())

    # 11. Delete test user
    # Uncomment this section when you are ready to delete the test user.

    # print("\n========== DELETE USER ==========")
    # delete_success = data_manager.delete_user(user_id)
    #
    # if delete_success:
    #     print("Test user deleted successfully!")
    # else:
    #     print("Failed to delete test user.")

    client.close()

