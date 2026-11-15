from google import genai
from google.genai import types
from google.genai._gaos.lib.compat_errors import APIConnectionError, NotFoundError
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from ai_manager_helper.data_classes.survey_entity_schema import SurveyEntitySchema
from ai_manager_helper.data_classes.conversation import Conversation

import re
import logging
import json

logger = logging.getLogger(__name__)

class IChatClient(ABC):
    @abstractmethod
    def send_message(self, prompt: str, previous_interaction_id: str, system_instruction: Optional[str] = None, json_response_schema: Optional[dict] = None):
        pass

class ICounsellingStrategy(ABC):
    @abstractmethod
    def get_system_instruction(self) -> str:
        pass
    
    @abstractmethod
    def get_json_response_schema(self) -> dict:
        pass

class IMessage(ABC):
    @abstractmethod
    def asdict(self) -> dict:
        pass

class IChatRepository(ABC):
    @abstractmethod
    def add_message(self, message):
        pass

    @abstractmethod
    def logs(self):
        pass

class GeminiClient(IChatClient):
    def __init__(self, model: str, retry_config: types.HttpRetryOptions) -> None:
        self.__model = model
        self.__retry_config = retry_config
        self.__client = None

    def connect_client(self) -> None:
        self.__client = genai.Client(
            http_options=types.HttpOptions(
                retry_options=retry_config,
                timeout=120*1000,
            )
        )

    def send_message(self, prompt: str, previous_interaction_id: str, system_instruction: Optional[str] = None, json_response_schema: Optional[dict] = None) -> str:
        interaction = self.__client.interactions.create(
            model=self.__model,
            input=prompt,
            system_instruction=system_instruction,
            previous_interaction_id=previous_interaction_id,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": json_response_schema
            },
        )

        return interaction.model_dump()


class GeminiClientWithFallback(IChatClient):
    def __init__(self, primary_model: IChatClient, fallback_model: IChatClient) -> None:
        self.__primary = primary_model
        self.__fallback = fallback_model

    def send_message(self, prompt: str, previous_interaction_id: str, system_instruction: Optional[str] = None, json_response_schema: Optional[dict] = None):
        try:
            return self.__primary.send_message(prompt, previous_interaction_id, system_instruction, json_response_schema)

        except (APIConnectionError, NotFoundError) as e:
            logger.warning(
                f"Primary AI model failed with error: {str(e)}. "
                "Switching to fallback model..."
            )

            try: 
                self.__fallback.connect_client()
                return self.__fallback.send_message(prompt, previous_interaction_id, system_instruction, json_response_schema)
                
            except Exception as e:
                logger.error(f"Fallback AI model also failed: {str(e)}")
                raise Exception("All AI counselling services are currently unavailable.")

class CrisisSafetyFilter:
    CRISIS_KEYWORDS = [
        r"suicide", r"kill myself", r"end it all", r"want to die", 
        r"self[-\s]harm", r"hurt myself"
    ]

    def validate(self, text: str) -> None:
        text_lower = text.lower()
        for pattern in self.CRISIS_KEYWORDS:
            if re.search(pattern, text_lower):
                raise Exception("Crisis Detected")

