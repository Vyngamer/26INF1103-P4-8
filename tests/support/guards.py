
class LiveServiceBlocked(AssertionError):
    """Raised when production code tries to reach a real external service during tests."""
