import json
import os
from datetime import datetime
import os
import uuid
from pathlib import Path

class JSONStorage:
    def __init__(self, filename):
        self.__filename = filename

    def get_filename(self):
        return self.__filename

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

class AssessmentRecord:
    def __init__(self, user_input, ai_output, logic_output):
        self.__record_id = str(uuid.uuid4())
        now = datetime.now()
        self.__date = now.strftime("%d-%m-%Y")
        self.__time = now.strftime("%H:%M:%S")
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
