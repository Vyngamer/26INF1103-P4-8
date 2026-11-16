# import pytest

# from logic_manager import (get_risk_tier, get_warnings, decide_route, check_sleep,
#                            compare_sleep, compare_social, compare_focus, compare_risk_score,
#                            compare_mental_wellness, compare_burnout, assess)


# # create scores to test get_risk_tier
# @pytest.mark.parametrize(
#     "score, expected",
#     [
#         # test cases to test Low
#         (0, "Low"),
#         (40, "Low"),
#         (-1, "Low"),
#         # test cases to test Medium
#         (41, "Medium"),
#         (50, "Medium"),
#         (70, "Medium"),
#         # test cases to test High
#         (71, "High"),
#         (85, "High"),
#         (100, "High")
#         # test cases to test out of range
#     ],
# )

# # function to use the above values to test
# def test_get_risk_tier(score, expected):
#     assert get_risk_tier(score) == expected


# # create values to test get_warnings function
# @pytest.mark.parametrize(
#     "senti, burnout_score, sleep, workload, social_activity_level, focus, expected",
#     [
#         # test cases to get high burnout
#         ("Positive", 76, 5, 5, 8, 8, ["High Burnout Warning (Sleep)"]),
#         ("Negative", 75, 6, 5, 8, 8, []),
#         ("Positive", 80, 4, 5, 8, 8, ["High Burnout Warning (Sleep)"]),
#         # test cases to get burnout warning (workload)
#         ("Positive", 61, 8, 7, 8, 8, ["Burnout Warning (Workload)"]),
#         ("Positive", 60, 8, 6, 8, 8, []),
#         ("Positive", 75, 8, 8, 8, 8, ["Burnout Warning (Workload)"]),
#         # test cases to get social withdrawal
#         ("Negative", 55, 8, 8, 3, 5, ["Social Withdrawal Risk"]),
#         ("Positive", 55, 8, 8, 3, 5, []),
#         ("Negative", 55, 8, 8, 2, 5, ["Social Withdrawal Risk"]),
#         # test cases to get cognitive fatigue risks
#         ("Negative", 55, 8, 8, 4, 4, ["Cognitive Fatigue Risk"]),
#         ("Positive", 55, 8, 8, 4, 5, []),
#         ("Negative", 55, 8, 8, 4, 3, ["Cognitive Fatigue Risk"]),
#         # test cases to get multiple risks
#         ("Negative", 84, 4, 8, 2, 3, ["High Burnout Warning (Sleep)", "Burnout Warning (Workload)", "Social Withdrawal Risk", "Cognitive Fatigue Risk"]),
#         ("Negative", 84, 7, 8, 2, 3, ["Burnout Warning (Workload)", "Social Withdrawal Risk", "Cognitive Fatigue Risk"]),
#         ("Negative", 84, 5, 8, 2, 6, ["High Burnout Warning (Sleep)", "Burnout Warning (Workload)", "Social Withdrawal Risk"]),
#         ("Positive", 84, 5, 8, 2, 3, ["High Burnout Warning (Sleep)", "Burnout Warning (Workload)"])
#     ]
# ) # senti, burnout_score, sleep,
#   # workload, social_activity_level, focus, expected

# def test_get_warnings(senti, burnout_score, sleep, workload, social_activity_level, focus, expected):
#     assert get_warnings(senti, burnout_score, sleep, workload, social_activity_level, focus) == expected



