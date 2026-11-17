'''
Read-only pages: home, dashboard, history, result and progress
'''

from flask import render_template, request, redirect, url_for

from app_helpers.routes.RouteGroup import RouteGroup


# Shows a student's saved assessment records from Data Manager
class DashboardRoutes(RouteGroup):

    def __init__(self, user_session, data_manager):
        super().__init__(user_session)
        self.__data_manager = data_manager

    def _routes(self):
        return [
            ("/", "main", self.__main, ["GET"]),
            ("/dashboard", "dashboard", self._protected(self.__dashboard), ["GET"]),
            ("/history", "history", self._protected(self.__history), ["GET"]),
            ("/result", "result", self._protected(self.__result), ["GET", "POST"]),
            ("/progress", "progress", self._protected(self.__progress), ["GET", "POST"]),
        ]

    # Default page when the app runs
    @staticmethod
    def __main():
        return render_template("index.html")

    def __dashboard(self, uid, username):
        latest_attempt = self.__data_manager.get_latest_user_record(uid)
        return render_template("dashboard.html", username=username, latest_attempt=latest_attempt)

    def __history(self, uid, username):
        previous_attempts = self.__data_manager.get_user_records(uid)
        return render_template("history.html", username=username, previous_attempts=previous_attempts)

    def __result(self, uid, username):
        record_id = request.args.get("attempt_id")
        if record_id is None:
            return redirect(url_for("history"))
        # None uid is unknown or belongs to another user
        # results.html then says no results are available
        return render_template("results.html", choosen_attempt=self.__find_user_record(uid, record_id))

    def __progress(self, uid, username):
        # Progress graph needs at least two attempts, oldest first
        user_records = self.__data_manager.get_user_records(uid)
        history = None
        if len(user_records) > 1:
            history = self.__data_manager.get_user_int_records(user_records, uid)[::-1]
        return render_template("progress.html", history=history)

    # Looks only through this user's own records, so one student can't open another's result
    def __find_user_record(self, uid, record_id):
        for record in self.__data_manager.get_user_records(uid):
            if record.get_record_id() == record_id:
                return record
        return None