from ai_manager_helper.interfaces.counselling_strategy import ICounsellingStrategy
from ai_manager_helper.collect_survey_strategy import CollectSurveyStrategy
from ai_manager_helper.evaluate_survey_strategy import EvaluateSurveyStrategy

class CounsellingStrategyFactory:
    @staticmethod
    def create_strategy(strategy_type:str) -> ICounsellingStrategy:
        strategies = {
                'survey': CollectSurveyStrategy,
                'evaluate': EvaluateSurveyStrategy
        }

        return strategies[strategy_type]()

