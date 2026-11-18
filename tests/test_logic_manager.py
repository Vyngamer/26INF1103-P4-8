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
from LogicManager import LogicManager
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