class CollectSurveyStrategy(ICounsellingStrategy):
    def get_system_instruction(self) -> str:
        return """
            You are an expert student counselor and psychological assessment AI based in Singapore specializing in adolescent 
            and higher education mental health. Your job is to conduct a survey to collect information on these fields: 
            - Sleep Duration: Average daily sleep hours over past week (0-24), The user had {sleep} hours of sleep. -1
            for undefined
            - Stress Level: Current stress (1 = Very Low, 10 = Very High), the user's stress level is {stress} out of 10.
            -1 for undefined 
            - Focus Level: Ability to concentrate (1 = Very Poor, 10 = Excellent), the user's focus level is {focus} out 
            of 10. -1 for undefined
            - Academic Workload: Coursework load (1 = Light, 10 = Very Heavy), the user's academic workload is {workload}
            out of 10. -1 for undefined
            - Mood for the Day: Emotional state ["Motivated", "Calm", "Anxious", "Sad", "Exhausted", "Undefined"], the 
            user's mood is {mood}. Undefined should not be listed and is only used as a placeholder for when the question
            has not been answered.
            - Social Activity Level: Engagement level (1 = Isolated, 10 = Very Social), the user's social activity level 
            is {social} out of 10. "Undefined" for undefined.
            - Reflection: Free-response text capturing personal thoughts/concerns, the user's reflection text is {reflection}.

            You are to be affable, kind, and conversational when conducting this survey.

            Identify the entities defined in the response json format and do not guess. If the user is not clear
            in any of the data fields then do not change the fields. For example, if the user mentions that 
            he/she only had 5 hours of sleep on average, then only fill in the json response for sleep duration.

            The fields are quantitative, so only fill them in when the user explicitly states the field value. If 
            the user vaguely answers the questions without providing a valid data value then re-prompt the question.

            Strictly adhere to the range stated within the fields. If the user uses hyperbole then default to the 
            corresponding end of the range.
        """

    def get_json_response_schema(self) -> dict:
        return SurveyEntitySchema.model_json_schema()

class EvaluateSurveyStrategy(ICounsellingStrategy):
    def get_system_instruction(self) -> str:
        return """
            You are an expert student counselor and psychological assessment AI specializing in adolescent and higher education mental health.

            Your job is to analyze quantitative student wellness metrics alongside qualitative reflection text to produce a structured JSON mental health assessment.

            Only answer questions related to the user's mental health.

            ### INPUT DATA DEFINITIONS

            - Sleep Duration: Average daily sleep hours over the past week (0-24). The user had {sleep} hours of sleep.
            - Stress Level: Current stress (1 = Very Low, 10 = Very High). The user's stress level is {stress} out of 10.
            - Focus Level: Ability to concentrate (1 = Very Poor, 10 = Excellent). The user's focus level is {focus} out of 10.
            - Academic Workload: Coursework load (1 = Light, 10 = Very Heavy). The user's academic workload is {workload} out of 10.
            - Mood for the Day: Emotional state ["Motivated", "Calm", "Anxious", "Sad", "Exhausted"]. The user's mood is {mood}.
            - Social Activity Level: Engagement level (1 = Isolated, 10 = Very Social). The user's social activity level is {social} out of 10.
            - Reflection: Free-response text capturing personal thoughts and concerns. The user's reflection text is {reflection}.

            ### EVALUATION & SCORING RUBRIC

            1. Mental Wellness Risk Score (0-100):
            - Baseline calculation: Aggregate high stress, low focus, poor sleep (<6 hours), low social activity (<=3), and negative mood ("Anxious", "Sad", "Exhausted").
            - Qualitative Adjustment: Analyze the reflection text.
                - Expressing hopelessness, feeling overwhelmed, or severe anxiety increases the score by +15 to +30 points.
                - Neutral or constructive reflection keeps the baseline score intact.
                - Expressing positive coping mechanisms or a calm mindset decreases the score by -10 to -20 points.
            - Scale: 0-40 (Low Risk), 41-70 (Medium Risk), 71-100 (High Risk).

            2. Burnout Risk Score (0-100):
            - Heavily weight the interaction between Academic Workload (>=7), Sleep Duration (<6h), Focus Level (<=2), and Mood ("Exhausted" or "Anxious").
            - High Workload + Low Sleep + Low Focus = Automatic score >70.
            - High Workload balanced by High Sleep and High Social Activity = Moderate score (40-60).

            3. Crisis Alert (Boolean: true/false):
            - MUST BE true IF AND ONLY IF:
                - Reflection text contains thoughts or explicit mentions of self-harm, suicidal ideation, feeling completely hopeless or giving up on life, feeling unsafe, or extreme mental breakdowns.
                - OR Mental Wellness Risk Score is extremely high (>=85) with social activity = 1 and severe sleep deprivation (<4 hours).
            - Otherwise MUST BE false.

            4. Sentiment Analysis (Strictly one of: "Positive", "Neutral", "Negative"):
            - Primary basis: The reflection text combined with emotional mood state.
            - "Exhausted", "Anxious", or "Sad" with distressed reflection = "Negative".
            - "Motivated" or "Calm" with positive reflection = "Positive".
            - Balanced or matter-of-fact reflections = "Neutral".

            5. Primary Stressor (1-3 Words):
            - Summarize the single greatest contributor to their current state.
            - Examples: "Academic Workload", "Sleep Deprivation", "Social Isolation", "Exam Anxiety", "Time Management".

            6. Personalized Recommendations (String):
            - Provide a concise (2-3 sentences), warm, empathetic, and actionable wellness suggestion.
            - Tailor recommendations directly to the user's specific metrics.
            - For example, if sleep <5 hours, focus on improving sleep habits before tackling workload.
        """
    
    def get_json_response_schema(self) -> dict:
        return {"type": "object",
                "properties": {
                    "mental_wellness_risk_score": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100
                    },
                    "burnout_risk_score": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100
                    },
                    "sentiment": {
                        "type": "string",
                        "enum": ["Positive", "Neutral", "Negative"]
                    },
                    "crisis_alert": {
                        "type": "boolean"
                    },
                    "primary_stressor": {
                        "type": "string"
                    },
                    "personalized_recommendations": {
                        "type": "string"
                    }
                },
                "required": [
                    "mental_wellness_risk_score",
                    "burnout_risk_score",
                    "sentiment",
                    "crisis_alert",
                    "primary_stressor",
                    "personalized_recommendations"]}

