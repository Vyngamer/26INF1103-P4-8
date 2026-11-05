class PreviousAttempts:
    """Hold historical attempts in oldest-to-newest order."""

    def __init__(self, attempts: list[dict]):
        self._attempts = [attempt.copy() for attempt in attempts]

    def get_values(self, field: str) -> list:
        return [attempt[field] for attempt in self._attempts]

    def get_latest(self, field: str):
        if not self._attempts:
            return None

        return self._attempts[-1][field]

    def get_average(self, field: str):
        values = self.get_values(field)

        if not values:
            return None

        return sum(values) / len(values)