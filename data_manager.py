import json
from datetime import datetime
import os
import uuid
from pathlib import Path
import shutil

# load function will read the data from the json database and load it into records
def load(filename):
    if os.path.exists(filename): 
        try:
            with open(filename,"r") as file:
                records = json.load(file)
        except json.JSONDecodeError:
            records = []
    else:
        records = []
        with open(filename,"w") as file:
            json.dump(records, file)
    return records

# save function will save the user_input, ai_ouput and logic_output into database as a single record
def save(record, filename):

    if Path(filename).is_file():
        backup_path = backup_json_file(filename)
    records = load(filename)
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

    with open(filename, "w") as file:
        json.dump(records, file, indent=4)

    print("Records saved successfully")

# query functions that can be used for filtering rows
def query(filter, filename):
    records = load(filename)

    matching_records = []

    for record in records:
        if filter(record):
            matching_records.append(record)

    return matching_records

# function will backup the JSON file into a folder and keep the latest 3 files
def backup_json_file(file_path: str, add_timestamp: bool=True) -> str:
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    backup_folder = path.parent / "Backup"
    backup_folder.mkdir(parents=True, exist_ok=True)

    if add_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{path.stem}_backup_{timestamp}{path.suffix}"
    else:
        backup_name = f"{path.stem}_backup{path.suffix}"

    backup_path = backup_folder / backup_name

    shutil.copy2(path, backup_path)

    backup_pattern = f"{path.stem}_backup_*{path.suffix}"
    backup_files = list(backup_folder.glob(backup_pattern))
    backup_files.sort(key=lambda file: file.name, reverse=True)

    for old_backup in backup_files[3:]:
        old_backup.unlink()

    return str(backup_path)

# get_user_history function will retrieve past records for selected columns for the current user
def get_user_int_records(records, user_id):
    history = []

    for record in records:
        if record["user_id"] == user_id:
            history.append({
                "sleep_duration": record["user_input"]["sleep_duration"],
                "focus_level": record["user_input"]["focus_level"],
                "social_activity_level": record["user_input"]["social_activity_level"],
                "mental_wellness_risk_score": record["ai_output"]["mental_wellness_risk_score"],
                "burnout_risk_score": record["ai_output"]["burnout_risk_score"]
            })

    return history

# merge_record function combine data from other layers to form 1 record
def merge_record(user_input, ai_output, logic_output):
    record = {
    "user_input": user_input,
    "ai_output": ai_output,
    "logic_output": logic_output
    }
    return record

# function that will be return all records from that user only
def get_user_records(user_id, filename):
    records = load(filename)
    user_records = []

    for record in records:
        if record["user_input"]["user_id"] == user_id:
            user_records.append(record)

    return user_records

# function that retrieves the latest record from the user
def get_latest_user_record(user_id, filename):
    user_records = get_user_records(user_id, filename)

    if not user_records:
        return None

    latest_record = max(
        user_records,
        key=lambda record: datetime.strptime(
            record["date"] + " " + record["time"],
            "%d-%m-%Y %H:%M:%S"
        )
    )

    return latest_record

# function that will display out the latest record on the screen nicely
def view_latest_assessment(user_id, filename):
    # retrieve the latest assessment record
    record = get_latest_user_record(user_id, filename)

    if record is None:
        print("\nNo assessment records found.")
        return

    user_input = record["user_input"]
    ai_output = record["ai_output"]
    logic_output = record["logic_output"]

    print("\n" + "=" * 50)
    print("          LATEST WELL-BEING ASSESSMENT")
    print("=" * 50)

    print(f"Record ID : {record['record_id']}")
    print(f"Date      : {record['date']}")
    print(f"Time      : {record['time']}")

    print("\n--- User Inputs ---")
    print(f"Sleep Duration       : {user_input['sleep_duration']} hours")
    print(f"Stress Level         : {user_input['stress_level']}/10")
    print(f"Focus Level          : {user_input['focus_level']}/10")
    print(f"Academic Workload    : {user_input['academic_workload']}/10")
    print(f"Mood                 : {user_input['mood']}")
    print(f"Social Activity      : {user_input['social_activity_level']}/10")
    print(f"Reflection           : {user_input['reflection']}")

    print("\n--- AI Assessment Results ---")
    print(f"Mental Wellness Risk : {ai_output['mental_wellness_risk_score']}/100")
    print(f"Burnout Risk Score   : {ai_output['burnout_risk_score']}/100")
    print(f"Sentiment            : {ai_output['sentiment']}")
    print(f"Crisis Alert         : {ai_output['crisis_alert']}")
    print(f"Primary Stressor     : {ai_output['primary_stressor']}")

    print("\n--- Business Rule Results ---")
    print(f"Risk Tier            : {logic_output['mental_wellness_risk_tier']}")
    print(f"Route                : {logic_output['route']}")

    print("Warnings:")
    warnings = logic_output.get("warnings", [])

    if warnings:
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("  - No warnings triggered")

    print(f"Counselling Required : {logic_output['counselling_recommendation']}")

    print("\n--- Personalised Recommendations ---")
    print(ai_output["personalized_recommendations"])

    print("=" * 50)

#Note that below is the required format for the return value for each of the 3 layers
#------------------------------------------------------------------------------
user_input = {
    "user_id": 1,
    "sleep_duration": 8,
    "stress_level": 2,
    "focus_level": 2,
    "academic_workload": 9,
    "mood": "Exhausted",
    "social_activity_level": 3,
    "reflection": "not enough sleep"
    }

ai_output = {
    "conversation_id": 10,
    "mental_wellness_risk_score": 78,
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
    }
#------------------------------------------------------------------------------


# Main Function
if __name__ == "__main__":
    filename = "records.json"
    records = load(filename)

    record = merge_record(user_input, ai_output, logic_output)

    #save(record, filename)
    #query(lambda record: record["user_input"]["stress"] > 8, filename)
    #get_user_history(records, user_id)
    view_latest_assessment(1, filename)