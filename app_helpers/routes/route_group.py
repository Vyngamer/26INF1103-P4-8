'''
Base class for groups of related pages
'''

from abc import ABC, abstractmethod


# Every page group registers its routes the same way, so app.py can treat them all alike
# Endpoint names are given explicitly
class RouteGroup(ABC):

    def __init__(self, user_session):
        self._user_session = user_session

    # Adds this group's routes to the Flask app
    def register(self, app):
        for rule, endpoint, view, methods in self._routes():
            app.add_url_rule(rule, endpoint, view, methods=methods)

    # (rule, endpoint, view, methods) for every route in the group
    @abstractmethod
    def _routes(self):
        ...

    # Shortcut for views that need a logged-in user (see UserSession.login_required)
    def _protected(self, view):
        return self._user_session.login_required(view)