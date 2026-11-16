'''
Logged-in user (Flask session)
'''

import functools

from flask import session, redirect, url_for


# Wraps Flask's session cookie so no other class reads or writes 'user_id' directly
class UserSession:
    _SESSION_KEY = "user_id"
    _LOGIN_ENDPOINT = "login"

    def __init__(self, io_manager):
        self.__io_manager = io_manager

    # Returns (user id, username) of the logged-in user
    # or (None, None) if nobody is logged in or their account no longer exists
    def current_user(self):
        uid = session.get(self._SESSION_KEY)
        username = self.__io_manager.get_username(uid) if uid else None
        if username is None:
            session.pop(self._SESSION_KEY, None)
            return None, None
        return uid, username

    def log_in(self, uid):
        session[self._SESSION_KEY] = uid

    @staticmethod
    def log_out():
        session.clear()

    # Decorator for views that need a logged-in user.
    # Sends visitors to the login page; otherwise calls the view with (uid, username, ...)
    def login_required(self, view):
        @functools.wraps(view)
        def wrapper(*args, **kwargs):
            uid, username = self.current_user()
            if uid is None:
                return redirect(url_for(self._LOGIN_ENDPOINT))
            return view(uid, username, *args, **kwargs)
        return wrapper