# # test cases for decide route function
# @pytest.mark.parametrize(
#     "ai_output, tier, warnings, expected",
#     [
#         # test cases to get urgent support
#         ({"burnout_risk_score": 50,"crisis_alert": True,"mental_wellness_risk_score": 85,"personalized_recommendations": "Your sleep duration of only one hour is critically low and poses an immediate danger to your physical and cognitive health. Please prioritize immediate rest or contact a medical professional, as your current level of sleep deprivation is unsustainable and requires urgent attention.","primary_stressor": "Sleep Deprivation","sentiment": "Neutral"}, "High", [], "Urgent support"),
#         # test cases to get counsellor follow-up
#         ({"burnout_risk_score": 50,"crisis_alert": False,"mental_wellness_risk_score": 85,"personalized_recommendations": "Your sleep duration of only one hour is critically low and poses an immediate danger to your physical and cognitive health. Please prioritize immediate rest or contact a medical professional, as your current level of sleep deprivation is unsustainable and requires urgent attention.","primary_stressor": "Sleep Deprivation","sentiment": "Neutral"}, "High", [], "Counsellor follow-up"),
#         ({"burnout_risk_score": 50,"crisis_alert": False,"mental_wellness_risk_score": 55,"personalized_recommendations": "Your sleep duration of only one hour is critically low and poses an immediate danger to your physical and cognitive health. Please prioritize immediate rest or contact a medical professional, as your current level of sleep deprivation is unsustainable and requires urgent attention.","primary_stressor": "Sleep Deprivation","sentiment": "Neutral"}, "Low", ["High Burnout Warning (Sleep)", "Burnout Warning (Workload)"], "Counsellor follow-up"),
#         ({"burnout_risk_score": 70,"crisis_alert": False,"mental_wellness_risk_score": 60,"personalized_recommendations": "Your sleep duration of only one hour is critically low and poses an immediate danger to your physical and cognitive health. Please prioritize immediate rest or contact a medical professional, as your current level of sleep deprivation is unsustainable and requires urgent attention.","primary_stressor": "Sleep Deprivation","sentiment": "Negative"}, "Low", [], "Counsellor follow-up"),
#         # test for self-care guidance
#         ({"burnout_risk_score": 50,"crisis_alert": False,"mental_wellness_risk_score": 85,"personalized_recommendations": "Your sleep duration of only one hour is critically low and poses an immediate danger to your physical and cognitive health. Please prioritize immediate rest or contact a medical professional, as your current level of sleep deprivation is unsustainable and requires urgent attention.","primary_stressor": "Sleep Deprivation","sentiment": "Neutral"}, "Low", [], "Self-care guidance")
#     ]
# )

# def test_decide_route(ai_output, tier, warnings, expected):
#     assert decide_route(ai_output, tier, warnings) == expected


# # test cases to check check_sleep function
# @pytest.mark.parametrize(
#     "sleep_duration, expected",
#     [
#         # testcase to get sleep_duration
#         (6.9, ["You slept less than 7 hours. Try to get more sleep."]),
#         (7, [])
#     ]
# )

# def test_check_sleep(sleep_duration, expected):
#     assert check_sleep(sleep_duration) == expected

# def attempts(field, values):
#     return [{field: v} for v in values]

# # initialise any dummy data that we will need
# previous_attemps = [
#     {
#         "user_id": 1,
#         "sleep_duration": 5,
#         "stress_level": 5,
#         "focus_level": 5,
#         "academic_workload": 9,
#         "mood": "Exhausted",
#         "social_activity_level": 6,
#         "reflection": "im feeling too stressed already",
#         "conversation_id": 10,
#         "mental_wellness_risk_score": 78,
#         "sentiment": "Negative",
#         "burnout_risk_score": 82,
#         "crisis_alert": False,
#         "primary_stressor": "Assignment deadlines",
#         "personalized_recommendations": "Prioritise sleep and manage deadlines."
#     },
#     {
#         "user_id": 1,
#         "sleep_duration": 5,
#         "stress_level": 8,
#         "focus_level": 5,
#         "academic_workload": 9,
#         "mood": "Exhausted",
#         "social_activity_level": 5,
#         "reflection": "im feeling too stressed already",
#         "conversation_id": 10,
#         "mental_wellness_risk_score": 78,
#         "sentiment": "Negative",
#         "burnout_risk_score": 82,
#         "crisis_alert": False,
#         "primary_stressor": "Assignment deadlines",
#         "personalized_recommendations": "Prioritise sleep and manage deadlines."
#     },
#     {
#         "user_id": 1,
#         "sleep_duration": 5,
#         "stress_level": 5,
#         "focus_level": 5,
#         "academic_workload": 9,
#         "mood": "Exhausted",
#         "social_activity_level": 4,
#         "reflection": "im feeling too stressed already",
#         "conversation_id": 10,
#         "mental_wellness_risk_score": 78,
#         "sentiment": "Negative",
#         "burnout_risk_score": 82,
#         "crisis_alert": False,
#         "primary_stressor": "Assignment deadlines",
#         "personalized_recommendations": "Prioritise sleep and manage deadlines."
#     },
#     {
#         "user_id": 1,
#         "sleep_duration": 5,
#         "stress_level": 5,
#         "focus_level": 6,
#         "academic_workload": 9,
#         "mood": "Exhausted",
#         "social_activity_level": 3,
#         "reflection": "im feeling too stressed already",
#         "conversation_id": 10,
#         "mental_wellness_risk_score": 78,
#         "sentiment": "Negative",
#         "burnout_risk_score": 82,
#         "crisis_alert": False,
#         "primary_stressor": "Assignment deadlines",
#         "personalized_recommendations": "Prioritise sleep and manage deadlines."
#     }
# ]

