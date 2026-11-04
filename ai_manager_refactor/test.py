from ai_manager_refactor import AICounsellor

class AIManager:
    def __init__(self):
        self._client = AICounsellor()
        
    def connect_client(self):
        try:
            self._client.connect_client()
        except Exception as e:
            print(e)
            print("Failed to connect to client. Terminating program")

    def start_conversation():
        print(client.call_api("Hello!"))

    def prompt_bot()
        prompt = input("Enter prompt:\n")
        chat_response = client.call_api(prompt).data
        print(chat_response)
