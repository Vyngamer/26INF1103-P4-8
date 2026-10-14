import pytest

from logic_manager import (get_risk_tier, get_warnings, decide_route, check_sleep,
                           compare_sleep, compare_social, compare_focus, compare_risk_score,
                           compare_mental_wellness, compare_burnout, assess)


# create scores to test get_risk_tier
@pytest.mark.parametrize(
    "score, expected",
    [
        # test cases to test Low
        (0, "Low"),
        (40, "Low"),
        (-1, "Low"),
        # test cases to test Medium
        (41, "Medium"),
        (50, "Medium"),
        (70, "Medium"),
        # test cases to test High
        (71, "High"),
        (85, "High"),
        (100, "High")
        # test cases to test out of range
    ],
)

# function to use the above values to test
def test_get_risk_tier(score, expected):
    assert get_risk_tier(score) == expected


# create values to test get_warnings function
@pytest.mark.parametrize(
    "senti, burnout_score, sleep, workload, social_activity_level, focus, expected",
    [
        # test cases to get high burnout
        ("Positive", 76, 5, 5, 8, 8, ["High Burnout Warning (Sleep)"]),
        ("Negative", 75, 6, 5, 8, 8, []),
        ("Positive", 80, 4, 5, 8, 8, ["High Burnout Warning (Sleep)"]),
        # test cases to get burnout warning (workload)
        ("Positive", 61, 8, 7, 8, 8, ["Burnout Warning (Workload)"]),
        ("Positive", 60, 8, 6, 8, 8, []),
        ("Positive", 75, 8, 8, 8, 8, ["Burnout Warning (Workload)"]),
        # test cases to get social withdrawal
        ("Negative", 55, 8, 8, 3, 5, ["Social Withdrawal Risk"]),
        ("Positive", 55, 8, 8, 3, 5, []),
        ("Negative", 55, 8, 8, 2, 5, ["Social Withdrawal Risk"]),
        # test cases to get cognitive fatigue risks
        ("Negative", 55, 8, 8, 4, 4, ["Cognitive Fatigue Risk"]),
        ("Positive", 55, 8, 8, 4, 5, []),
        ("Negative", 55, 8, 8, 4, 3, ["Cognitive Fatigue Risk"]),
        # test cases to get multiple risks
        ("Negative", 84, 4, 8, 2, 3, ["High Burnout Warning (Sleep)", "Burnout Warning (Workload)", "Social Withdrawal Risk", "Cognitive Fatigue Risk"]),
        ("Negative", 84, 7, 8, 2, 3, ["Burnout Warning (Workload)", "Social Withdrawal Risk", "Cognitive Fatigue Risk"]),
        ("Negative", 84, 5, 8, 2, 6, ["High Burnout Warning (Sleep)", "Burnout Warning (Workload)", "Social Withdrawal Risk"]),
        ("Positive", 84, 5, 8, 2, 3, ["High Burnout Warning (Sleep)", "Burnout Warning (Workload)"])
    ]
) # senti, burnout_score, sleep,
  # workload, social_activity_level, focus, expected

def test_get_warnings(senti, burnout_score, sleep, workload, social_activity_level, focus, expected):
    assert get_warnings(senti, burnout_score, sleep, workload, social_activity_level, focus) == expected



# test cases for decide route function
@pytest.mark.parametrize(
    "ai_output, tier, warnings, expected",
    [
        # test cases to get urgent support
        ({"burnout_risk_score": 50,"crisis_alert": True,"mental_wellness_risk_score": 85,"personalized_recommendations": "Your sleep duration of only one hour is critically low and poses an immediate danger to your physical and cognitive health. Please prioritize immediate rest or contact a medical professional, as your current level of sleep deprivation is unsustainable and requires urgent attention.","primary_stressor": "Sleep Deprivation","sentiment": "Neutral"}, "High", [], "Urgent support"),
        # test cases to get counsellor follow-up
        ({"burnout_risk_score": 50,"crisis_alert": False,"mental_wellness_risk_score": 85,"personalized_recommendations": "Your sleep duration of only one hour is critically low and poses an immediate danger to your physical and cognitive health. Please prioritize immediate rest or contact a medical professional, as your current level of sleep deprivation is unsustainable and requires urgent attention.","primary_stressor": "Sleep Deprivation","sentiment": "Neutral"}, "High", [], "Counsellor follow-up"),
        ({"burnout_risk_score": 50,"crisis_alert": False,"mental_wellness_risk_score": 55,"personalized_recommendations": "Your sleep duration of only one hour is critically low and poses an immediate danger to your physical and cognitive health. Please prioritize immediate rest or contact a medical professional, as your current level of sleep deprivation is unsustainable and requires urgent attention.","primary_stressor": "Sleep Deprivation","sentiment": "Neutral"}, "Low", ["High Burnout Warning (Sleep)", "Burnout Warning (Workload)"], "Counsellor follow-up"),
        ({"burnout_risk_score": 70,"crisis_alert": False,"mental_wellness_risk_score": 60,"personalized_recommendations": "Your sleep duration of only one hour is critically low and poses an immediate danger to your physical and cognitive health. Please prioritize immediate rest or contact a medical professional, as your current level of sleep deprivation is unsustainable and requires urgent attention.","primary_stressor": "Sleep Deprivation","sentiment": "Negative"}, "Low", [], "Counsellor follow-up"),
        # test for self-care guidance
        ({"burnout_risk_score": 50,"crisis_alert": False,"mental_wellness_risk_score": 85,"personalized_recommendations": "Your sleep duration of only one hour is critically low and poses an immediate danger to your physical and cognitive health. Please prioritize immediate rest or contact a medical professional, as your current level of sleep deprivation is unsustainable and requires urgent attention.","primary_stressor": "Sleep Deprivation","sentiment": "Neutral"}, "Low", [], "Self-care guidance")
    ]
)