# previous_attemps2 = [
#     {
#         "user_id": 1,
#         "sleep_duration": 5,
#         "stress_level": 5,
#         "focus_level": 2,
#         "academic_workload": 9,
#         "mood": "Exhausted",
#         "social_activity_level": 6,
#         "reflection": "im feeling too stressed already",
#         "conversation_id": 10,
#         "mental_wellness_risk_score": 78,
#         "sentiment": "Negative",
#         "burnout_risk_score": 82,
#         "crisis_alert": False,
#         "primary_stressor": "Assignment deadlines",
#         "personalized_recommendations": "Prioritise sleep and manage deadlines."
#     },
#     {
#         "user_id": 1,
#         "sleep_duration": 5,
#         "stress_level": 8,
#         "focus_level": 2,
#         "academic_workload": 9,
#         "mood": "Exhausted",
#         "social_activity_level": 5,
#         "reflection": "im feeling too stressed already",
#         "conversation_id": 10,
#         "mental_wellness_risk_score": 78,
#         "sentiment": "Negative",
#         "burnout_risk_score": 82,
#         "crisis_alert": False,
#         "primary_stressor": "Assignment deadlines",
#         "personalized_recommendations": "Prioritise sleep and manage deadlines."
#     },
#     {
#         "user_id": 1,
#         "sleep_duration": 5,
#         "stress_level": 5,
#         "focus_level": 2,
#         "academic_workload": 9,
#         "mood": "Exhausted",
#         "social_activity_level": 4,
#         "reflection": "im feeling too stressed already",
#         "conversation_id": 10,
#         "mental_wellness_risk_score": 78,
#         "sentiment": "Negative",
#         "burnout_risk_score": 82,
#         "crisis_alert": False,
#         "primary_stressor": "Assignment deadlines",
#         "personalized_recommendations": "Prioritise sleep and manage deadlines."
#     },
#     {
#         "user_id": 1,
#         "sleep_duration": 5,
#         "stress_level": 5,
#         "focus_level": 5,
#         "academic_workload": 9,
#         "mood": "Exhausted",
#         "social_activity_level": 4,
#         "reflection": "im feeling too stressed already",
#         "conversation_id": 10,
#         "mental_wellness_risk_score": 55,
#         "sentiment": "Negative",
#         "burnout_risk_score": 82,
#         "crisis_alert": False,
#         "primary_stressor": "Assignment deadlines",
#         "personalized_recommendations": "Prioritise sleep and manage deadlines."
#     }
# ]

# user_input = {
#     "user_id": 1,
#     "sleep_duration": 3,
#     "stress_level": 8,
#     "focus_level": 2,
#     "academic_workload": 9,
#     "mood": "Exhausted",
#     "social_activity_level": 3,
#     "reflection": "im feeling too stressed already"
# }
# ai_output = {
#     "conversation_id": 10,
#     "mental_wellness_risk_score": 78,
#     "sentiment": "Negative",
#     "burnout_risk_score": 82,
#     "crisis_alert": False,
#     "primary_stressor": "Assignment deadlines",
#     "personalized_recommendations": "Prioritise sleep and manage deadlines."
# }

