from __future__ import annotations

from typing import Any

from tests.doubles.fake_interactions import FakeInteractions

class FakeGenAIClient:
    """Replaces genai.Client; remembers the options it was built with."""

    def __init__(self, interactions: FakeInteractions, **options: Any) -> None:
        self.options = options
        self.interactions = interactions
