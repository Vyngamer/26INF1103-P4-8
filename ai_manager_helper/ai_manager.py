from ai_manager_helper.interfaces.counselling_strategy import ICounsellingStrategy
from ai_manager_helper.collect_survey_strategy import CollectSurveyStrategy
from ai_manager_helper.evaluate_survey_strategy import EvaluateSurveyStrategy
from ai_manager_helper.data_classes.conversation import Conversation
from ai_manager_helper.data_classes.survey_entity_schema import SurveyEntitySchema
from typing import Optional
import json

class AIManager:
    def __init__(self, client: IChatClient, safety_filter: CrisisSafetyFilter) -> None:
        self.__client = client
        self.__safety_filter = safety_filter
        self.__previous_interaction_id = None
        self.__survey_results = None
    
    def process_message(self, prompt: str, strategy: ICounsellingStrategy, ignore_message: bool = False) -> dict:
        self.__safety_filter.validate(prompt)

        system_instruction = strategy.get_system_instruction()

        json_response_schema = strategy.get_json_response_schema()
        response = self.__client.send_message(prompt, self.__previous_interaction_id, system_instruction, json_response_schema)

        # Add error handling if error

        self.__previous_interaction_id = response['id']

        survey_results = json.loads(response['output_text'])        

        survey_done = None
        if isinstance(strategy, CollectSurveyStrategy): 
            self.__survey_results = survey_results
            survey_done = survey_results['survey_done']
            ai_response = survey_results['text']
        else:
            ai_response = survey_results

        
        return {'text': ai_response, 'survey_done': survey_done}
        
    def show_survey_results(self, by_alias: bool = False, by_class = False):
        survey_results = SurveyEntitySchema(**self.__survey_results)

        del survey_results.text, survey_results.survey_done

        if by_class:
            return survey_results

        return survey_results.model_dump(by_alias=by_alias)
    
