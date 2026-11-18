import pytest
from pydantic import ValidationError

from ai_manager_helper.data_classes.conversation import Conversation

class TestConversation:

    @pytest.fixture
    def conversation(self) -> Conversation:
        return Conversation()

    def test_starts_empty_idle_and_unfinished(self, conversation):
        assert conversation.logs() == []
        assert conversation.is_bot_typing() is False
        assert conversation.is_done() is False

    def test_logs_messages_in_order_as_dicts(self, conversation):
        conversation.add_message("user", "YT", "Hi")
        conversation.add_message("ai", "AI", "Hello!")
        assert conversation.logs() == [
            {"sender": "user", "avatar": "YT", "message": "Hi"},
            {"sender": "ai", "avatar": "AI", "message": "Hello!"},
        ]

    def test_last_log_is_the_newest_message(self, conversation):
        conversation.add_message("user", "YT", "first")
        conversation.add_message("ai", "AI", "second")
        assert conversation.get_last_log()["message"] == "second"

    def test_last_log_of_empty_conversation_raises(self, conversation):
        with pytest.raises(IndexError):
            conversation.get_last_log()

    def test_typing_flag_toggles(self, conversation):
        conversation.set_bot_typing(True)
        assert conversation.is_bot_typing() is True
        conversation.set_bot_typing(False)
        assert conversation.is_bot_typing() is False

    @pytest.mark.parametrize("not_a_bool", [1, "yes", None])
    def test_typing_flag_must_be_boolean(self, conversation, not_a_bool):
        with pytest.raises(ValueError):
            conversation.set_bot_typing(not_a_bool)

    def test_done_flag(self, conversation):
        conversation.set_done(True)
        assert conversation.is_done() is True

    def test_reset_clears_messages(self, conversation):
        conversation.add_message("user", "YT", "Hi")
        conversation.reset_conversation()
        assert conversation.logs() == []

