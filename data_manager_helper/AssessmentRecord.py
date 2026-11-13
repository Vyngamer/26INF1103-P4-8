import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any

'''
Represents an individual student well-being assessment record
'''
class AssessmentRecord:
    def __init__(
        self,
        user_input: dict[str, Any], 
        ai_output: dict[str, Any], 
        logic_output: dict[str, Any], 
        record_id: str | None = None, 
        date: str | None = None, 
        time: str | None = None
    ) -> None:
        now = datetime.now(ZoneInfo("Asia/Singapore"))

        # new record then generate id, date, time
        if record_id is None:
            self.__record_id = str(uuid.uuid4())
            self.__date = now.strftime("%d-%m-%Y")
            self.__time = now.strftime("%H:%M:%S")
        #existing record, keep the values        
        else:
            self.__record_id = record_id
            self.__date = date
            self.__time = time

        self.__user_input: dict[str, Any] = user_input
        self.__ai_output: dict[str, Any] = ai_output
        self.__logic_output: dict[str, Any] = logic_output

    def get_record_id(self) -> str:
        return self.__record_id

    def get_date(self) -> str:
        return self.__date

    def get_time(self) -> str:
        return self.__time

    def get_user_input(self) -> dict[str, Any]:
        return self.__user_input

    def get_ai_output(self) -> dict[str, Any]:
        return self.__ai_output

    def get_logic_output(self) -> dict[str, Any]:
        return self.__logic_output

    # return record as a dict to save in db
    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.__record_id,
            "date": self.__date,
            "time": self.__time,
            "user_input": self.__user_input,
            "ai_output": self.__ai_output,
            "logic_output": self.__logic_output
        }