# # test cases to check compare_sleep function
# @pytest.mark.parametrize(
#     "previous_attemps, sleep_duration, expected",
#     [
#         # test case to get back and empty [] which means there are no previous attemps
#         ({}, 7, []),
#         # test case to get message that says that we slept more
#         (previous_attemps, 6, ["You slept 1.00 hours more than your average."]),
#         # test case to get message that says we slept less than
#         (previous_attemps, 4, ["You slept 1.00 hours less than your average."])
#     ]
# )

# def test_compare_sleep(previous_attemps, sleep_duration, expected):
#     assert compare_sleep(previous_attemps, sleep_duration) == expected


# @pytest.mark.parametrize(
#     "previous_attemps, social, expected",
#     [
#         # test cases to get an empty []
#         ({}, 5, []),
#         # test case to get social activity dopped
#         (previous_attemps, 2, ["Your social activity has dropped across four consecutive attempts. Try connecting with others."]),
#         # test case to get socialising less
#         (previous_attemps2, 2,["You are socialising less than your previous average. Try connecting with others."])
#     ]
# )

# def test_compare_social(previous_attemps, social, expected):
#     assert compare_social(previous_attemps, social) == expected



# @pytest.mark.parametrize(
#     "previous_attempts, focus_level, expected",
#     [
#         #test case to get empty []
#         ({}, 7, []),
#         #test case to get focus level dropped
#         (previous_attemps2, 3, ["Your focus level has dropped since your last attempt. Try taking a break and resting."]),
#         #test case to get focus level improved
#         (previous_attemps2, 7, ["Your focus level has improved since your last attempt. Keep it up!"])
#     ]
# )

# def test_compare_focus(previous_attempts, focus_level, expected):
#     assert compare_focus(previous_attempts, focus_level) == expected


# @pytest.mark.parametrize(
#     "previous_attempts, risk_score, field, label, expected",
#     [
#         # get empty [] due to no previous attempts
#         ({}, 67, "mental_wellness_risk_score", "mental wellness", []),
#         # get empty [] due to no improvement
#         (previous_attemps, 90, "mental_wellness_risk_score", "mental wellness", []),
#         (previous_attemps, 90, "burnout_risk_score", "burnout", []),
#         # get risk score improved since previous
#         (previous_attemps, 68, "mental_wellness_risk_score", "mental wellness", ["Your mental wellness risk score has improved since your last attempt. Keep it up!"]),
#         # get risk score improved average
#         (previous_attemps2, 53, "mental_wellness_risk_score", "mental wellness", ["Your mental wellness risk score has improved compared with your previous average. Keep it up!"])
#     ]
# )

# def test_compare_risk_score(previous_attempts, risk_score, field, label, expected):
#     assert compare_risk_score(previous_attempts, risk_score, field, label) == expected


# @pytest.mark.parametrize(
#     "user_input, ai_output, previous_attemps, expected",
#     [
#         # get a perfect display
#         (user_input, ai_output, previous_attemps, {"mental_wellness_risk_tier": "High", "warnings": ["High Burnout Warning (Sleep)", "Burnout Warning (Workload)", "Social Withdrawal Risk", "Cognitive Fatigue Risk"],"route": "Counsellor follow-up","counselling_recommendation": True,"display_messages": ["You slept less than 7 hours. Try to get more sleep.","You slept 2.00 hours less than your average.","Your focus level has dropped since your last attempt. Try taking a break and resting."]})
#     ]
# )

# def test_assess(user_input, ai_output, previous_attemps, expected):
#     assert assess(user_input, ai_output, previous_attemps) == expected

# new logic manager part
from types import SimpleNamespace

import pytest

from logic_manager_helper.comparisons.ComparisonRule import ComparisonRule
from logic_manager_helper.comparisons.FocusComparison import FocusComparison
from logic_manager_helper.comparisons.RiskScoreComparison import RiskScoreComparison
from logic_manager_helper.comparisons.SleepComparison import SleepComparison
from logic_manager_helper.comparisons.SocialComparison import SocialComparison

