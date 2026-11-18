'''
Web app tests (app.py and app_helper/)
Runs the real Flask app, managers and templates with an in-memory database & a fake chatbot
'''

import importlib
import json
import sys
from urllib.parse import urlparse, parse_qs

import pytest
from unittest.mock import MagicMock

PASSWORD = "pass1!"
ANSWERS = {"sleep_duration": 7.5, "stress_level": 5, "focus_level": 6, "academic_workload": 4,
           "mood": "Calm", "social_activity_level": 6, "reflection": "Good week"}
AI_SCORES = {"mental_wellness_risk_score": 30, "burnout_risk_score": 20, "sentiment": "Positive",
             "crisis_alert": False, "primary_stressor": "None", "personalized_recommendations": "Keep it up."}


# In-memory stand-in for MongoDBStorage (same methods, no database)
class FakeStorage:
    def __init__(self, collection, unique_fields=None):
        self.documents = []

    @staticmethod
    def _matches(document, query):
        for key, wanted in query.items():
            value = document
            for part in key.split("."):
                value = value.get(part) if isinstance(value, dict) else None
            if value != wanted:
                return False
        return True

    def load(self):
        return [dict(document) for document in self.documents]

    def save(self, data):
        self.documents.append(dict(data))
        return str(len(self.documents))

    def update(self, query, updates):
        for document in self.documents:
            if self._matches(document, query):
                document.update(updates)
                return True
        return False

    def delete(self, query):
        before = len(self.documents)
        self.documents = [d for d in self.documents if not self._matches(d, query)]
        return len(self.documents) < before

    def delete_many(self, query):
        before = len(self.documents)
        self.documents = [d for d in self.documents if not self._matches(d, query)]
        return before - len(self.documents)

    def replace_today(self, user_id, today, new_record):
        self.delete_many({"user_input.user_id": user_id, "date": today})
        self.documents.append(dict(new_record))
        return True


# Scripted chatbot settings, changed per test with monkeypatch.setitem
BOT = {"answers": ANSWERS, "scores": AI_SCORES, "ai_fails": False}
BOTS = []    # Every chatbot made, in order


def last_prompt(bot):
    return bot.prompt_bot.call_args.args[0]


def sign_up(web, username):
    client = web.test_client()
    client.post("/register", data={"username": username, "password": PASSWORD, "confirm": PASSWORD})
    client.post("/login", data={"username": username, "password": PASSWORD})
    return client


def finish_survey(client):
    client.get("/wellness-check")
    client.get("/get-bot-response")
    return client.get("/submit_survey")


# --- Pages and login ---

@pytest.mark.parametrize("path", ["/dashboard", "/history", "/progress", "/settings", "/wellness-check",
                                  "/result?attempt_id=x", "/get-bot-response", "/submit_survey"])
def test_pages_need_login(web, path):
    response = web.test_client().get(path)
    assert response.status_code == 302 and response.location.endswith("/login")


def test_register_login_and_pages(web):
    client = sign_up(web, "alice")
    for path in ["/", "/dashboard", "/history", "/progress", "/settings"]:
        assert client.get(path).status_code == 200
    assert b"alice" in client.get("/dashboard").data


def test_unknown_page_is_404(web):
    assert web.test_client().get("/no-such-page").status_code == 404


def test_logout(web):
    client = sign_up(web, "alice")
    client.get("/logout")
    assert client.get("/dashboard").location.endswith("/login")


# --- Chatbot ---

def test_chat_greets_then_replies(web):
    client = sign_up(web, "alice")
    assert client.get("/wellness-check").status_code == 200
    assert client.get("/get-bot-response").get_json()["message"] == "reply to Hello!"
    assert client.post("/get", data={"msg": "I slept 7 hours"}).get_json() == {
        "text": "reply to I slept 7 hours", "survey_done": True}


