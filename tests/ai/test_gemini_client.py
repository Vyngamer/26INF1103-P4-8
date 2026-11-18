import logging

import pytest
from google.genai import types

from ai_manager_helper import gemini_client as gemini_client_module
from ai_manager_helper.gemini_client import GeminiClient
from ai_manager_helper.gemini_client_with_fallback import GeminiClientWithFallback
from tests.support.guards import LiveServiceBlocked
from tests.support.contracts.ai import ChatClientContract
from tests.support.doubles.chat_clients import MockChatClient, QueuedResponder, Responder
from tests.support.doubles.genai_sdk import FakeGenAIModule, FakeInteractions, SdkErrors, retry_options


class TestGeminiClient:

    @pytest.fixture
    def interactions(self) -> FakeInteractions:
        return FakeInteractions(output_text='{"ok": true}')

    @pytest.fixture
    def sdk(self, monkeypatch, interactions) -> FakeGenAIModule:
        return install_fake_sdk(monkeypatch, interactions)

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

    @pytest.mark.parametrize("error", [SdkErrors.connection_error(), SdkErrors.model_not_found()],
                             ids=["connection", "not-found"])
    def test_sdk_errors_reach_the_caller(self, client, interactions, error):
        interactions.error = error
        with pytest.raises(type(error)):
            client.send_message("Hello!", None)

    def test_suite_blocks_a_real_connection(self, retry):
        # No fake SDK installed: the suite-wide guard must stop the real client being created.
        with pytest.raises(LiveServiceBlocked):
            GeminiClient("gemini-test", retry).connect_client()
