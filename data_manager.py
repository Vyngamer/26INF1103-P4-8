import json
from datetime import datetime
import pandas as pd
import os
import uuid
from pathlib import Path
import shutil

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
    
def save(record, filename):
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

    return print(f"Records has been saved in {filename}")

def query(filter, filename):
    records = load(filename)

    matching_records = []

    for record in records:
        if filter(record):
            matching_records.append(record)

    return matching_records

def query_pd(filter, filename, columns=None):
    records = load(filename)

    df = pd.json_normalize(records)

    matching_records = df[filter(df)]

    if columns:
        matching_records = matching_records.loc[:, columns]

    return matching_records

def backup_json_file(file_path: str, add_timestamp: bool=True) -> str:
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    if add_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{path.stem}_backup_{timestamp}{path.suffix}"
    else:
        backup_name = f"{path.stem}_backup{path.suffix}"

    backup_path = path.parent / backup_name

    shutil.copy2(path, backup_path)
    return str(backup_path) 

# Main Function

filename = "records.json"
load(filename)

#Note that below is the required format for the return value for each of the 3 layers
user_input = {
    "sleep_duration": 5,
    "stress_level": 1,
    "focus_level": 2,
    "academic_workload": 9,
    "mood": "Exhausted",
    "social_activity_level": 3,
    "reflection": "im feeling too stressed already"
    }

ai_output = {
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
    "counselling_recommendation": True
    }

#Need to insert in the actual functions from other layers
record = {
    "user_input": user_input,
    "ai_output": ai_output,
    "logic_output": logic_output
    }

save(record, filename)

# filter normal query
'''results = query(
    lambda record: record["user_input"]["stress_level"] > 8,
    filename
)

print(results)'''

# filter query using pandas
'''results = query_pd(
    lambda df: df["user_input.stress_level"] >= 8,
    filename,
    columns=["record_id", "date", "time", "user_input.reflection"]
    )

print(results)
'''


backup_file = backup_json_file("records.json")
print(f"Backup saved to: {backup_file}")