'''
I/O helper package used by io_manager.py

AccountResult      - User account results (AccountResult)
AccountService     - User account actions (AccountService)
Prompt             - Abstract class for other prompts. (Prompt)
                    Child classes implement answer checks that
                    convert one given answer or reject it with a message
TextPrompt         - Text prompt for a single answer (TextPrompt)
RangePrompt        - Range prompt for a single answer (RangePrompt)
ChoicePrompt       - Choice prompt for a single answer (ChoicePrompt)
Questionnaire      - Survey questions and their answer checks (Questionnaire)
validators         - Username and password rules (username_errors, password_errors)
SurveyResponse     - One completed survey's answers (SurveyResponse)
SurveyResult       - One completed surveys' result (SurveyResults)

Errors
AccountError       - Account-related error (AccountError)
InvalidInput       - Invalid prompt answer error (InvalidInput)
AssessmentFailed   - Assessment failed error (AssessmentFailed)
SurveyAnswersError - Survey question input error (SurveyError)

'''