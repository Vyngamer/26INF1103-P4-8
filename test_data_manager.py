import uuid

from data_manager import DataManager


# =========================================================
# TESTING
# =========================================================

if __name__ == "__main__":

    # Initialise DataManager
    data_manager = DataManager()

    try:

        print("\n========== USER TESTING ==========")

        # 1. Create a test user
        username = "test_user_" + str(uuid.uuid4())[:8]

        # Replace this with a properly hashed test password
        hashed_password = "test_hashed_password"

        user_id = data_manager.create_user(
            username,
            hashed_password
        )

        if user_id:
            print("User created successfully!")
            print("User ID:", user_id)
            print("Username:", username)
        else:
            print("Failed to create user.")
            raise Exception("Cannot continue without a test user.")

        # 2. Retrieve user by ID
        print("\n--- Retrieve User By ID ---")

        user = data_manager.get_user_by_id(user_id)

        if user:
            print("User ID:", user.get_user_id())
            print("Username:", user.get_username())
        else:
            print("User not found.")

        # 3. Retrieve user by username
        print("\n--- Retrieve User By Username ---")

        user = data_manager.get_user_by_username(username)

        if user:
            print("Found user:", user.get_username())
        else:
            print("User not found.")

        print("\n========== ASSESSMENT TESTING ==========")

        # 4. Create assessment input
        user_input = {
            "user_id": user_id,
            "sleep_duration": 7,
            "stress_level": 3,
            "focus_level": 4,
            "academic_workload": 3,
            "social_activity_level": 4,
            "mood": "Motivated",
            "reflection": "I feel quite productive today."
        }

        ai_output = {
            "burnout_risk_score": 20,
            "mental_wellness_risk_score": 25,
            "sentiment": "Positive",
            "crisis_alert": False,
            "primary_stressor": "Academic workload",
            "personalized_recommendations": "Maintain a consistent sleep schedule."
        }

        logic_output = {
            "mental_wellness_risk_tier": "Low",
            "warnings": [],
            "route": "Urgent support",
            "counselling_recommendation": False,
            "display_messages": [
                "You slept less than 7 hours. Try to get more sleep."
            ]
        }

        # 5. Merge assessment data into an AssessmentRecord
        assessment = data_manager.merge_record(
            user_input,
            ai_output,
            logic_output
        )

        # 6. Save assessment record
        success = data_manager.save(assessment)

        if success:
            print("Assessment saved successfully!")
            print("Record ID:", assessment.get_record_id())
            print("User ID:", assessment.get_user_input()["user_id"])
            print("Date:", assessment.get_date())
            print("Time:", assessment.get_time())
        else:
            print("Failed to save assessment.")

        # 7. Retrieve all assessments belonging to this user
        print("\n--- User Assessment History ---")

        records = data_manager.get_user_records(user_id)

        for record in records:
            print("Record ID:", record.get_record_id())
            print("Date:", record.get_date())
            print(
                "Stress Level:",
                record.get_user_input()["stress_level"]
            )
            print(
                "Risk Score:",
                record.get_ai_output()["mental_wellness_risk_score"]
            )
            print("----------------------------")

        # 8. Retrieve latest assessment
        print("\n--- Latest Assessment ---")

        latest = data_manager.get_latest_user_record(user_id)

        if latest:
            print("Latest Record ID:", latest.get_record_id())
            print("Date:", latest.get_date())
            print(
                "Risk Score:",
                latest.get_ai_output()["mental_wellness_risk_score"]
            )
        else:
            print("No assessment found.")

        # 9. Retrieve previous attempts
        print("\n--- Previous Attempts ---")

        previous_attempts = data_manager.get_previous_attempts(user_id)

        print("Number of previous attempts:", len(previous_attempts))

        for attempt in previous_attempts:
            print(attempt)

        # 10. Extract numerical assessment data
        print("\n--- Numerical Assessment Data ---")

        int_records = data_manager.get_user_int_records(
            records,
            user_id
        )

        for record in int_records:
            print(record)

        # 11. Update user
        print("\n========== UPDATE USER ==========")

        updated_username = username + "_updated"

        update_success = data_manager.update_user(
            user_id,
            {"username": updated_username}
        )

        if update_success:
            print("Username updated successfully!")
        else:
            print("Failed to update username.")

        # Verify updated username
        updated_user = data_manager.get_user_by_id(user_id)

        if updated_user:
            print("Updated username:", updated_user.get_username())

        # 12. Replace today's assessment
        print("\n========== REPLACE TODAY'S ASSESSMENT ==========")

        updated_ai_output = ai_output.copy()

        updated_ai_output["mental_wellness_risk_score"] = 40

        replacement_assessment = data_manager.merge_record(
            user_input,
            updated_ai_output,
            logic_output
        )

        replace_success = data_manager.replace_user_record(
            user_id,
            replacement_assessment
        )

        if replace_success:
            print("Today's assessment replaced successfully!")
        else:
            print("Failed to replace today's assessment.")

        # Verify replacement
        latest = data_manager.get_latest_user_record(user_id)

        if latest:
            print(
                "Updated risk score:",
                latest.get_ai_output()["mental_wellness_risk_score"]
            )

        # 13. Delete test user
        # Uncomment when you are ready to delete the test user.

        # print("\n========== DELETE USER ==========")
        # delete_success = data_manager.delete_user(user_id)
        #
        # if delete_success:
        #     print("Test user deleted successfully!")
        # else:
        #     print("Failed to delete test user.")

    finally:
        # Close MongoDB connection
        data_manager.close()

        print("\nMongoDB connection closed.")