from logic_manager_helper.warnings.WarningRule import WarningRule
from logic_manager_helper.warnings.CognitiveFatigueRule import CognitiveFatigueRule
from logic_manager_helper.warnings.SleepBurnoutRule import SleepBurnoutRule
from logic_manager_helper.warnings.SocialWithdrawalRule import SocialWithdrawalRule
from logic_manager_helper.warnings.WorkloadBurnoutRule import WorkloadBurnoutRule

from logic_manager_helper.CurrentAttempt import CurrentAttempt
from logic_manager_helper.PreviousAttempts import PreviousAttempts
from logic_manager_helper.RiskTierClassifier import RiskTierClassifier
from logic_manager_helper.SleepReminder import SleepReminder
from logic_manager_helper.SupportRouter import SupportRouter
from logic_manager_helper.LogicManager import LogicManager
from logic_manager_helper.LogicOutput import LogicOutput

def make_current(**overrides) -> CurrentAttempt:
    values = dict(
        sleep_duration=8,
        academic_workload=3,
        social_activity_level=7,
        focus_level=7,
        mental_wellness_risk_score=20,
        burnout_risk_score=20,
        sentiment="Positive",
        crisis_alert=False,
    )
    values.update(overrides)
    return CurrentAttempt(**values)


def make_history(field: str, values: list[int | float]) -> PreviousAttempts:
    return PreviousAttempts([{field: value} for value in values])


# testing previous attempts
@pytest.mark.parametrize(
    "values, latest, average",
    [
        ([], None, None),
        ([5], 5, 5),
        ([2, 4, 9], 9, 5),
        ([6, 5, 4, 3], 3, 4.5),
    ],
)
def test_previous_attempts(values, latest, average):
    history = make_history("x", values)
    assert history.get_values("x") == values
    assert history.get_latest("x") == latest
    assert history.get_average("x") == (None if average is None else pytest.approx(average))


def test_previous_attempts_copies_input():
    rows = [{"x": 1}]
    history = PreviousAttempts(rows)
    rows[0]["x"] = 100
    assert history.get_latest("x") == 1


# test the risk tier classifier
@pytest.mark.parametrize(
    "score, expected",
    [
        (0, "Low"),
        (40, "Low"),
        (41, "Medium"),
        (70, "Medium"),
        (71, "High"),
        (100, "High"),
    ],
)

def test_risk_tier(score, expected):
    current = make_current(mental_wellness_risk_score=score)
    assert RiskTierClassifier().classify(current) == expected


# test warning rules
@pytest.mark.parametrize(
    "rule, attempt, expected",
    [
        # test for SleepBurnoutRule
        (SleepBurnoutRule(), dict(burnout_risk_score=76, sleep_duration=5.9), "High Burnout Warning (Sleep)"),
        (SleepBurnoutRule(), dict(burnout_risk_score=75, sleep_duration=4), None),
        (SleepBurnoutRule(), dict(burnout_risk_score=90, sleep_duration=6), None),
        # test for WorkloadBurnoutRule
        (WorkloadBurnoutRule(), dict(burnout_risk_score=61, academic_workload=7), "Burnout Warning (Workload)"),
        (WorkloadBurnoutRule(), dict(burnout_risk_score=60, academic_workload=10), None),
        (WorkloadBurnoutRule(), dict(burnout_risk_score=90, academic_workload=6), None),
        # test for SocialWithdrawalRule
        (SocialWithdrawalRule(), dict(social_activity_level=3, sentiment="Negative"), "Social Withdrawal Risk"),
        (SocialWithdrawalRule(), dict(social_activity_level=4, sentiment="Negative"), None),
        (SocialWithdrawalRule(), dict(social_activity_level=1, sentiment="Neutral"), None),
        # test for CognitiveFatigueRule
        (CognitiveFatigueRule(), dict(focus_level=4, sentiment="Negative"), "Cognitive Fatigue Risk"),
        (CognitiveFatigueRule(), dict(focus_level=5, sentiment="Negative"), None),
        (CognitiveFatigueRule(), dict(focus_level=1, sentiment="Positive"), None),
    ],
)
def test_warning_rules(rule, attempt, expected):
    assert rule.evaluate(make_current(**attempt)) == expected



