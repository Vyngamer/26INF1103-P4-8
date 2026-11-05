from pydantic import ValidationError
from ai_manager_helper.data_classes import SurveyEntitySchema
from ai_manager_helper.api_client_classes import AICounsellor

class AIManager:
    def __init__(self):
        self._client = AICounsellor()
        
    def connect_client(self):
        try:
            self._client.connect_client()
        except Exception as e:
            print(e)
            print("Failed to connect to client. Terminating program")

    def start_conversation(self):
        print(self._client.call_api("Hello!"))

    def prompt_bot(self):
        prompt = input("Enter prompt:\n")
        return self._client.call_api(prompt).data

    def validate_response(self, response):
        return SurveyEntitySchema.validate_response(response)


if __name__ == "__main__":
    ai_manager = AIManager()
    ai_manager.connect_client()
    ai_manager.start_conversation()

    while True:
        ai_manager.prompt_bot()
    
