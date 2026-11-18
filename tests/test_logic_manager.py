from types import SimpleNamespace

import pytest

from logic_manager_helper.comparisons.FocusComparison import FocusComparison
from logic_manager_helper.comparisons.RiskScoreComparison import RiskScoreComparison
from logic_manager_helper.comparisons.SleepComparison import SleepComparison
from logic_manager_helper.comparisons.SocialComparison import SocialComparison

from logic_manager_helper.warnings.CognitiveFatigueRule import CognitiveFatigueRule
from logic_manager_helper.warnings.SleepBurnoutRule import SleepBurnoutRule
from logic_manager_helper.warnings.SocialWithdrawalRule import SocialWithdrawalRule
from logic_manager_helper.warnings.WorkloadBurnoutRule import WorkloadBurnoutRule

from logic_manager_helper.CurrentAttempt import CurrentAttempt
from logic_manager_helper.PreviousAttempts import PreviousAttempts
from logic_manager_helper.RiskTierClassifier import RiskTierClassifier
from logic_manager_helper.SleepReminder import SleepReminder
from logic_manager_helper.SupportRouter import SupportRouter
from logic_manager_helper.LogicOutput import LogicOutput
from LogicManager import LogicManager


class AttemptFactory:
    """Builds the domain objects the tests need, with sensible defaults."""

    DEFAULTS = dict(
        sleep_duration=8,
        academic_workload=3,
        social_activity_level=7,
        focus_level=7,
        mental_wellness_risk_score=20,
        burnout_risk_score=20,
        sentiment="Positive",
        crisis_alert=False,
    )

    USER_FIELDS = {"sleep_duration", "academic_workload", "social_activity_level", "focus_level"}

    @classmethod
    def current(cls, **overrides) -> CurrentAttempt:
        return CurrentAttempt(**{**cls.DEFAULTS, **overrides})

    @staticmethod
    def history(field: str, values: list[int | float]) -> PreviousAttempts:
        return PreviousAttempts([{field: value} for value in values])

    @classmethod
    def split_inputs(cls, attempt: dict) -> tuple[SimpleNamespace, SimpleNamespace]:
        """Split one dict into fake user_input / ai_output objects."""
        user = {k: v for k, v in attempt.items() if k in cls.USER_FIELDS}
        ai = {k: v for k, v in attempt.items() if k not in cls.USER_FIELDS}
        return SimpleNamespace(**user), SimpleNamespace(**ai)


class MessageAssertions:
    """Mixin for rules that return either None or a message string."""

    @staticmethod
    def assert_message(msg: str | None, expected_text: str | None) -> None:
        if expected_text is None:
            assert msg is None
        else:
            assert msg is not None
            assert expected_text in msg

class TestPreviousAttempts:

    @pytest.mark.parametrize(
        "values, latest, average",
        [
            ([], None, None),
            ([5], 5, 5),
            ([2, 4, 9], 9, 5),
            ([6, 5, 4, 3], 3, 4.5),
        ],
    )
    def test_values_latest_and_average(self, values, latest, average):
        history = AttemptFactory.history("x", values)
        assert history.get_values("x") == values
        assert history.get_latest("x") == latest
        assert history.get_average("x") == (None if average is None else pytest.approx(average))

    def test_copies_input(self):
        rows = [{"x": 1}]
        history = PreviousAttempts(rows)
        rows[0]["x"] = 100
        assert history.get_latest("x") == 1

class TestRiskTierClassifier:

    @pytest.fixture
    def classifier(self):
        return RiskTierClassifier()

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
    def test_classify(self, classifier, score, expected):
        current = AttemptFactory.current(mental_wellness_risk_score=score)
        assert classifier.classify(current) == expected

class TestWarningRules:

    @pytest.mark.parametrize(
        "rule, attempt, expected",
        [
            # SleepBurnoutRule
            (SleepBurnoutRule(), dict(burnout_risk_score=76, sleep_duration=5.9), "High Burnout Warning (Sleep)"),
            (SleepBurnoutRule(), dict(burnout_risk_score=75, sleep_duration=4), None),
            (SleepBurnoutRule(), dict(burnout_risk_score=90, sleep_duration=6), None),
            # WorkloadBurnoutRule
            (WorkloadBurnoutRule(), dict(burnout_risk_score=61, academic_workload=7), "Burnout Warning (Workload)"),
            (WorkloadBurnoutRule(), dict(burnout_risk_score=60, academic_workload=10), None),
            (WorkloadBurnoutRule(), dict(burnout_risk_score=90, academic_workload=6), None),
            # SocialWithdrawalRule
            (SocialWithdrawalRule(), dict(social_activity_level=3, sentiment="Negative"), "Social Withdrawal Risk"),
            (SocialWithdrawalRule(), dict(social_activity_level=4, sentiment="Negative"), None),
            (SocialWithdrawalRule(), dict(social_activity_level=1, sentiment="Neutral"), None),
            # CognitiveFatigueRule
            (CognitiveFatigueRule(), dict(focus_level=4, sentiment="Negative"), "Cognitive Fatigue Risk"),
            (CognitiveFatigueRule(), dict(focus_level=5, sentiment="Negative"), None),
            (CognitiveFatigueRule(), dict(focus_level=1, sentiment="Positive"), None),
        ],
    )
    def test_evaluate(self, rule, attempt, expected):
        assert rule.evaluate(AttemptFactory.current(**attempt)) == expected


class TestSleepReminder:

    REMINDER = "You slept less than 7 hours. Try to get more sleep."

    @pytest.mark.parametrize(
        "sleep, expected",
        [
            (3, REMINDER),
            (6.9, REMINDER),
            (7, None),
            (9, None),
        ],
    )
    def test_evaluate(self, sleep, expected):
        assert SleepReminder().evaluate(AttemptFactory.current(sleep_duration=sleep)) == expected


