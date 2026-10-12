# function to get risk tier based on mental wellness risk score
def get_risk_tier(risk_score):
    if risk_score >= 71:
        tier = "High"
    elif risk_score >= 41:
        tier = "Medium"
    else:
        tier = "Low"
    return tier

# function to get warnings based on various factors
def get_warnings(sentiment_analysis, burnout_risk_score, sleep, workload, social_activity_level, focus):
    warnings = []
    # check for high burnout warning due to sleep
    if burnout_risk_score > 75 and sleep < 6:
        warnings.append("High burnout warning (Sleep)")
    # check for burnout warning due to workload
    if burnout_risk_score > 60 and workload >= 7:
        warnings.append("Burnout warning (Workload)")

    # check for social withdrawal risk
    if social_activity_level <= 3 and sentiment_analysis == "Negative":
        warnings.append("social withdrawal risk")

    # check for cognitive fatigue risk
    if focus <= 4 and sentiment_analysis == "Negative":
        warnings.append("cognitive fatigue risk")
    return warnings

# Choose a support route based on AI results, risk tier, and warnings.
def decide_route(ai_output, tier, warnings):
    """Choose one actionable outcome from the AI assessment and warnings."""
    if ai_output["crisis_alert"]:
        return "Urgent support"

    # This rule combines three distinct AI output fields.
    combined_risk = (
        ai_output["mental_wellness_risk_score"] >= 60
        and ai_output["burnout_risk_score"] >= 70
        and ai_output["sentiment"] == "Negative"
    )
    # Recommend counsellor follow-up if the tier is High, there are at least two warnings, or combined risk is present.
    if tier == "High" or len(warnings) >= 2 or combined_risk:
        return "Counsellor follow-up"

    return "Self-care guidance"

# Calculate the average of a field across previous attempts.
def get_average(previous_attempts, field):
    sum=0
    for attempt in previous_attempts:
        if field not in ['mental_wellness_risk_score','burnout_risk_score']:
            sum += attempt["user_input"][field]
        else:
            sum += attempt["ai_output"][field]
    return sum/len(previous_attempts)
    
    # average = sum(attempt[field] for attempt in previous_attempts) / len(previous_attempts)
    # return average

# Remind the user to sleep more if sleep is below 7 hours.
def check_sleep(sleep_duration):
    if sleep_duration < 7:
        return ["You slept less than 7 hours. Try to get more sleep."]
    return []

# Shows how much sleep the user has compared to their average.
def compare_sleep(previous_attempts, sleep_duration):
    if not previous_attempts:
        return []

    average = get_average(previous_attempts, "sleep_duration")
    difference = average - sleep_duration

    if difference > 0:
        return [f"You slept {difference:.2f} hours less than your average."]
    elif difference < 0:
        return [f"You slept {abs(difference):.2f} hours more than your average."]

    return ["You slept the same number of hours as your average."]

# Prioritise showing consecutive social decline. If not, then compare with the previous average.
def compare_social(previous_attempts, social_activity_level):
    if not previous_attempts:
        return []

    # Check for three drops of at least 1 point across four consecutive attempts.
    if len(previous_attempts) >= 3:
        first = previous_attempts[-3]["user_input"]["social_activity_level"]
        second = previous_attempts[-2]["user_input"]["social_activity_level"]
        third = previous_attempts[-1]["user_input"]["social_activity_level"]

        consecutive_drop = (
            first - second >= 1
            and second - third >= 1
            and third - social_activity_level >= 1
        )

        if consecutive_drop:
            return ["Your social activity has dropped across four consecutive attempts. Try connecting with others."]

    average = get_average(previous_attempts, "social_activity_level")

    if average - social_activity_level >= 2:
        return ["You are socialising less than your previous average. Try connecting with others."]

    return []

# Show a focus message which priortise the latest attempt over the average.
def compare_focus(previous_attempts, focus_level):
    if not previous_attempts:
        return []

    previous = previous_attempts[-1]["user_input"]["focus_level"]

    # Show a negative message for a drop of at least 2 from the latest attempt.
    if previous - focus_level >= 2:
        return ["Your focus level has dropped since your last attempt. Try taking a break and resting."]

    # Show a positive message for an increase of at least 1 from the latest attempt.
    if focus_level - previous >= 1:
        return ["Your focus level has improved since your last attempt. Keep it up!"]

    # Compare with the average if neither latest-attempt rule matches.
    average = get_average(previous_attempts, "focus_level")

    if average - focus_level >= 2:
        return ["Your focus level is below your previous average. Try taking a break and resting."]

    if focus_level - average >= 1:
        return ["Your focus level has improved compared with your previous average. Keep it up!"]

    return []

# a function that compares scores based on what argument you give
def compare_risk_score(previous_attempts, risk_score, field, label):
    if not previous_attempts:
        return []

    previous = previous_attempts[-1]["ai_output"][field]

    # No improvement messages if risk increased since the latest attempt.
    if risk_score > previous:
        return []

    # A decrease of at least 10 points indicates improvement.
    if previous - risk_score >= 10:
        return [f"Your {label} risk score has improved since your last attempt. Keep it up!"]

    average = get_average(previous_attempts, field)

    if average - risk_score >= 10:
        return [f"Your {label} risk score has improved compared with your previous average. Keep it up!"]

    return []

# a function that checks if the mental wellness score has improved
def compare_mental_wellness(previous_attempts, mental_wellness_risk_score):
    return compare_risk_score(
        previous_attempts,
        mental_wellness_risk_score,
        "mental_wellness_risk_score",
        "mental wellness",
    )

# a function that checks if the burnout score has improved
def compare_burnout(previous_attempts, burnout_risk_score):
    return compare_risk_score(
        previous_attempts,
        burnout_risk_score,
        "burnout_risk_score",
        "burnout",
    )

# Apply business rules to user input and AI output, then return the assessment outcome.
def assess(user_input, ai_output, previous_attempts):
    tier = get_risk_tier(ai_output["mental_wellness_risk_score"])

    print(previous_attempts)
    warnings = get_warnings(
        ai_output["sentiment"],
        ai_output["burnout_risk_score"],
        user_input["sleep_duration"],
        user_input["academic_workload"],
        user_input["social_activity_level"],
        user_input["focus_level"],
    )
# Assign a support route using AI output, mental_wellness risk tier and warnings
    route = decide_route(ai_output, tier, warnings)

    display_messages = (
        check_sleep(user_input["sleep_duration"])
        + compare_sleep(
            previous_attempts, user_input["sleep_duration"]
        )
        + compare_social(
            previous_attempts, user_input["social_activity_level"]
        )
        + compare_focus(
            previous_attempts, user_input["focus_level"]
        )
        + compare_mental_wellness(
            previous_attempts, ai_output["mental_wellness_risk_score"]
        )
        + compare_burnout(
            previous_attempts, ai_output["burnout_risk_score"]
        )
    )

    return {
        "mental_wellness_risk_tier": tier,
        "warnings": warnings,
        "route": route,
        "counselling_recommendation": route in ("Urgent support", "Counsellor follow-up"),
        "display_messages": display_messages,
    }
