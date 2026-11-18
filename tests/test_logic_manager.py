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

    def test_values_latest_and_average(self):
        history = AttemptFactory.history("x", [2, 4, 9])
        assert history.get_values("x") == [2, 4, 9]
        assert history.get_latest("x") == 9
        assert history.get_average("x") == pytest.approx(5)

    def test_copies_input(self):
        rows = [{"x": 1}]
        history = PreviousAttempts(rows)
        rows[0]["x"] = 100
        assert history.get_latest("x") == 1

class TestRiskTierClassifier:

    @pytest.mark.parametrize(
        "score, expected",
        [
            (40, "Low"),
            (41, "Medium"),
            (71, "High"),
        ],
    )
    def test_classify(self, score, expected):
        current = AttemptFactory.current(mental_wellness_risk_score=score)
        assert RiskTierClassifier().classify(current) == expected

class TestWarningRules:

    @pytest.mark.parametrize(
        "rule, attempt, expected",
        [
            (SleepBurnoutRule(), dict(burnout_risk_score=76, sleep_duration=5.9), "High Burnout Warning (Sleep)"),
            (SleepBurnoutRule(), dict(burnout_risk_score=75, sleep_duration=4), None),
            (WorkloadBurnoutRule(), dict(burnout_risk_score=61, academic_workload=7), "Burnout Warning (Workload)"),
            (WorkloadBurnoutRule(), dict(burnout_risk_score=60, academic_workload=10), None),
            (SocialWithdrawalRule(), dict(social_activity_level=3, sentiment="Negative"), "Social Withdrawal Risk"),
            (CognitiveFatigueRule(), dict(focus_level=4, sentiment="Negative"), "Cognitive Fatigue Risk"),
        ],
    )
    def test_evaluate(self, rule, attempt, expected):
        assert rule.evaluate(AttemptFactory.current(**attempt)) == expected

class TestSleepReminder:

    @pytest.mark.parametrize(
        "sleep, expected",
        [
            (6.9, "You slept less than 7 hours. Try to get more sleep."),
            (7, None),
        ],
    )
    def test_evaluate(self, sleep, expected):
        assert SleepReminder().evaluate(AttemptFactory.current(sleep_duration=sleep)) == expected

class TestSupportRouter:

    EVERYTHING = dict(mental_wellness_risk_score=60, burnout_risk_score=70, sentiment="Negative")

    @pytest.mark.parametrize(
        "attempt, tier, warnings, expected",
        [
            (dict(crisis_alert=True), "High", ["a", "b"], "Urgent support"),
            ({}, "High", [], "Counsellor follow-up"),
            (EVERYTHING, "Medium", [], "Counsellor follow-up"),
            ({**EVERYTHING, "sentiment": "Neutral"}, "Medium", [], "Self-care guidance"),
        ],
    )
    def test_decide(self, attempt, tier, warnings, expected):
        assert SupportRouter().decide(AttemptFactory.current(**attempt), tier, warnings) == expected


class TestComparisonsWithNoHistory:

    def test_all_return_none(self):
        rules = [
            SleepComparison(),
            SocialComparison(),
            FocusComparison(),
            RiskScoreComparison("burnout_risk_score", "burnout"),
        ]
        current = AttemptFactory.current()
        empty = PreviousAttempts([])
        for rule in rules:
            assert rule.evaluate(current, empty) is None, type(rule).__name__


class TestSleepComparison:

    @pytest.mark.parametrize(
        "history, sleep, expected",
        [
            ([8, 8], 6.5, "You slept 1.50 hours less than your average."),
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
            ([6, 5, 4], 3, "four consecutive attempts"),
            ([6, 6], 4, "less than your previous average"),
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
            ([7], 5, "dropped since your last attempt"),
            ([5], 6, "improved since your last attempt"),
            ([5], 5, None),
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
            ("burnout_risk_score", "burnout", [60], 50, "Your burnout risk score has improved since your last attempt"),
            ("burnout_risk_score", "burnout", [80, 55], 55, "Your burnout risk score has improved compared with your previous average"),
            ("burnout_risk_score", "burnout", [30], 50, None),
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