# Project Initial Details of 26INF1103-P4-8

### App quickstart
```powershell
docker compose build

docker run --rm -it -v "${PWD}:/app" -e DISPLAY=:0 -v /run/desktop/mnt/host/wslg/.X11-unix:/tmp/.X11-unix ai-counsellor
```

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
| Mental Wellness Risk Tier | - | Mental Wellness Risk Score | High: Score ≥ 71; Medium: Score 41-70; Low: Score ≤ 40 |
| High Burnout Warning (Sleep) | Sleep Duration | Burnout Risk Score | Burnout Risk Score > 75 AND Sleep Duration < 6 |
| Burnout Warning (Workload) | Academic Workload | Burnout Risk Score | Burnout Risk Score > 60 AND Academic Workload ≥ 7 |
| Social Withdrawal Risk | Social Activity Level | Sentiment Analysis | Social Activity Level ≤ 3 AND Sentiment = “Negative” |
| Cognitive Fatigue Risk | Focus Level | Sentiment Analysis | Focus Level ≤ 4 AND Sentiment = “Negative” |
| Support Route | - | Crisis Alert, Mental Wellness Risk Score, Burnout Risk Score, Sentiment | Urgent support: Crisis Alert = True; Counsellor follow-up:  Mental Wellness Risk Tier = “High” OR two or more warning rules are triggered OR (Mental Wellness Risk Score ≥ 60 AND Burnout Risk Score ≥ 70 AND Sentiment = “Negative”); Self-care guidance: Neither of the conditions met |

Additionally, we use the user’s previous assessments to compare the current attempt with their historical average, latest attempt, and recent trends. These comparisons generate display messages separately from the original warnings. They are not stored in the JSON file.

| Rule | Current Data Used | Previous Data Used | Condition and Message |
|---|---|---|---|
| Sleep Reminder | Sleep Duration | None | Sleep Duration < 7 hours: remind the user to get more sleep. |
| Sleep Comparison | Sleep Duration | Average Sleep Duration | Report how many hours more or less the user slept compared with their previous average, rounded to two decimal places. Report no difference when equal. |
| Consecutive Social Decline | Social Activity Level | Latest three Social Activity Levels | A decrease of at least 1 point in each of three transitions across four consecutive attempts: show a social decline message. |
| Below-Average Social Activity | Social Activity Level | Average Social Activity Level | Show there is a 4-consecutive-attempt decline in social activity level. Else if the current level is at least 2 points below average: show a below-average message. |
| Focus Decline Since Last Attempt | Focus Level | Latest Focus Level | A decrease of at least 2 points: show a focus decline message. |
| Focus Improvement Since Last Attempt | Focus Level | Latest Focus Level | An increase of at least 1 point: show a focus improvement message. |
| Below-Average Focus | Focus Level | Average Focus Level | If neither latest-attempt focus rule matches and the current level is at least 2 points below average: show a below-average message. |
| Above-Average Focus | Focus Level | Average Focus Level | If neither latest-attempt focus rule matches and the current level is at least 1 point above average: show an improvement message. |
| Risk Score Improvement Since Last Attempt | Mental Wellness or Burnout Risk Score | Latest corresponding Risk Score | A decrease of at least 10 points: show an improvement message. |
| Risk Score Improvement Compared with Average | Mental Wellness or Burnout Risk Score | Average corresponding Risk Score | If the score has not increased since the latest attempt, the score will be compared with previous average. If the score is at least 10 points below average, show an improvement message. |

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
https://github.com/Vyngamer/26INF1103-P4-8