# ---------------------------------------------------------------------------
# SupportRouter
# ---------------------------------------------------------------------------

class TestSupportRouter:

    EVERYTHING = dict(mental_wellness_risk_score=60, burnout_risk_score=70, sentiment="Negative")

    @pytest.fixture
    def router(self):
        return SupportRouter()

    @pytest.mark.parametrize(
        "attempt, tier, warnings, expected",
        [
            (dict(crisis_alert=True), "Low", [], "Urgent support"),
            (dict(crisis_alert=True), "High", ["a", "b"], "Urgent support"),
            ({}, "High", [], "Counsellor follow-up"),
            ({}, "Low", ["a", "b"], "Counsellor follow-up"),
            (EVERYTHING, "Medium", [], "Counsellor follow-up"),
            ({**EVERYTHING, "sentiment": "Neutral"}, "Medium", [], "Self-care guidance"),
            ({**EVERYTHING, "burnout_risk_score": 69}, "Medium", [], "Self-care guidance"),
            ({**EVERYTHING, "mental_wellness_risk_score": 59}, "Medium", [], "Self-care guidance"),
            ({}, "Medium", ["a"], "Self-care guidance"),
            ({}, "Low", [], "Self-care guidance"),
        ],
    )
    def test_decide(self, router, attempt, tier, warnings, expected):
        assert router.decide(AttemptFactory.current(**attempt), tier, warnings) == expected

class TestSleepComparison:

    @pytest.mark.parametrize(
        "history, sleep, expected",
        [
            ([], 7, None),
            ([8, 8], 6.5, "You slept 1.50 hours less than your average."),
            ([6], 8, "You slept 2.00 hours more than your average."),
            ([7], 7, "You slept the same number of hours as your average."),
        ],
    )
    def test_evaluate(self, history, sleep, expected):
        previous = AttemptFactory.history("sleep_duration", history)
        current = AttemptFactory.current(sleep_duration=sleep)
        assert SleepComparison().evaluate(current, previous) == expected


class TestSocialComparison(MessageAssertions):

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
    def test_evaluate(self, history, social, expected_text):
        previous = AttemptFactory.history("social_activity_level", history)
        current = AttemptFactory.current(social_activity_level=social)
        self.assert_message(SocialComparison().evaluate(current, previous), expected_text)


class TestFocusComparison(MessageAssertions):

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
    def test_evaluate(self, history, focus, expected_text):
        previous = AttemptFactory.history("focus_level", history)
        current = AttemptFactory.current(focus_level=focus)
        self.assert_message(FocusComparison().evaluate(current, previous), expected_text)


class TestRiskScoreComparison(MessageAssertions):

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
    def test_evaluate(self, field, label, history, score, expected_text):
        rule = RiskScoreComparison(field, label)
        previous = AttemptFactory.history(field, history)
        current = AttemptFactory.current(**{field: score})
        self.assert_message(rule.evaluate(current, previous), expected_text)

class TestLogicOutput:

    @pytest.mark.parametrize(
        "route, expected",
        [
            ("Urgent support", True),
            ("Counsellor follow-up", True),
            ("Self-care guidance", False),
        ],
    )
    def test_counselling_recommendation(self, route, expected):
        output = LogicOutput("Low", [], route, [])
        assert output.counselling_recommendation is expected
        assert output.to_dict()["counselling_recommendation"] is expected

    def test_lists_are_protected(self):
        warnings = ["a"]
        output = LogicOutput("Low", warnings, "Self-care guidance", [])
        warnings.append("b")
        output.warnings.append("c")
        assert output.warnings == ["a"]

class TestLogicManager:

    NORMAL = dict(AttemptFactory.DEFAULTS)

    NOT_SO_GOOD = dict(
        sleep_duration=3, academic_workload=9, social_activity_level=3, focus_level=2,
        mental_wellness_risk_score=78, burnout_risk_score=82, sentiment="Negative", crisis_alert=False,
    )

    NOT_SO_GOOD_HISTORY = [
        {"sleep_duration": 5, "social_activity_level": s, "focus_level": f,
         "mental_wellness_risk_score": 78, "burnout_risk_score": 82}
        for s, f in [(6, 5), (5, 5), (4, 5), (3, 6)]
    ]

    ALL_WARNINGS = [
        "High Burnout Warning (Sleep)",
        "Burnout Warning (Workload)",
        "Social Withdrawal Risk",
        "Cognitive Fatigue Risk",
    ]

    @pytest.fixture
    def manager(self):
        return LogicManager()

    @pytest.mark.parametrize(
        "attempt, history, tier, warnings, route, recommend, messages_include",
        [
            pytest.param(NORMAL, [], "Low", [], "Self-care guidance", False, [], id="healthy"),
            pytest.param(
                {**NORMAL, "crisis_alert": True}, [], "Low", [], "Urgent support", True, [],
                id="crisis",
            ),
            pytest.param(
                {**NORMAL, "mental_wellness_risk_score": 55}, [], "Medium", [], "Self-care guidance", False, [],
                id="medium-no-warnings",
            ),
            pytest.param(
                NOT_SO_GOOD, NOT_SO_GOOD_HISTORY, "High", ALL_WARNINGS,
                "Counsellor follow-up", True,
                ["You slept less than 7 hours. Try to get more sleep.",
                 "You slept 2.00 hours less than your average."],
                id="struggling",
            ),
        ],
    )
    def test_assess(self, manager, attempt, history, tier, warnings, route, recommend, messages_include):
        user, ai = AttemptFactory.split_inputs(attempt)
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