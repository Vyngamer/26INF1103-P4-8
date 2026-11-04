'''
Functionality for user to view history
'''

from abc import ABC, abstractmethod
from datetime import datetime
from data_manager import get_user_records
from console import Console


# One user's saved assessments in a records file
class AssessmentHistory:
    DATE_FORMAT = "%d-%m-%Y"

    def __init__(self, user_id, filename):
        self.user_id = user_id
        self.filename = filename

    #All of the user's records (newest first)
    def records(self):
        return get_user_records(self.user_id, self.filename)

    '''
    #The newest record, or None if there are none
    def latest(self):
        records = self.records()
        return records[0] if records else None
    '''

    #Return all of the user's records dated today (newest first)
    def todays_records(self):
        today = datetime.now().strftime(self.DATE_FORMAT)
        return [record for record in self.records() if record["date"] == today]


# Abstract base class for a titled report printed to the console
class ReportView(ABC):
    def __init__(self, title, width):
        self.title = title
        self.width = width

    def show(self):
        Console.title(self.title, self.width)
        self.render_body()
        print("=" * self.width)

    @abstractmethod
    def render_body(self):
        pass


# Originally view_assessment_details()
# Display one record on the screen
class AssessmentDetailView(ReportView):
    def __init__(self, record, title="ASSESSMENT DETAILS"):
        super().__init__(title, Console.DEFAULT_WIDTH)
        self.record = record

    def render_body(self):
        record = self.record
        user_input = record["user_input"]
        ai_output = record["ai_output"]
        logic_output = record["logic_output"]

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

        print("\n--- Risk Evaluation & Support Guidance ---")
        print(f"Risk Tier            : {logic_output['mental_wellness_risk_tier']}")
        print(f"Route                : {logic_output['route']}")

        print("Warnings:")
        warnings = logic_output.get("warnings", [])

        if warnings:
            for warning in warnings:
                print(f"  - {warning}")
        else:
            print("  - No warnings triggered")

        print(f"Counselling Required : {"Yes" if logic_output['counselling_recommendation'] else "No"}")

        print("\n--- Personalised Recommendations ---")
        print(ai_output["personalized_recommendations"])

        print("\n--- Historical Insights ---")
        messages = logic_output.get("display_messages", [])
        if messages:
            for msg in messages:
                print(f"  - {msg}")
        else:
            print("  - No historical insights available.")


# Originally view_assessment_history()
# Table of all of a user's assessments
class AssessmentHistoryTable(ReportView):
    def __init__(self, records):
        super().__init__("ASSESSMENT HISTORY", 78)
        self.records = records

    def render_body(self):
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

        print("-" * self.width)

        # Display each assessment
        for index, record in enumerate(self.records, start=1):
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

        print("-" * self.width)
        print(f"Total assessments: {len(self.records)}")

'''
Note that below is the required format for the return value for each of the 3 layers
------------------------------------------------------------------------------
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
------------------------------------------------------------------------------
'''