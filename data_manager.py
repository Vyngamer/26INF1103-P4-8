import json
from datetime import datetime
import os
import uuid
from pathlib import Path
import shutil
import logging

# Load data from the JSON database into records
def load(filename):
    try:
        if os.path.exists(filename): 
            with open(filename, "r", encoding="utf-8") as file:
                records = json.load(file)
        
            if not isinstance(records, list):
                raise ValueError("Database must contain a list of records.")

            return records

        # Create a new database if the file does not exist
        records = []
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(records, file, indent=4)
        
        return records
    
    except (OSError, json.JSONDecodeError, ValueError) as error:
        logging.error("Failed to load database %s : %s", filename, error)
        return []

# Save data into database as a single record
def save(record, filename):
    try:
        # Validate the record
        if not isinstance(record, dict):
            raise ValueError("Record must be a dictionary.")

        required_keys = ["user_input", "ai_output", "logic_output"]

        for key in required_keys:
            if key not in record:
                raise ValueError(f"Missing required key: {key}")

        # Back up the existing database
        if Path(filename).is_file():
            backup_json_file(filename)
    
        records = load(filename)

        if not isinstance(records, list):
            raise ValueError("Database must contain a list of records.")

        # Create a new record
        now = datetime.now()

        new_record = {
            "record_id": str(uuid.uuid4()),
            "date": now.strftime("%d-%m-%Y"),
            "time": now.strftime("%H:%M:%S"),
            "user_input": record["user_input"],
            "ai_output": record["ai_output"],
            "logic_output": record["logic_output"]
        }
        
        records.append(new_record)

        # Write the updated database
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(records, file, indent=4, ensure_ascii=False)

        return True

    except (OSError, TypeError, ValueError) as error:
        logging.error("Failed to save database %s: %s", filename, error)
        return False

# Back up the database before saving and keep the latest 3 backups
def backup_json_file(file_path: str) -> str:
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    # Create the backup folder
    backup_folder = path.parent / "Backup"
    backup_folder.mkdir(parents=True, exist_ok=True)

    # Create a timestamp backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{path.stem}_backup_{timestamp}{path.suffix}"
    backup_path = backup_folder / backup_name

    shutil.copy2(path, backup_path)

    backup_pattern = f"{path.stem}_backup_*{path.suffix}"
    backup_files = list(backup_folder.glob(backup_pattern))
    backup_files.sort(key=lambda file: file.name, reverse=True)

    for old_backup in backup_files[3:]:
        old_backup.unlink()

    return str(backup_path)

# Retrieves past records for selected columns for logic assessment
def get_user_int_records(records, user_id):
    history = []

    for record in records:
        if record["user_input"]["user_id"] == user_id:
            history.append({
                "sleep_duration": record["user_input"]["sleep_duration"],
                "focus_level": record["user_input"]["focus_level"],
                "stress_level": record["user_input"]["stress_level"],
                "social_activity_level":record["user_input"]["social_activity_level"],
                "mental_wellness_risk_score": record["ai_output"]["mental_wellness_risk_score"],
                "burnout_risk_score": record["ai_output"]["burnout_risk_score"]
            })

    return history

# Combine data from other layers to form a single record
def merge_record(user_input, ai_output, logic_output):
    record = {
    "user_input": user_input,
    "ai_output": ai_output,
    "logic_output": logic_output
    }
    return record

# Retrieves all past records for the user in order
def get_user_records(user_id, filename):
    records = load(filename)
    user_records = []

    for record in records:
        if record["user_input"]["user_id"] == user_id:
            user_records.append(record)

    user_records.sort(
        key=lambda record: datetime.strptime(
            f"{record['date']} {record['time']}",
            "%d-%m-%Y %H:%M:%S"
        ),
        reverse=True
    )

    return user_records

# Retrieves the latest record from the user
def get_latest_user_record(user_id, filename):
    user_records = get_user_records(user_id, filename)

    if not user_records:
        return None

    return user_records[0]

# Replaces a record from user from the same date
def replace_user_record(user_id, record, filename):
    records = load(filename)
    today = datetime.now().strftime("%d-%m-%Y")

    has_record_today = False
    updated_records = []

    for existing_record in records:
        same_user = existing_record["user_input"]["user_id"] == user_id
        same_date = existing_record["date"] == today

        if same_user and same_date:
            has_record_today = True
            continue

        updated_records.append(existing_record)

    if has_record_today:
        # Remove today's old record
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(updated_records, file, indent=4, ensure_ascii=False)

        # Save the replacement record
        save(record, filename)
    else:
        # No record exists for today, so save a new one
        save(record, filename)

# gets previous attempts of user
def get_previous_attempts(user_id, filename):
    today = datetime.now().date()
    user_records = get_user_records(user_id, filename)
    previous_attempts = []

    # Reverse the newest-first records into oldest-first order.
    for record in reversed(user_records):
        record_date = datetime.strptime(
            record["date"], "%d-%m-%Y"
        ).date()

        # Exclude today's old entry from comparisons.
        if record_date < today:
            previous_attempts.append({
                **record["user_input"],
                **record["ai_output"],
            })

    return previous_attempts


#Note that below is the required format for the return value for each of the 3 layers
#------------------------------------------------------------------------------
'''{
        "record_id": "58cf2be5-a36f-4849-944f-004c20ab96ba",
        "date": "12-10-2026",
        "time": "22:09:59",
        "user_input": {
            "user_id": "088c5abb-18d7-44d9-888b-2abca870e6bd",
            "sleep_duration": 1.0,
            "stress_level": 1,
            "focus_level": 1,
            "academic_workload": 1,
            "mood": "Motivated",
            "social_activity_level": 1,
            "reflection": "second"
        },
        "ai_output": {
            "burnout_risk_score": 50,
            "crisis_alert": true,
            "mental_wellness_risk_score": 85,
            "personalized_recommendations": "Your sleep duration of only one hour is critically low and poses an immediate danger to your physical and cognitive health. Please prioritize immediate rest or contact a medical professional, as your current level of sleep deprivation is unsustainable and requires urgent attention.",
            "primary_stressor": "Sleep Deprivation",
            "sentiment": "Neutral"
        },
        "logic_output": {
            "mental_wellness_risk_tier": "High",
            "warnings": [],
            "route": "Urgent support",
            "counselling_recommendation": true,
            "display_messages": [
                "You slept less than 7 hours. Try to get more sleep."
            ]
        }
    }'''
#------------------------------------------------------------------------------

# Main Function
if __name__ == "__main__":
    filename = "records.json"
    records = load(filename)
