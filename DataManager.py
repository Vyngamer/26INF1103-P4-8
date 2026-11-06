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
            return list(self.__collection.find({}))

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
    def update(self, identifier, updates):
        try:
            result = self.__collection.update_one(
                {"_id": ObjectId(identifier)},
                {"$set": updates}
            )

            return result.matched_count > 0

        except DuplicateKeyError:
            print("Duplicate value detected.")
            return False

        except (PyMongoError, ValueError) as error:
            print(f"Error updating record: {error}")
            return False

    # Delete a document
    def delete(self, identifier):
        try:
            result = self.__collection.delete_one({
                "_id": ObjectId(identifier)
            })

            return result.deleted_count > 0

        except (PyMongoError, ValueError) as error:
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

class DataManager:

    def __init__(self, collection):
        self.__storage = MongoDBStorage(collection)
        self.__records = []

        # Load existing assessment records
        self.load_records()

    # Load records from MongoDB and convert them into objects
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

    # Save a new assessment record
    def save(self, record):

        if not isinstance(record, AssessmentRecord):
            return False

        record_data = record.to_dict()

        success = self.__storage.save(record_data)

        if success:
            self.__records.append(record)
            return True

        return False

    # Merge outputs from the different managers
    def merge_record(self, user_input, ai_output, logic_output):

        return AssessmentRecord(
            user_input,
            ai_output,
            logic_output
        )

    # Get all assessment records
    def get_records(self):

        return self.__records

    # Get assessment records belonging to a user
    def get_user_records(self, user_id):

        user_records = []

        for record in self.__records:

            user_input = record.get_user_input()

            if user_input.get("user_id") == user_id:
                user_records.append(record)

        # Sort records by date and time
        user_records.sort(
            key=lambda record: datetime.strptime(
                record.get_date() + " " + record.get_time(),
                "%d-%m-%Y %H:%M:%S"
            ),
            reverse=True
        )

        return user_records

    # Get the latest assessment record for a user
    def get_latest_user_record(self, user_id):

        records = self.get_user_records(user_id)

        if records:
            return records[0]

        return None

    # Get selected assessment information for a user
    def get_user_int_records(self, records, user_id):

        user_records = []

        for record in records:

            user_input = record.get_user_input()
            ai_output = record.get_ai_output()

            if user_input.get("user_id") == user_id:

                user_records.append({
                    "date": record.get_date(),

                    "sleep_duration": user_input.get(
                        "sleep_duration"
                    ),

                    "focus_level": user_input.get(
                        "focus_level"
                    ),

                    "stress_level": user_input.get(
                        "stress_level"
                    ),

                    "social_activity_level": user_input.get(
                        "social_activity_level"
                    ),

                    "mental_wellness_risk_score": ai_output.get(
                        "mental_wellness_risk_score"
                    ),

                    "burnout_risk_score": ai_output.get(
                        "burnout_risk_score"
                    )
                })

        return user_records

    # Replace today's assessment record for a user
    def replace_user_record(self, user_id, record):

        if not isinstance(record, AssessmentRecord):
            return False

        # Check that the replacement belongs to the correct user
        if record.get_user_input().get("user_id") != user_id:
            return False

        # Get today's date in Singapore timezone
        today = datetime.now(
            ZoneInfo("Asia/Singapore")
        ).strftime("%d-%m-%Y")

        # Ensure the replacement record is dated today
        if record.get_date() != today:
            return False

        # Convert the assessment object into a dictionary
        record_data = record.to_dict()

        # Replace the existing MongoDB document
        success = self.__storage.replace_today(
            user_id,
            today,
            record_data
        )

        if success:

            updated_records = []

            for existing_record in self.__records:

                user_input = existing_record.get_user_input()

                # Keep records belonging to other users or dates
                if not (
                    user_input.get("user_id") == user_id
                    and existing_record.get_date() == today
                ):
                    updated_records.append(existing_record)

            updated_records.append(record)

            self.__records = updated_records

            return True

        return False

    # Get previous assessment attempts
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


if __name__ == "__main__":

    print("\n========== DATA MANAGER TESTING ==========\n")

    # Initialise DataManager
    data_manager = DataManager(assessment_records)

    # ----------------------------------
    # 1. Test load_records()
    # ----------------------------------
    print("1. Testing load_records()")

    records = data_manager.load_records()

    print("Total records loaded:", len(records))


    # ----------------------------------
    # 2. Test merge_record()
    # ----------------------------------
    print("\n2. Testing merge_record()")

    user_input =  {
            "user_id": "3",
            "sleep_duration": 1.0,
            "stress_level": 1,
            "focus_level": 1,
            "academic_workload": 1,
            "mood": "Motivated",
            "social_activity_level": 1,
            "reflection": "sad"
            }
    
    ai_output = {
            "burnout_risk_score": 50,
            "crisis_alert": True,
            "mental_wellness_risk_score": 85,
            "personalized_recommendations": "Your sleep duration of only one hour is critically low and poses an immediate danger to your physical and cognitive health. Please prioritize immediate rest or contact a medical professional, as your current level of sleep deprivation is unsustainable and requires urgent attention.",
            "primary_stressor": "Sleep Deprivation",
            "sentiment": "Neutral"
            }
    
    logic_output = {
            "mental_wellness_risk_tier": "High",
            "warnings": [],
            "route": "Urgent support",
            "counselling_recommendation": True,
            "display_messages": [
                "You slept less than 7 hours. Try to get more sleep."
            ]
            }

    record = data_manager.merge_record(
        user_input,
        ai_output,
        logic_output
    )

    print("Record created:", record.to_dict())


    # ----------------------------------
    # 3. Test save()
    # ----------------------------------
    print("\n3. Testing save()")

    success = data_manager.save(record)

    print("Record saved:", success)


    # ----------------------------------
    # 4. Test get_records()
    # ----------------------------------
    print("\n4. Testing get_records()")

    all_records = data_manager.get_records()

    print("Total records:", len(all_records))


    # ----------------------------------
    # 5. Test get_user_records()
    # ----------------------------------
    print("\n5. Testing get_user_records()")

    user_records = data_manager.get_user_records("1")

    print("User records:", len(user_records))


    # ----------------------------------
    # 6. Test get_latest_user_record()
    # ----------------------------------
    print("\n6. Testing get_latest_user_record()")

    latest_record = data_manager.get_latest_user_record(
        "1"
    )

    if latest_record:
        print("Latest record:", latest_record.to_dict())
    else:
        print("No records found.")


    # ----------------------------------
    # 7. Test get_user_int_records()
    # ----------------------------------
    print("\n7. Testing get_user_int_records()")

    selected_records = data_manager.get_user_int_records(
        all_records,
        "1"
    )

    print("Selected assessment information:")
    print(selected_records)


    # ----------------------------------
    # 8. Test replace_user_record()
    # ----------------------------------
    print("\n8. Testing replace_user_record()")

    updated_user_input = {
        **user_input,
        "stress_level": 2,
        "reflection": "Feeling less stressed today."
    }

    updated_record = data_manager.merge_record(
        updated_user_input,
        ai_output,
        logic_output
    )

    success = data_manager.replace_user_record(
        "1",
        updated_record
    )

    print("Record replaced:", success)


    # ----------------------------------
    # 9. Test get_previous_attempts()
    # ----------------------------------
    print("\n9. Testing get_previous_attempts()")

    previous_attempts = data_manager.get_previous_attempts(
        "1"
    )

    print("Previous attempts:", previous_attempts)


    print("\n========== TESTING COMPLETED ==========")