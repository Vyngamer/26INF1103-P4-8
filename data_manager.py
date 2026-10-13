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

# Retrieves past records for selected columns for analysis
def get_user_int_records(records, user_id):
    history = []

    for record in records:
        if record["user_input"]["user_id"] == user_id:
            history.append({
                "sleep_duration": record["user_input"]["sleep_duration"],
                "focus_level": record["user_input"]["focus_level"],
                "stress_level": record["user_input"]["stress_level"],
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

# Retrieves selected fields from a past records from the user
def get_user_records_by_columns(user_id, filename, columns):
    records = get_user_records(user_id, filename)
    selected_records = []

    for record in records:
        selected_record = {}

        for column in columns:
            value = record

            for part in column.split("."):
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break

            selected_record[column] = value

        selected_records.append(selected_record)

    return selected_records

# Replaces a record from user from the same date
def replace_user_record(user_id, record, filename):
    records = load(filename)
    today = datetime.now().strftime("%d-%m-%Y")

    # Keep records belonging to other users and other dates
    updated_records = []

    for existing_record in records:
        same_user = existing_record["user_input"]["user_id"] == user_id
        same_date = existing_record["date"] == today

        if same_user and same_date:
            continue

        updated_records.append(existing_record)

    # Save the records after removing today's old record
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(updated_records, file, indent=4, ensure_ascii=False)

    # Create the new record
    save(record, filename)


#Note that below is the required format for the return value for each of the 3 layers
#------------------------------------------------------------------------------
'''user_input = {
    "user_id": 1,
    "sleep_duration": 7,
    "stress_level": 2,
    "focus_level": 2,
    "academic_workload": 9,
    "mood": "Exhausted",
    "social_activity_level": 3,
    "reflection": "not enough sleep"
    }

ai_output = {
    "conversation_id": 10,
    "mental_wellness_risk_score": 1,
    "sentiment": "Negative",
    "burnout_risk_score": 82,
    "crisis_alert": False,
    "primary_stressor": "Assignment deadlines",
    "personalized_recommendations": "Prioritise sleep and manage deadlines."
    }

logic_output = {
    "mental_wellness_risk_tier": "High",
    "warnings": ["High Burnout Warning"],
    "route": "Urgent support",
    "counselling_recommendation": True
    }'''
#------------------------------------------------------------------------------

# Main Function
if __name__ == "__main__":
    filename = "records.json"
    records = load(filename)

    #record = merge_record(user_input, ai_output, logic_output)
    #replace_user_record(1, record, filename)
    