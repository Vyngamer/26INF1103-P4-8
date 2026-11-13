from pydantic import ValidationError
from ai_manager_helper.data_classes.survey_entity_schema import SurveyEntitySchema
from ai_manager_helper.api_client_classes.ai_counsellor import AICounsellor
import json
import sys

class AIManager:
    def __init__(self):
        self._client = AICounsellor()
        self._survey_results = None
        
    def connect_client(self):
        try:
            self._client.connect_client()
        except Exception as e:
            print(e)
            print("Failed to connect to client. Terminating program")

    def prompt_bot(self, message):
        output_response = json.loads(self._client.call_api(message).data)
        self._survey_results = output_response

        return {'text': output_response['text'], 'survey_done': output_response['survey_done']}

    def check_survey_end(self, response):
        return response['survey_done']
    
    def show_survey_results(self, by_alias=False):
        survey_results = SurveyEntitySchema(**self._survey_results)

        del survey_results.text, survey_results.survey_done
        return survey_results.model_dump(by_alias=by_alias)

    def deny_survey(self):
        self._client.deny_survey(self._survey_results)

    def start_conversation(self):
        output_response = json.loads(self._client.start_conversation().data)
        
        return {'text': output_response['text'], 'survey_done': output_response['survey_done']}

    def get_ai_output(self, user_input):
        return self._client.get_ai_output(user_input)

if __name__ == "__main__":
    ai_manager = AIManager()
    ai_manager.connect_client()
# 
#     while True:
#         ai_manager.prompt_bot()
    
    print(ai_manager.prompt_bot("hello"))
