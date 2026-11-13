from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any

from data_manager_helper.AssessmentRecord import AssessmentRecord
from data_manager_helper.StorageInterface import StorageInterface

'''
Keeps an in-memory list of assessment records
'''

class AssessmentManager:
    def __init__(self, storage: StorageInterface) -> None:
        self.__storage: StorageInterface = storage
        self.__records: list[AssessmentRecord] = []

        self.load_records()

    # load all records
    def load_records(self) -> list[AssessmentRecord]:
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

        return self.get_records()

    # save a record
    def save(self, record: AssessmentRecord) -> bool:
        if not isinstance(record, AssessmentRecord):
            return False

        record_data = record.to_dict()

        result = self.__storage.save(record_data)

        if result is not None:
            self.__records.append(record)
            return True

        return False

    # combine 3 outputs into a record
    def merge_record(self, user_input: dict[str, Any], ai_output: dict[str, Any], logic_output: dict[str, Any]):
        return AssessmentRecord(
            user_input,
            ai_output,
            logic_output
        )

    # get all records
    def get_records(self) -> list[AssessmentRecord]:
        return self.__records.copy()

    # get that user records only
    def get_user_records(self, user_id: str) -> list[AssessmentRecord]:
        user_records = []

        for record in self.__records:
            user_input = record.get_user_input()

            if user_input.get("user_id") == user_id:
                user_records.append(record)

        # sort new to old
        user_records.sort(
            key=lambda record: datetime.strptime(
                record.get_date() + " " + record.get_time(),
                "%d-%m-%Y %H:%M:%S"
            ),
            reverse=True
        )

        return user_records

    # get the latest record only from the user
    def get_latest_user_record(self, user_id: str) -> AssessmentRecord | None:
        records = self.get_user_records(user_id)

        if records:
            return records[0]

        return None

    # get user records for numeric fields for graph
    def get_user_int_records(self, records: list[AssessmentRecord], user_id: str) -> list[dict[str, Any]]:
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

    # replace user record for today with the new one
    def replace_user_record(self, user_id: str, record: AssessmentRecord) -> bool:
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
            # remove today old record
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

    # return user previous attempts without the today record
    def get_previous_attempts(self, user_id: str) -> list[dict[str, Any]]:
        records = self.get_user_records(user_id)

        today = datetime.now(
            ZoneInfo("Asia/Singapore")
        ).strftime("%d-%m-%Y")

        previous_attempts = []

        for record in reversed(records):
            if record.get_date() != today:
                previous_attempts.append({
                    **record.get_user_input(),
                    **record.get_ai_output(),
                    "date": record.get_date(),
                    "time": record.get_time(),
                    "record_id": record.get_record_id()
                })

        return previous_attempts

    # delete all the user records
    def delete_user_records(self, user_id: str) -> bool:
        deleted_count = self.__storage.delete_many(
            {"user_input.user_id": user_id}
        )

        if deleted_count is None:
            return False

        remaining_records = []

        for record in self.__records:
            record_user_id = record.get_user_input().get("user_id")

            if record_user_id != user_id:
                remaining_records.append(record)

        self.__records = remaining_records
        return True