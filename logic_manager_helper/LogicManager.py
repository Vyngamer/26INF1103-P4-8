from .CurrentAttempt import CurrentAttempt
from .PreviousAttempts import PreviousAttempts
from .LogicOutput import LogicOutput
from .RiskTierClassifier import RiskTierClassifier
from .SupportRouter import SupportRouter
from .SleepReminder import SleepReminder

from .warnings.SleepBurnoutRule import SleepBurnoutRule
from .warnings.WorkloadBurnoutRule import WorkloadBurnoutRule
from .warnings.SocialWithdrawalRule import SocialWithdrawalRule
from .warnings.CognitiveFatigueRule import CognitiveFatigueRule

from .comparisons.SleepComparison import SleepComparison
from .comparisons.SocialComparison import SocialComparison
from .comparisons.FocusComparison import FocusComparison
from .comparisons.RiskScoreComparison import RiskScoreComparison

class LogicManager:
    """Apply business rules and return a LogicOutput object."""

    def __init__(self):
        self._classifier = RiskTierClassifier()
        self._router = SupportRouter()

        self._warning_rules = [
            SleepBurnoutRule(),
            WorkloadBurnoutRule(),
            SocialWithdrawalRule(),
            CognitiveFatigueRule(),
        ]

        self._sleep_reminder = SleepReminder()

        self._comparison_rules = [
            SleepComparison(),
            SocialComparison(),
            FocusComparison(),
            RiskScoreComparison(
                "mental_wellness_risk_score",
                "mental wellness",
            ),
            RiskScoreComparison(
                "burnout_risk_score",
                "burnout",
            ),
        ]

    def _make_current_attempt(
        self,
        user_input,
        ai_output,
    ) -> CurrentAttempt:
        return CurrentAttempt(
            sleep_duration=user_input.sleep_duration,
            academic_workload=user_input.academic_workload,
            social_activity_level=user_input.social_activity_level,
            focus_level=user_input.focus_level,
            mental_wellness_risk_score=ai_output.mental_wellness_risk_score,
            burnout_risk_score=ai_output.burnout_risk_score,
            sentiment=ai_output.sentiment,
            crisis_alert=ai_output.crisis_alert,
        )

    def _collect_warnings(
        self,
        current: CurrentAttempt,
    ) -> list[str]:
        warnings = []

        for rule in self._warning_rules:
            warning = rule.evaluate(current)

            if warning is not None:
                warnings.append(warning)

        return warnings

    def _collect_display_messages(
        self,
        current: CurrentAttempt,
        history: PreviousAttempts,
    ) -> list[str]:
        messages = []

        reminder = self._sleep_reminder.evaluate(current)
        if reminder is not None:
            messages.append(reminder)

        for rule in self._comparison_rules:
            message = rule.evaluate(current, history)

            if message is not None:
                messages.append(message)

        return messages

    def assess(
        self,
        user_input,
        ai_output,
        previous_attempts: list[dict],
    ) -> LogicOutput:
        current = self._make_current_attempt(user_input, ai_output)
        history = PreviousAttempts(previous_attempts)

        tier = self._classifier.classify(current)
        warnings = self._collect_warnings(current)
        route = self._router.decide(current, tier, warnings)

        # Display messages do not affect the support route.
        display_messages = self._collect_display_messages(
            current, history
        )

        return LogicOutput(
            mental_wellness_risk_tier=tier,
            warnings=warnings,
            route=route,
            display_messages=display_messages,
        )