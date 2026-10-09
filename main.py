import questionnaire
import io_manager
import data_manager
import ai_manager
import logic_manager
import json

user_id = 'user1'
database_file = 'records.json'

user_input = questionnaire.prompt_questionnaire()
interaction = ai_manager.generate_survey_response(user_input)

interaction_id = interaction.id
ai_output = json.loads(interaction.output_text)

print(ai_output)

logic_output = logic_manager.assess(user_input, ai_output)

record = {
    "user_input": user_input,
    "ai_output": ai_output,
    "logic_output": logic_output
}

data_manager.save(record, database_file, user_id)