def test_decide_route(ai_output, tier, warnings, expected):
    assert decide_route(ai_output, tier, warnings) == expected


# test cases to check check_sleep function
@pytest.mark.parametrize(
    "sleep_duration, expected",
    [
        # testcase to get sleep_duration
        (6.9, ["You slept less than 7 hours. Try to get more sleep."]),
        (7, [])
    ]
)

def test_check_sleep(sleep_duration, expected):
    assert check_sleep(sleep_duration) == expected

def attempts(field, values):
    return [{field: v} for v in values]

# initialise any dummy data that we will need
previous_attemps = [
    {
        "user_id": 1,
        "sleep_duration": 5,
        "stress_level": 5,
        "focus_level": 5,
        "academic_workload": 9,
        "mood": "Exhausted",
        "social_activity_level": 6,
        "reflection": "im feeling too stressed already",
        "conversation_id": 10,
        "mental_wellness_risk_score": 78,
        "sentiment": "Negative",
        "burnout_risk_score": 82,
        "crisis_alert": False,
        "primary_stressor": "Assignment deadlines",
        "personalized_recommendations": "Prioritise sleep and manage deadlines."
    },
    {
        "user_id": 1,
        "sleep_duration": 5,
        "stress_level": 8,
        "focus_level": 5,
        "academic_workload": 9,
        "mood": "Exhausted",
        "social_activity_level": 5,
        "reflection": "im feeling too stressed already",
        "conversation_id": 10,
        "mental_wellness_risk_score": 78,
        "sentiment": "Negative",
        "burnout_risk_score": 82,
        "crisis_alert": False,
        "primary_stressor": "Assignment deadlines",
        "personalized_recommendations": "Prioritise sleep and manage deadlines."
    },
    {
        "user_id": 1,
        "sleep_duration": 5,
        "stress_level": 5,
        "focus_level": 5,
        "academic_workload": 9,
        "mood": "Exhausted",
        "social_activity_level": 4,
        "reflection": "im feeling too stressed already",
        "conversation_id": 10,
        "mental_wellness_risk_score": 78,
        "sentiment": "Negative",
        "burnout_risk_score": 82,
        "crisis_alert": False,
        "primary_stressor": "Assignment deadlines",
        "personalized_recommendations": "Prioritise sleep and manage deadlines."
    },
    {
        "user_id": 1,
        "sleep_duration": 5,
        "stress_level": 5,
        "focus_level": 6,
        "academic_workload": 9,
        "mood": "Exhausted",
        "social_activity_level": 3,
        "reflection": "im feeling too stressed already",
        "conversation_id": 10,
        "mental_wellness_risk_score": 78,
        "sentiment": "Negative",
        "burnout_risk_score": 82,
        "crisis_alert": False,
        "primary_stressor": "Assignment deadlines",
        "personalized_recommendations": "Prioritise sleep and manage deadlines."
    }
]

