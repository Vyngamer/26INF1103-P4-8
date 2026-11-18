from __future__ import annotations

from typing import Any
from google.genai._gaos.types.interactions.interaction import Interaction

class FakeInteractions:
    """Records create() calls and returns a canned Interaction (or raises a canned error)."""

    def __init__(self, output_text: str = "{}", error: BaseException | None = None) -> None:
        self.output_text = output_text
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Interaction:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        # The SDK derives output_text from the trailing model_output step, so build it that way.
        return Interaction.model_validate({
            "status": "completed",
            "id": f"sdk-interaction-{len(self.calls)}",
            "previous_interaction_id": kwargs.get("previous_interaction_id"),
            "steps": [{"type": "model_output", "content": [{"type": "text", "text": self.output_text}]}],
        })

