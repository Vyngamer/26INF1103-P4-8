from .CurrentAttempt import CurrentAttempt

class SleepReminder:
    """Check the current attempt without using history."""

    def evaluate(self, current: CurrentAttempt) -> str | None:
        if current.sleep_duration < 7:
            return "You slept less than 7 hours. Try to get more sleep."
        return None