previous_attemps2 = [
    {
        "user_id": 1,
        "sleep_duration": 5,
        "stress_level": 5,
        "focus_level": 2,
        "academic_workload": 9,
        "mood": "Exhausted",
        "social_activity_level": 6,
        "reflection": "im feeling too stressed already",
        "conversation_id": 10,
        "mental_wellness_risk_score": 78,
        "sentiment": "Negative",
        "burnout_risk_score": 82,
        "crisis_alert": False,
        "primary_stressor": "Assignment deadlines",
        "personalized_recommendations": "Prioritise sleep and manage deadlines."
    },
    {
        "user_id": 1,
        "sleep_duration": 5,
        "stress_level": 8,
        "focus_level": 2,
        "academic_workload": 9,
        "mood": "Exhausted",
        "social_activity_level": 5,
        "reflection": "im feeling too stressed already",
        "conversation_id": 10,
        "mental_wellness_risk_score": 78,
        "sentiment": "Negative",
        "burnout_risk_score": 82,
        "crisis_alert": False,
        "primary_stressor": "Assignment deadlines",
        "personalized_recommendations": "Prioritise sleep and manage deadlines."
    },
    {
        "user_id": 1,
        "sleep_duration": 5,
        "stress_level": 5,
        "focus_level": 2,
        "academic_workload": 9,
        "mood": "Exhausted",
        "social_activity_level": 4,
        "reflection": "im feeling too stressed already",
        "conversation_id": 10,
        "mental_wellness_risk_score": 78,
        "sentiment": "Negative",
        "burnout_risk_score": 82,
        "crisis_alert": False,
        "primary_stressor": "Assignment deadlines",
        "personalized_recommendations": "Prioritise sleep and manage deadlines."
    },
    {
        "user_id": 1,
        "sleep_duration": 5,
        "stress_level": 5,
        "focus_level": 5,
        "academic_workload": 9,
        "mood": "Exhausted",
        "social_activity_level": 4,
        "reflection": "im feeling too stressed already",
        "conversation_id": 10,
        "mental_wellness_risk_score": 55,
        "sentiment": "Negative",
        "burnout_risk_score": 82,
        "crisis_alert": False,
        "primary_stressor": "Assignment deadlines",
        "personalized_recommendations": "Prioritise sleep and manage deadlines."
    }
]

user_input = {
    "user_id": 1,
    "sleep_duration": 3,
    "stress_level": 8,
    "focus_level": 2,
    "academic_workload": 9,
    "mood": "Exhausted",
    "social_activity_level": 3,
    "reflection": "im feeling too stressed already"
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

# test cases to check compare_sleep function
@pytest.mark.parametrize(
    "previous_attemps, sleep_duration, expected",
    [
        # test case to get back and empty [] which means there are no previous attemps
        ({}, 7, []),
        # test case to get message that says that we slept more
        (previous_attemps, 6, ["You slept 1.00 hours more than your average."]),
        # test case to get message that says we slept less than
        (previous_attemps, 4, ["You slept 1.00 hours less than your average."])
    ]
)

def test_compare_sleep(previous_attemps, sleep_duration, expected):
    assert compare_sleep(previous_attemps, sleep_duration) == expected


@pytest.mark.parametrize(
    "previous_attemps, social, expected",
    [
        # test cases to get an empty []
        ({}, 5, []),
        # test case to get social activity dopped
        (previous_attemps, 2, ["Your social activity has dropped across four consecutive attempts. Try connecting with others."]),
        # test case to get socialising less
        (previous_attemps2, 2,["You are socialising less than your previous average. Try connecting with others."])
    ]
)

def test_compare_social(previous_attemps, social, expected):
    assert compare_social(previous_attemps, social) == expected



@pytest.mark.parametrize(
    "previous_attempts, focus_level, expected",
    [
        #test case to get empty []
        ({}, 7, []),
        #test case to get focus level dropped
        (previous_attemps2, 3, ["Your focus level has dropped since your last attempt. Try taking a break and resting."]),
        #test case to get focus level improved
        (previous_attemps2, 7, ["Your focus level has improved since your last attempt. Keep it up!"])
    ]
)

def test_compare_focus(previous_attempts, focus_level, expected):
    assert compare_focus(previous_attempts, focus_level) == expected


@pytest.mark.parametrize(
    "previous_attempts, risk_score, field, label, expected",
    [
        # get empty [] due to no previous attempts
        ({}, 67, "mental_wellness_risk_score", "mental wellness", []),
        # get empty [] due to no improvement
        (previous_attemps, 90, "mental_wellness_risk_score", "mental wellness", []),
        (previous_attemps, 90, "burnout_risk_score", "burnout", []),
        # get risk score improved since previous
        (previous_attemps, 68, "mental_wellness_risk_score", "mental wellness", ["Your mental wellness risk score has improved since your last attempt. Keep it up!"]),
        # get risk score improved average
        (previous_attemps2, 53, "mental_wellness_risk_score", "mental wellness", ["Your mental wellness risk score has improved compared with your previous average. Keep it up!"])
    ]
)

def test_compare_risk_score(previous_attempts, risk_score, field, label, expected):
    assert compare_risk_score(previous_attempts, risk_score, field, label) == expected


@pytest.mark.parametrize(
    "user_input, ai_output, previous_attemps, expected",
    [
        # get a perfect display
        (user_input, ai_output, previous_attemps, {"mental_wellness_risk_tier": "High", "warnings": ["High Burnout Warning (Sleep)", "Burnout Warning (Workload)", "Social Withdrawal Risk", "Cognitive Fatigue Risk"],"route": "Counsellor follow-up","counselling_recommendation": True,"display_messages": ["You slept less than 7 hours. Try to get more sleep.","You slept 2.00 hours less than your average.","Your focus level has dropped since your last attempt. Try taking a break and resting."]})
    ]
)

def test_assess(user_input, ai_output, previous_attemps, expected):
    assert assess(user_input, ai_output, previous_attemps) == expected