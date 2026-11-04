import os
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Retrieve MongoDB connection string
MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI is missing from .env")

# Connect to MongoDB Atlas
client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=5000
)

# Test connection
try:
    client.admin.command("ping")
    print("Successfully connected to MongoDB Atlas!")

except PyMongoError as error:
    client.close()
    raise ConnectionError(f"MongoDB connection failed: {error}")

# Select database and collection
project_db = client["student_wellbeing_db"]
assessment_records = project_db["assessment_records"]

class MongoDBStorage:
    def __init__(self, collection):
        self.__collection = collection

    # Retrievs all assessment records from MongoDB
    def load(self):
        try:
            records = self.__collection.find(
                {},
                {"_id": 0}
            )

            return list(records)

        except PyMongoError as error:
            print(f"Error loading records: {error}")
            return []

    # Insert an assessment record into MongoDB
    def save(self, record):
        try:
            self.__collection.insert_one(record)
            return True

        except PyMongoError as error:
            print(f"Error saving record: {error}")
            return False

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

    # Load records from JSON and convert them into objects
    def load_records(self):
        documents = self.__storage.load()

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
        
    # Save all assessment objects into JSON
    def save_records(self):
        records_data = []

        for record in self.__records:
            records_data.append(record.to_dict())

        return self.__collection.save(records_data)

    # Merge outputs from the different managers
    def merge_record(self, user_input, ai_output, logic_output):
        return AssessmentRecord(user_input, ai_output, logic_output)

    # Save a new assessment record
    def save(self, record):
        if not isinstance(record, AssessmentRecord):
            return False

        self.__records.append(record)

        if self.save_records():
            return True

        # Remove the record if saving fails
        self.__records.pop()
        return False

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

    # Get the latest assessment record
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
                    "sleep_duration": user_input.get("sleep_duration"),
                    "focus_level": user_input.get("focus_level"),
                    "stress_level": user_input.get("stress_level"),
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

        today = datetime.now().strftime("%d-%m-%Y")

        updated_records = []

        for existing_record in self.__records:
            user_input = existing_record.get_user_input()

            # Keep records belonging to other users or other dates
            if not (
                user_input.get("user_id") == user_id
                and existing_record.get_date() == today
            ):
                updated_records.append(existing_record)

        # Check that the replacement belongs to the correct user
        if record.get_user_input().get("user_id") != user_id:
            return False

        old_records = self.__records
        self.__records = updated_records
        self.__records.append(record)

        if self.save_records():
            return True

        # Restore original records if saving fails
        self.__records = old_records
        return False

    # Get previous assessment attempts
    def get_previous_attempts(self, user_id):
        records = self.get_user_records(user_id)

        today = datetime.now().strftime("%d-%m-%Y")

        previous_attempts = []

        for record in records:
            if record.get_date() != today:
                previous_attempts.append({
                    **record.get_user_input(),
                    **record.get_ai_output()
                })

        return previous_attempts



class JSONStorage:
    def __init__(self, filename):
        self.__filename = filename

    # Load data from JSON file
    def load(self):
        if os.path.exists(self.__filename):
            try:
                with open(self.__filename, "r") as file:
                    records = json.load(file)

                if not isinstance(records, list):
                    raise ValueError("JSON file must contain a list.")

                return records

            except (json.JSONDecodeError, OSError, ValueError) as error:
                print(f"Error loading JSON file: {error}")
                return None

        else:
            # Create an empty JSON file if it does not exist
            self.save([])
            return []

     # Save data into JSON file
    def save(self, records):
        try:
            with open(self.__filename, "w") as file:
                json.dump(records, file, indent=4)

            return True

        except (OSError, TypeError) as error:
            print(f"Error saving JSON file: {error}")
            return False

     



