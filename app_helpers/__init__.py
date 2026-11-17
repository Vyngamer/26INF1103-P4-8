'''
Web app helper package used by app.py

UserSession         - Logged-in user stored in Flask's session (UserSession)
ChatSession         - One user's chatbot conversation (ChatSession)
ChatRegistry        - One ChatSession per logged-in user (ChatRegistry)
AssessmentService   - Wellness check pipeline
                    - Survey answers -> AI scores -> business rules -> saved record (AssessmentService)

Routes
RouteGroup          - Abstract base class for a group of pages (RouteGroup)
AccountRoutes       - Register, login, logout & settings pages (AccountRoutes)
DashboardRoutes     - Home, dashboard, history, result & progress pages (DashboardRoutes)
WellnessRoutes      - Chatbot wellness check pages (WellnessRoutes)
'''