# test sleep reminder
@pytest.mark.parametrize(
    "sleep, expected",
    [
        (3, "You slept less than 7 hours. Try to get more sleep."),
        (6.9, "You slept less than 7 hours. Try to get more sleep."),
        (7, None),
        (9, None),
    ],
)
def test_sleep_reminder(sleep, expected):
    assert SleepReminder().evaluate(make_current(sleep_duration=sleep)) == expected

# test logic router
everything = dict(mental_wellness_risk_score=60, burnout_risk_score=70, sentiment="Negative")

@pytest.mark.parametrize(
    "attempt, tier, warnings, expected",
    [
        (dict(crisis_alert=True), "Low", [], "Urgent support"),
        (dict(crisis_alert=True), "High", ["a", "b"], "Urgent support"),
        ({}, "High", [], "Counsellor follow-up"),
        ({}, "Low", ["a", "b"], "Counsellor follow-up"),
        (everything, "Medium", [], "Counsellor follow-up"),
        ({**everything, "sentiment": "Neutral"}, "Medium", [], "Self-care guidance"),
        ({**everything, "burnout_risk_score": 69}, "Medium", [], "Self-care guidance"),
        ({**everything, "mental_wellness_risk_score": 59}, "Medium", [], "Self-care guidance"),
        ({}, "Medium", ["a"], "Self-care guidance"),
        ({}, "Low", [], "Self-care guidance"),
    ],
)
def test_support_router(attempt, tier, warnings, expected):
    assert SupportRouter().decide(make_current(**attempt), tier, warnings) == expected


# test comparison rules
@pytest.mark.parametrize(
    "history, sleep, expected",
    [
        ([], 7, None),
        # test sleep less than
        ([8, 8], 6.5, "You slept 1.50 hours less than your average."),
        # test sleep more than
        ([6], 8, "You slept 2.00 hours more than your average."),
        # test same as
        ([7], 7, "You slept the same number of hours as your average."),
    ],
)
def test_sleep_comparison(history, sleep, expected):
    history = make_history("sleep_duration", history)
    assert SleepComparison().evaluate(make_current(sleep_duration=sleep), history) == expected


@pytest.mark.parametrize(
    "history, social, expected_text",
    [
        ([], 5, None),
        ([6, 5, 4], 3, "four consecutive attempts"),
        ([9, 6, 5, 4], 3, "four consecutive attempts"),
        ([6, 6], 4, "less than your previous average"),
        ([5, 5], 4, None),
        ([6, 5, 4, 3], 3, None),
    ],
)
def test_social_comparison(history, social, expected_text):
    history = make_history("social_activity_level", history)
    msg = SocialComparison().evaluate(make_current(social_activity_level=social), history)
    if expected_text is None:
        assert msg is None
    else:
        assert expected_text in msg


@pytest.mark.parametrize(
    "history, focus, expected_text",
    [
        ([], 5, None),
        ([7], 5, "dropped since your last attempt"),
        ([5], 6, "improved since your last attempt"),
        ([9, 9, 5], 5, "below your previous average"),
        ([2, 2, 6], 6, "compared with your previous average"),
        ([5], 5, None),
        ([6], 5, None),
    ],
)
def test_focus_comparison(history, focus, expected_text):
    history = make_history("focus_level", history)
    msg = FocusComparison().evaluate(make_current(focus_level=focus), history)
    if expected_text is None:
        assert msg is None
    else:
        assert expected_text in msg


