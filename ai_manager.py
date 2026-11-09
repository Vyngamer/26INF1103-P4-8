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
        print(output_response, file=sys.stdout)

        return {'text': output_response['text'], 'survey_done': output_response['survey_done']}

    def validate_response(self, response):
        return SurveyEntitySchema.validate_response(response)

    def check_survey_end(self, response):
        return response['survey_done']
    
    def confirm_survey(self):
        output_response = self._client.confirm_survey(self._survey_results)
        return output_response

if __name__ == "__main__":
    ai_manager = AIManager()
    ai_manager.connect_client()
# 
#     while True:
#         ai_manager.prompt_bot()
    
    print(ai_manager.prompt_bot("hello"))
