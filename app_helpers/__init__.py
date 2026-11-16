'''
Web app helper package used by app.py

user_session        - Logged-in user stored in Flask's session (UserSession)
chat_session        - One user's chatbot conversation (ChatSession)
chat_registry       - One ChatSession per logged-in user (ChatRegistry)
assessment_service  - Wellness check pipeline
                    - Survey answers -> AI scores -> business rules -> saved record (AssessmentService)

Routes
route_group         - Abstract base class for a group of pages (RouteGroup)
account_routes      - Register, login, logout & settings pages (AccountRoutes)
dashboard_routes    - Home, dashboard, history, result & progress pages (DashboardRoutes)
wellness_routes     - Chatbot wellness check pages (WellnessRoutes)
'''