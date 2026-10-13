'''
Functionality for user to view and delete history
'''
import json
import os
from datetime import datetime
from data_manager import backup_json_file, get_latest_user_record, get_user_records, load, merge_record
from title import print_title

#Display the latest record on the screen nicely
def view_latest_assessment(user_id, filename, messages = {}):
    # retrieve the latest assessment record
    record = get_latest_user_record(user_id, filename)

    if record is None:
        print("\nNo assessment records found.")
        return

    view_assessment_details(record, "LATEST WELL-BEING ASSESSMENT")

#Display a selected record on the screen
def view_assessment_details(record, title="ASSESSMENT DETAILS"):
    user_input = record["user_input"]
    ai_output = record["ai_output"]
    logic_output = record["logic_output"]

    width = 50
    print_title(title,width)

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

    messages = logic_output.get("display_messages", [])
    if messages:
        for msg in messages:
            print(f"  - {msg}")

    print("=" * width)

#Return all of the user's records dated today (newest first)
def get_todays_records(user_id, filename):
    today = datetime.now().strftime("%d-%m-%Y")
    return [record for record in get_user_records(user_id, filename) if record["date"] == today]

#Delete user records using user id
#Returns how many records were deleted. A backup of the file is made before deleting.
def delete_records(record_ids, user_id, filename):
    record_ids = [record_id for record_id in record_ids if record_id is not None]
    records = load(filename)

    remaining = [
        record for record in records
        if not (record.get("record_id") in record_ids
                and (record.get("user_input") or {}).get("user_id") == user_id)
    ]

    deleted = len(records) - len(remaining)
    if deleted == 0:
        return 0

    backup_json_file(filename)

    # write to a temp file first so crash can't leave half-written records file
    temp_file = filename + ".tmp"
    with open(temp_file, "w") as file:
        json.dump(remaining, file, indent=4)
    os.replace(temp_file, filename)

    return deleted

#Display full assessment history
def view_assessment_history(user_id, filename):
    records = get_user_records(user_id, filename)

    if not records:
        print("\nNo assessment history found.")
        return

    title = "ASSESSMENT HISTORY"
    width = 78
    print_title(title,width)

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

    print("-" * width)

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

    print("-" * width)
    print(f"Total assessments: {len(records)}")
    print("=" * width)

#Compare 2 most recent records and show changes in mental wellness risk score & burnout risk score
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

    title = "ASSESSMENT COMPARISON"
    width = 85
    print_title(title,width)

    print(f"{'Information':<25}{'Previous Assessment':<25}{'Latest Assessment':<25}")
    print("-" * width)

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
    print("-" * width)

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

    print("=" * width)

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

    print("=" * width)

#Overall summary of assessments
def view_wellbeing_summary(user_id, filename):
    records = get_user_records(user_id, filename)

    if not records:
        print("\nNo assessment records found.")
        return

    # Records are sorted newest first
    latest = records[0]
    latest_ai = latest["ai_output"]
    latest_logic = latest["logic_output"]

    # Calculate average scores across all assessments
    total_risk = 0
    total_burnout = 0

    for record in records:
        ai_output = record["ai_output"]
        total_risk += ai_output["mental_wellness_risk_score"]
        total_burnout += ai_output["burnout_risk_score"]

    average_risk = total_risk / len(records)
    average_burnout = total_burnout / len(records)

    # Display summary
    title = "WELL-BEING SUMMARY"
    width = 55
    print_title(title,width)

    print("\n--- Assessment History ---")
    print(f"Total Assessments      : {len(records)}")
    print(f"First Assessment       : {records[-1]['date']}")
    print(f"Latest Assessment      : {latest['date']}")

    print("\n--- Latest Results ---")
    print(
        f"Mental Wellness Risk   : "
        f"{latest_ai['mental_wellness_risk_score']}/100"
    )
    print(f"Burnout Risk           : {latest_ai['burnout_risk_score']}/100")
    print(f"Risk Tier              : {latest_logic['mental_wellness_risk_tier']}")
    print(f"Mood                   : {latest['user_input']['mood']}")

    print("\n--- Average Scores ---")
    print(f"Average Risk Score     : {average_risk:.1f}/100")
    print(f"Average Burnout Score  : {average_burnout:.1f}/100")

    # Compare latest and previous assessments
    print("\n--- Recent Changes ---")

    if len(records) < 2:
        print("Complete another assessment to see recent changes.")
    else:
        previous_ai = records[1]["ai_output"]

        risk_change = (
            latest_ai["mental_wellness_risk_score"]
            - previous_ai["mental_wellness_risk_score"]
        )

        burnout_change = (
            latest_ai["burnout_risk_score"]
            - previous_ai["burnout_risk_score"]
        )

        print(f"Mental Wellness Risk   : {risk_change:+} points")
        print(f"Burnout Risk           : {burnout_change:+} points")

        if risk_change > 0:
            print("Risk Trend             : Increasing")
        elif risk_change < 0:
            print("Risk Trend             : Decreasing")
        else:
            print("Risk Trend             : Unchanged")

    print("=" * width)

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
    #view_wellbeing_summary(1,filename)