def test_each_student_has_their_own_chat(web):
    alice, bob = sign_up(web, "alice"), sign_up(web, "bob")
    alice.get("/wellness-check")
    alice.get("/get-bot-response")
    alice.post("/get", data={"msg": "private message"})
    bob.get("/wellness-check")
    bob.get("/get-bot-response")
    assert b"private message" in alice.get("/wellness-check").data
    assert b"private message" not in bob.get("/wellness-check").data
    assert len(BOTS) == 2


def test_confirm_survey_shows_answers(web):
    client = sign_up(web, "alice")
    client.get("/wellness-check")
    assert b"Good week" in client.get("/confirm-survey").data


def test_confirm_without_answers_returns_to_chat(web, monkeypatch):
    monkeypatch.setitem(BOT, "answers", None)
    client = sign_up(web, "alice")
    assert "/wellness-check/True" in client.get("/confirm-survey").location
    assert "/wellness-check/True" in client.get("/submit_survey").location


def test_deny_survey(web):
    client = sign_up(web, "alice")
    client.get("/wellness-check")
    client.get("/get-bot-response")
    assert "/wellness-check/True" in client.get("/deny-survey").location
    client.get("/get-bot-response")
    assert BOTS[0].deny_survey.call_count == 1
    assert last_prompt(BOTS[0]) == "The survey results are not accurate."


# --- Assessment ---

def test_submit_survey_saves_and_shows_result(web):
    client = sign_up(web, "alice")
    response = finish_survey(client)
    record_id = parse_qs(urlparse(response.location).query)["attempt_id"][0]
    assert urlparse(response.location).path == "/result"
    assert client.get(response.location).status_code == 200
    assert b"Keep it up." in client.get(response.location).data
    assert web.emails == []

    # The finished chat is discarded, so the next wellness check starts fresh (and knows it's done today)
    page = client.get("/wellness-check").data
    assert len(BOTS) == 2
    assert record_id in client.get("/history").data.decode()
    assert b"redoModal" in page


def test_other_students_cannot_open_a_result(web):
    alice = sign_up(web, "alice")
    location = finish_survey(alice).location
    bob = sign_up(web, "bob")
    assert b"Keep it up." not in bob.get(location).data


def test_invalid_answers_go_back_to_chatbot(web, monkeypatch):
    monkeypatch.setitem(BOT, "answers", {**ANSWERS, "stress_level": 11})
    client = sign_up(web, "alice")
    assert finish_survey(client).location.endswith("/wellness-check")
    client.get("/get-bot-response")
    assert BOTS[0].deny_survey.call_count == 1
    assert last_prompt(BOTS[0]).startswith("Some answers need to be fixed: Stress Level")


def test_failed_assessment_offers_retry(web, monkeypatch):
    monkeypatch.setitem(BOT, "ai_fails", True)
    client = sign_up(web, "alice")
    assert finish_survey(client).location.endswith("/confirm-survey")
    assert b"couldn&#39;t finish your assessment" in client.get("/confirm-survey").data
    assert web.emails == []


def test_counsellor_emailed_when_needed(web, monkeypatch):
    monkeypatch.setitem(BOT, "scores", {**AI_SCORES, "crisis_alert": True})
    client = sign_up(web, "alice")
    finish_survey(client)
    assert web.emails == ["alice"]


# --- Account settings ---

def test_delete_account_checks_password_and_confirmation(web):
    client = sign_up(web, "alice")
    page = client.post("/delete_account", data={"delete_password": "wrong1!", "confirm_text": "delete"}).data.decode()
    assert "Incorrect password" in page and "Type DELETE" in page
    assert client.get("/dashboard").status_code == 200    # still logged in, account kept


def test_delete_account(web):
    client = sign_up(web, "alice")
    finish_survey(client)
    response = client.post("/delete_account", data={"delete_password": PASSWORD, "confirm_text": "DELETE"})
    assert response.location.endswith("/")
    assert client.get("/dashboard").location.endswith("/login")
    assert client.post("/login", data={"username": "alice", "password": PASSWORD}).status_code == 200    # not logged in


def test_change_username(web):
    client = sign_up(web, "alice")
    client.post("/update_username", data={"username": "alicia"})
    assert b"alicia" in client.get("/settings").data