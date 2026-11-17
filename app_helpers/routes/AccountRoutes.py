'''
Account pages: register, login, logout and settings
'''

from flask import render_template, request, redirect, url_for, flash

from app_helpers.routes.RouteGroup import RouteGroup


# Turns account forms into IOManager calls and shows the result
# All validation checks stay in IO Manager's AccountService
class AccountRoutes(RouteGroup):

    def __init__(self, user_session, io_manager, chat_registry):
        super().__init__(user_session)
        self.__io_manager = io_manager
        self.__chat_registry = chat_registry

    def _routes(self):
        return [
            ("/register", "register", self.__register, ["GET", "POST"]),
            ("/login", "login", self.__login, ["GET", "POST"]),
            ("/logout", "logout", self.__logout, ["GET"]),
            ("/settings", "settings", self._protected(self.__settings), ["GET"]),
            ("/update_username", "update_username", self._protected(self.__update_username), ["GET", "POST"]),
            ("/update_password", "update_password", self._protected(self.__update_password), ["GET", "POST"]),
            ("/delete_account", "delete_account", self._protected(self.__delete_account), ["POST"]),
        ]

    def __register(self):
        if request.method == "POST":
            result = self.__io_manager.register(request.form.get("username"), request.form.get("password"),
                                                request.form.get("confirm"))
            if not result.ok:
                return render_template("register.html", error=result.message)
            flash(result.message)
            return redirect(url_for("login"))
        return render_template("register.html")

    def __login(self):
        if request.method == "POST":
            result = self.__io_manager.login(request.form.get("username"), request.form.get("password"))
            if not result.ok:
                return render_template("login.html", error=result.message)
            self._user_session.log_in(result.uid)
            return redirect(url_for("dashboard"))
        return render_template("login.html")

    def __logout(self):
        uid, _ = self._user_session.current_user()
        if uid is not None:
            self.__chat_registry.discard(uid)
        self._user_session.log_out()
        return redirect(url_for("main"))

    @staticmethod
    def __settings(uid, username):
        return render_template("settings.html", username=username)

    def __update_username(self, uid, username):
        if request.method == "GET":
            return redirect(url_for("settings"))
        result = self.__io_manager.change_username(uid, request.form.get("username"))
        if not result.ok:
            return render_template("settings.html", error1=result.message, username=username)
        flash(result.message)
        return render_template("settings.html", username=result.username)

    def __update_password(self, uid, username):
        if request.method == "GET":
            return redirect(url_for("settings"))
        result = self.__io_manager.change_password(uid, request.form.get("current"), request.form.get("newpw"),
                                                   request.form.get("confirm"))
        if not result.ok:
            return render_template("settings.html", username=username, error2=[result.message])
        flash(result.message)
        return render_template("settings.html", username=username)

    def __delete_account(self, uid, username):
        result = self.__io_manager.delete_account(uid, request.form.get("delete_password"),
                                                  request.form.get("confirm_text"))
        if not result.ok:
            return render_template("settings.html", username=username, error3=[result.message])
        self.__chat_registry.discard(uid)
        self._user_session.log_out()
        flash(result.message)
        return redirect(url_for("main"))