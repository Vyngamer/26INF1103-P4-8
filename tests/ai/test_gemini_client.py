import pytest
from google.genai import types

from ai_manager_helper.gemini_client import GeminiClient
from tests.support.guards import LiveServiceBlocked
from tests.doubles.fake_genai_client import FakeGenAIClient
from tests.doubles.fake_interactions import FakeInteractions
from tests.doubles.fake_genai_modules import FakeGenAIModule


class TestGeminiClient:

    @pytest.fixture
    def interactions(self) -> FakeInteractions:
        return FakeInteractions(output_text='{"ok": true}')

    @pytest.fixture
    def retry(self) -> types.HttpRetryOptions:
        return types.HttpRetryOptions(attempts=3, http_status_codes=[503])

    @pytest.fixture
    def client(self, sdk, retry) -> GeminiClient:
        client = GeminiClient("gemini-test", retry)
        client.connect_client()
        return client

    def test_connect_uses_retry_options_and_two_minute_timeout(self, sdk, client, retry):
        http_options = sdk.clients[0].options["http_options"]
        assert http_options.retry_options is retry
        assert http_options.timeout == 120 * 1000

    def test_send_forwards_everything_to_the_sdk(self, client, interactions):
        schema = {"type": "object", "properties": {"x": {"type": "integer"}}}

        client.send_message("Hello!", "previous-id", "be kind", schema)

        assert interactions.calls == [{
            "model": "gemini-test",
            "input": "Hello!",
            "system_instruction": "be kind",
            "previous_interaction_id": "previous-id",
            "response_format": {"type": "text", "mime_type": "application/json", "schema": schema},
        }]

    def test_reply_is_the_interaction_as_a_dict(self, client):
        reply = client.send_message("Hello!", None)
        assert reply["output_text"] == '{"ok": true}'
        assert reply["status"] == "completed"

    def test_sending_before_connecting_fails(self, sdk, retry):
        with pytest.raises(AttributeError):
            GeminiClient("gemini-test", retry).send_message("Hello!", None)
