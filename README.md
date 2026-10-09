# Project Initial Details of 26-INF1103-P4-8

### Problem Statement
Mental health challenges such as stress, anxiety, and burnout are increasingly common among students. Many students fail to recognise early warning signs of declining mental well-being until their academic performance, physical health, or social life is negatively affected. Existing wellness applications often provide generic advice and do not offer personalised analysis based on a student's individual circumstances.

### Target Users
The target users for this project are mainly polytechnic students and university students, along with school counsellors and student support services.

### User Inputs
We will ask the user to provide a series of inputs. Each input will need to have some form of validation.

| Input Name | Description | Data Type | Possible Values |
|---|---|---|---|
| Sleep Duration | Average hours of daily sleep over the past week | Integer | 0 - 24 |
| Stress Level | Current level of stress experienced | Integer | 1 - 10 (1 = Very Low, 10 = Very High) |
| Focus Level | Ability to concentrate on tasks and studies | Integer | 1 - 10 (1 = Very Poor, 10 = Excellent) | 
| Academic Workload | Overall academic workload from coursework | Integer | 1 - 10 (1 = Light, 10 = Very Heavy) |
| Mood for the Day | Current emotional state of the student | String | Motivated, Calm, Anxious, Sad, Exhausted |
| Social Activity Level | Frequency of social interaction and engagement | Integer | 1 - 10 (1 = Isolated, 10 = Very Social) |
| Reflection | Personal thoughts, experiences, or concerns | String | Free-response text |

### Use of AI
We will format a prompt with the user inputs and send it to the LLM. The LLM will analyse the prompt and output the following data.

| Output Name | Description | Data Type | Possible Values |
|---|---|---|---|
| Mental Wellness Risk Score | Overall mental wellness risk level | Integer | 0 - 100 |
| Sentiment Analysis | Overall emotional tone detected | String | Positive, Neutral, Negative |
| Burnout Risk Score | Likelihood of burnout | Integer | 0 - 100 |
| Crisis Alert | Indicates potential mental health crisis | Boolean | True, False |
| Primary Stressor | Main source of stress identified | String | 1-3 words |
| Personalized Recommendations | AI-generated wellness suggestions | String | Free-response text

### Business Rules
We will create rules by combining user inputs and AI-generated outputs to identify mental wellness risks and provide appropriate alerts and recommendations.

| Rule | User Input Used | AI Output Used | Condition |
|---|---|---|---|
| Mental Wellness Risk Tier | - | Mental Wellness Risk Score | High: Score ≥ 71 Medium: Score 41-70 Low: Score ≤ 40 |
| High Burnout Warning (Sleep) | Sleep Duration | Burnout Risk Score | Burnout Risk Score > 75 AND Sleep Duration < 6 |
| Burnout Warning (Workload) | Academic Workload | Burnout Risk Score | Burnout Risk Score > 60 AND Academic Workload ≥ 7 |
| Social Withdrawal Risk | Social Activity Level | Sentiment Analysis | Social Activity Level ≤ 3 AND Sentiment = “Negative” |
| Cognitive Fatigue Risk | Focus Level | Sentiment Analysis | Focus Level ≤ 4 AND Sentiment = “Negative” |
| Counselling Recommendation | Social Activity Level, Focus Level | Crisis Alert | Crisis Alert = True OR Mental Wellness Risk Tier = “High” OR two or more warning rules are triggered |

#### Sample Output Report to User: <br>
Mental Wellness Risk: High (78/100) <br>
Burnout Risk: High (82/100) <br>
Sentiment: Negative <br>
Primary Stressor: Assignment deadlines <br>
Crisis Alert: False <br>
Alert: High Burnout Warning <br>
Recommendation: Prioritise sleep and manage assignment deadlines with a study plan.

### Repository information
The link to the repository can be found here:
https://github.com/Vyngamer/26-INF1103-P4-8