@pytest.mark.parametrize(
    "field, label, history, score, expected_text",
    [
        ("burnout_risk_score", "burnout", [], 50, None),
        ("burnout_risk_score", "burnout", [30], 50, None),
        ("burnout_risk_score", "burnout", [60], 50, "Your burnout risk score has improved since your last attempt"),
        ("burnout_risk_score", "burnout", [80, 55], 55, "Your burnout risk score has improved compared with your previous average"),
        ("burnout_risk_score", "burnout", [55], 50, None),
        ("mental_wellness_risk_score", "mental wellness", [80], 50, "Your mental wellness risk score has improved since"),
        ("mental_wellness_risk_score", "mental wellness", [90, 60], 60, "Your mental wellness risk score has improved compared"),
        ("mental_wellness_risk_score", "mental wellness", [40], 45, None),
    ],
)
def test_risk_score_comparison(field, label, history, score, expected_text):
    rule = RiskScoreComparison(field, label)
    history = make_history(field, history)
    msg = rule.evaluate(make_current(**{field: score}), history)
    if expected_text is None:
        assert msg is None
    else:
        assert expected_text in msg



# test logic output
@pytest.mark.parametrize(
    "route, expected",
    [
        ("Urgent support", True),
        ("Counsellor follow-up", True),
        ("Self-care guidance", False),
    ],
)
def test_counselling_recommendation(route, expected):
    output = LogicOutput("Low", [], route, [])
    assert output.counselling_recommendation is expected
    assert output.to_dict()["counselling_recommendation"] is expected


def test_logic_output_lists_are_protected():
    warnings = ["a"]
    output = LogicOutput("Low", warnings, "Self-care guidance", [])
    warnings.append("b")
    output.warnings.append("c")
    assert output.warnings == ["a"]



# test logic manager class, basically everything in one class so we will need some data
normal = dict(sleep_duration=8, academic_workload=3, social_activity_level=7, focus_level=7,
    mental_wellness_risk_score=20, burnout_risk_score=20, sentiment="Positive", crisis_alert=False)

not_so_good = dict(sleep_duration=3, academic_workload=9, social_activity_level=3, focus_level=2,
    mental_wellness_risk_score=78, burnout_risk_score=82, sentiment="Negative", crisis_alert=False)

not_so_good_history = [{"sleep_duration": 5, "social_activity_level": s, "focus_level": f,
     "mental_wellness_risk_score": 78, "burnout_risk_score": 82}
    for s, f in [(6, 5), (5, 5), (4, 5), (3, 6)]]

fields = {"sleep_duration", "academic_workload", "social_activity_level", "focus_level"}


def split_inputs(attempt: dict):
    """Split one dict into fake user_input / ai_output objects."""
    user = {k: v for k, v in attempt.items() if k in fields}
    ai = {k: v for k, v in attempt.items() if k not in fields}
    return SimpleNamespace(**user), SimpleNamespace(**ai)


@pytest.mark.parametrize(
    "attempt, history, tier, warnings, route, recommend, messages_include",
    [
        pytest.param(normal, [], "Low", [], "Self-care guidance", False, [], id="healthy"),
        pytest.param(
            {**normal, "crisis_alert": True}, [], "Low", [], "Urgent support", True, [], id="crisis",
        ),
        pytest.param(
            {**normal, "mental_wellness_risk_score": 55}, [], "Medium", [], "Self-care guidance", False, [],
            id="medium-no-warnings",
        ),
        pytest.param(
            not_so_good, not_so_good_history, "High",
            ["High Burnout Warning (Sleep)", "Burnout Warning (Workload)",
             "Social Withdrawal Risk", "Cognitive Fatigue Risk"],
            "Counsellor follow-up", True,
            ["You slept less than 7 hours. Try to get more sleep.",
             "You slept 2.00 hours less than your average."],
            id="struggling",
        ),
    ],
)
def test_logic_manager(attempt, history, tier, warnings, route, recommend, messages_include):
    user, ai = split_inputs(attempt)
    manager = LogicManager()
    out = manager.assess(user, ai, history)

    assert out.mental_wellness_risk_tier == tier
    assert out.warnings == warnings
    assert out.route == route
    assert out.counselling_recommendation is recommend
    for message in messages_include:
        assert message in out.display_messages
    if not history and attempt["sleep_duration"] >= 7:
        assert out.display_messages == []
    assert manager.to_dict(out) == out.to_dict()

print("hi")