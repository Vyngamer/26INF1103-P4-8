from __future__ import annotations

from tests.support.builders import Builder
from tests.support.survey_answers_builder import SurveyAnswersBuilder
from ai_manager_helper.data_classes.survey_entity_schema import SurveyEntitySchema


class SurveyPayloadBuilder(Builder[dict]):
    """The JSON the model returns for the survey-collection strategy (keys use the schema aliases)."""

    DEFAULTS = {**SurveyAnswersBuilder.DEFAULTS, "text": "Thanks, that's everything!", "survey_done": True}

    def build(self) -> dict:
        fields = SurveyEntitySchema.model_fields
        return {(fields[name].alias or name): value for name, value in self.values().items()}