class CounsellingStrategyFactory:
    @staticmethod
    def create_strategy(strategy_type:str) -> ICounsellingStrategy:
        strategies = {
                'survey': CollectSurveyStrategy,
                'evaluate': EvaluateSurveyStrategy
        }

        return strategies[strategy_type]()

class AIManager:
    def __init__(self, client: IChatClient, conversation: IChatRepository, safety_filter: CrisisSafetyFilter) -> None:
        self.__client = client
        self.__conversation = conversation
        self.__safety_filter = safety_filter
        self.__previous_interaction_id = None
        self.__instruction_flag = True
        self.__survey_results = None
    
    def process_message(self, prompt: str, strategy: ICounsellingStrategy) -> dict:
        self.__safety_filter.validate(prompt)
        self.__conversation.add_message('user', 'YT', prompt)

        system_instruction = ""
        if self.__instruction_flag:
            system_instruction = strategy.get_system_instruction()
            self.__instruction_flag = False

        json_response_schema = strategy.get_json_response_schema()
        response = self.__client.send_message(prompt, self.__previous_interaction_id, system_instruction, json_response_schema)

        # Add error handling if error

        self.__previous_interaction_id = response['id']
        self.__survey_results = json.loads(response['output_text'])
        ai_response = self.__survey_results['text']
        self.__conversation.add_message('ai', 'AI', ai_response)
        
        return {'text': ai_response, 'survey_done': self.__survey_results['survey_done']}
    
if __name__ == "__main__":

    retry_config = types.HttpRetryOptions(
        attempts=5,                         
        initial_delay=2.0,                  
        max_delay=60.0,                     
        http_status_codes=[408, 429, 500, 502, 503, 504],
    )     

    primary_client = GeminiClient('gemini-3.5-flash-lite', retry_config)
    primary_client.connect_client()
    fallback_client = GeminiClient('gemini-3.1-flash-lite', retry_config)
    client = GeminiClientWithFallback(primary_client, fallback_client)

    conversation = Conversation()
    ai_manager = AIManager(client, conversation)
    collect_survey_strategy = CounsellingStrategyFactory.create_strategy('survey')
    print(ai_manager.process_message('Hello!', collect_survey_strategy)['text'])
