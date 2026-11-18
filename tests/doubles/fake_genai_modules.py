from __future__ import annotations
from typing import Any
from tests.doubles.fake_interactions import FakeInteractions
from tests.doubles.fake_genai_client import FakeGenAIClient

class FakeGenAIModule:
    """Replaces the ``genai`` module object inside ai_manager_helper.gemini_client."""

    def __init__(self, interactions: FakeInteractions) -> None:
        self.interactions = interactions
        self.clients: list[FakeGenAIClient] = []

    def Client(self, **options: Any) -> FakeGenAIClient:  # noqa: N802 - mirrors the SDK name
        client = FakeGenAIClient(self.interactions, **options)
        self.clients.append(client)
        return client
