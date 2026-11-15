from abc import ABC, abstractmethod

class IChatClient(ABC):
    @abstractmethod
    def send_message(self, prompt: str, previous_interaction_id: str, system_instruction: Optional[str] = None, json_response_schema: Optional[dict] = None):
        pass

