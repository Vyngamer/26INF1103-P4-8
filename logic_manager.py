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

# Apply business rules to user input and AI output, then return the assessment outcome.
def assess(user_input, ai_output):
    """Return the outcome derived from the validated AI fields and input."""
    tier = get_risk_tier(ai_output["mental_wellness_risk_score"])

    warnings = get_warnings(
        ai_output["sentiment"],
        ai_output["burnout_risk_score"],
        user_input["sleep_duration"],
        user_input["academic_workload"],
        user_input["social_activity_level"],
        user_input["focus_level"],
    )

    route = decide_route(ai_output, tier, warnings)

    return {
        "mental_wellness_risk_tier": tier,
        "warnings": warnings,
        "route": route,
        "counselling_recommendation": route in ("Urgent support", "Counsellor follow-up"),
    }
