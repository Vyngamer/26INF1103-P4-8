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

# function that will be return all records from that user only in order
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

# function that retrieves the latest record from the user
def get_latest_user_record(user_id, filename):
    user_records = get_user_records(user_id, filename)

    if not user_records:
        return None

    return user_records[0]

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

# function that will display all the assessment history
def view_assessment_history(user_id, filename):
    records = get_user_records(user_id, filename)

    if not records:
        print("\nNo assessment history found.")
        return

    print("\n" + "=" * 78)
    print("                     ASSESSMENT HISTORY")
    print("=" * 78)

    # Display table headings
    print(
        f"{'No.':<5}"
        f"{'Date':<14}"
        f"{'Time':<11}"
        f"{'Risk Score':<13}"
        f"{'Burnout':<11}"
        f"{'Risk Tier':<12}"
        f"{'Mood':<12}"
    )

    print("-" * 78)

    # Display each assessment
    for index, record in enumerate(records, start=1):
        user_input = record["user_input"]
        ai_output = record["ai_output"]
        logic_output = record["logic_output"]

        print(
            f"{index:<5}"
            f"{record['date']:<14}"
            f"{record['time']:<11}"
            f"{ai_output['mental_wellness_risk_score']:<13}"
            f"{ai_output['burnout_risk_score']:<11}"
            f"{logic_output['mental_wellness_risk_tier']:<12}"
            f"{user_input['mood']:<12}"
        )

    print("-" * 78)
    print(f"Total assessments: {len(records)}")
    print("=" * 78)

def compare_assessments(user_id, filename):
    records = get_user_records(user_id, filename)

    if len(records) < 2:
        print("\nYou need at least 2 assessments to compare.")
        return

    # Records are sorted newest first
    latest = records[0]
    previous = records[1]

    latest_input = latest["user_input"]
    previous_input = previous["user_input"]

    latest_ai = latest["ai_output"]
    previous_ai = previous["ai_output"]

    latest_logic = latest["logic_output"]
    previous_logic = previous["logic_output"]

    print("\n" + "=" * 85)
    print(" " * 25 + "ASSESSMENT COMPARISON")
    print("=" * 85)

    print(f"{'Information':<25}{'Previous Assessment':<25}{'Latest Assessment':<25}")
    print("-" * 85)

    # Assessment dates
    print(
        f"{'Date':<25}"
        f"{previous['date']:<25}"
        f"{latest['date']:<25}"
    )

    # User inputs
    print(
        f"{'Sleep Duration':<25}"
        f"{str(previous_input['sleep_duration']) + ' hours':<25}"
        f"{str(latest_input['sleep_duration']) + ' hours':<25}"
    )

    print(
        f"{'Stress Level':<25}"
        f"{str(previous_input['stress_level']) + '/10':<25}"
        f"{str(latest_input['stress_level']) + '/10':<25}"
    )

    print(
        f"{'Focus Level':<25}"
        f"{str(previous_input['focus_level']) + '/10':<25}"
        f"{str(latest_input['focus_level']) + '/10':<25}"
    )

    print(
        f"{'Academic Workload':<25}"
        f"{str(previous_input['academic_workload']) + '/10':<25}"
        f"{str(latest_input['academic_workload']) + '/10':<25}"
    )

    print(
        f"{'Social Activity':<25}"
        f"{str(previous_input['social_activity_level']) + '/10':<25}"
        f"{str(latest_input['social_activity_level']) + '/10':<25}"
    )

    print(
        f"{'Mood':<25}"
        f"{previous_input['mood']:<25}"
        f"{latest_input['mood']:<25}"
    )

    # AI results
    print("-" * 85)

    print(
        f"{'Mental Wellness Risk':<25}"
        f"{str(previous_ai['mental_wellness_risk_score']) + '/100':<25}"
        f"{str(latest_ai['mental_wellness_risk_score']) + '/100':<25}"
    )

    print(
        f"{'Burnout Risk':<25}"
        f"{str(previous_ai['burnout_risk_score']) + '/100':<25}"
        f"{str(latest_ai['burnout_risk_score']) + '/100':<25}"
    )

    print(
        f"{'Sentiment':<25}"
        f"{previous_ai['sentiment']:<25}"
        f"{latest_ai['sentiment']:<25}"
    )

    print(
        f"{'Risk Tier':<25}"
        f"{previous_logic['mental_wellness_risk_tier']:<25}"
        f"{latest_logic['mental_wellness_risk_tier']:<25}"
    )

    print(
        f"{'Crisis Alert':<25}"
        f"{str(previous_ai['crisis_alert']):<25}"
        f"{str(latest_ai['crisis_alert']):<25}"
    )

    print(
        f"{'Counselling Required':<25}"
        f"{str(previous_logic['counselling_recommendation']):<25}"
        f"{str(latest_logic['counselling_recommendation']):<25}"
    )

    print("=" * 85)

    # Risk score changes
    risk_change = (
        latest_ai["mental_wellness_risk_score"]
        - previous_ai["mental_wellness_risk_score"]
    )

    burnout_change = (
        latest_ai["burnout_risk_score"]
        - previous_ai["burnout_risk_score"]
    )

    print("\n--- Changes Since Previous Assessment ---")

    if risk_change > 0:
        print(f"Mental wellness risk increased by {risk_change} points.")
    elif risk_change < 0:
        print(f"Mental wellness risk decreased by {abs(risk_change)} points.")
    else:
        print("Mental wellness risk remained unchanged.")

    if burnout_change > 0:
        print(f"Burnout risk increased by {burnout_change} points.")
    elif burnout_change < 0:
        print(f"Burnout risk decreased by {abs(burnout_change)} points.")
    else:
        print("Burnout risk remained unchanged.")

    print("=" * 85)

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
    #view_assessment_history(1, filename)
    compare_assessments(1,filename)