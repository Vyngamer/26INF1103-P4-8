'''
Flask web app
'''

import os

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_mail import Mail

import threading
import logic_manager
import json
from datetime import date

from google.genai import types
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_mail import Mail
from dotenv import load_dotenv
from markupsafe import escape
from ai_manager_helper.ai_manager import AIManager
from data_manager import DataManager
from io_manager import IOManager
from LogicManager import LogicManager
from app_helpers.user_session import UserSession
from app_helpers.chat_registry import ChatRegistry
from app_helpers.assessment_service import AssessmentService
from app_helpers.routes.account_routes import AccountRoutes
from app_helpers.routes.dashboard_routes import DashboardRoutes
from app_helpers.routes.wellness_routes import WellnessRoutes


# Builds the whole web app & wires managers together.
class WellnessApp:
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587

    def __init__(self):
        load_dotenv()    # Load before anything reads .env

        self.__flask = Flask(__name__)
        self.__configure()
        self.__mail = Mail(self.__flask)

        # Initialize managers
        self.__data_manager = DataManager()
        self.__io_manager = IOManager(self.__data_manager)
        self.__logic_manager = LogicManager()

        # Initialize app helpers
        self.__user_session = UserSession(self.__io_manager)
        self.__chat_registry = ChatRegistry()
        self.__assessment_service = AssessmentService(self.__io_manager, self.__data_manager, self.__logic_manager,
                                                      self.__mail, os.environ.get("MAIL_USERNAME"))

        self.__route_groups = [
            AccountRoutes(self.__user_session, self.__io_manager, self.__chat_registry),
            DashboardRoutes(self.__user_session, self.__data_manager),
            WellnessRoutes(self.__user_session, self.__chat_registry, self.__assessment_service),
        ]

        for group in self.__route_groups:
            group.register(self.__flask)

        self.__flask.register_error_handler(404, self.__page_not_found)

    # Flask app, for `flask run`, Docker & tests
    @property
    def flask_app(self):
        return self.__flask

    def run(self, **options):
        self.__flask.run(**options)

    # Secret key & email settings come from .env
    def __configure(self):
        mail_username = os.environ.get("MAIL_USERNAME")
        self.__flask.secret_key = os.environ.get("FLASK_SECRET_KEY")
        self.__flask.config.update(
            MAIL_SERVER=self.MAIL_SERVER,
            MAIL_PORT=self.MAIL_PORT,
            MAIL_USE_TLS=True,
            MAIL_USE_SSL=False,
            MAIL_USERNAME=mail_username,
            MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD"),
            MAIL_DEFAULT_SENDER=mail_username,
        )

    # 404 page
    @staticmethod
    def __page_not_found(error):
        return render_template("errors/error_404.html"), 404


# Module-level app so `flask --app app run` (and Docker) keep working
app = WellnessApp().flask_app

if __name__ == "__main__":
    app.run()
