import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

# Represents an individual student well-being assessment record
class AssessmentRecord:
    def __init__(self, user_input, ai_output, logic_output, record_id=None, date=None, time=None):
        now = datetime.now(ZoneInfo("Asia/Singapore"))

        if record_id is None:
            self.__record_id = str(uuid.uuid4())
            self.__date = now.strftime("%d-%m-%Y")
            self.__time = now.strftime("%H:%M:%S")
        else:
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

    def to_dict(self):
        return {
            "record_id": self.__record_id,
            "date": self.__date,
            "time": self.__time,
            "user_input": self.__user_input,
            "ai_output": self.__ai_output,
            "logic_output": self.__logic_output
        }