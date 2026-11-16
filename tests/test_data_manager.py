# test_data_manager.py
# Tests DataManager's user and assessment record functions against an in-memory fake of MongoDB

import copy
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
import pytest
from pymongo.errors import DuplicateKeyError
import data_manager as data_manager_module
from data_manager import DataManager
from data_manager_helper.AssessmentRecord import AssessmentRecord

MISSING = object()

# ---------- in-memory stand-in for pymongo ----------

# read a value from a nested dict using a dotten key
def get_path(doc, dotted):
    current = doc
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return MISSING
        current = current[part]
    return current

# true is document matches every key / value pair in the query
def matches(doc, query):
    return all(get_path(doc, key) == value for key, value in query.items())

# Mimics the result object pymongo returns from write operations
class FakeResult:
    def __init__(self, inserted_id=None, matched_count=0, deleted_count=0, upserted_id=None):
        self.inserted_id = inserted_id
        self.matched_count = matched_count
        self.deleted_count = deleted_count
        self.upserted_id = upserted_id

# store documents in a python list
class FakeCollection:
    def __init__(self):
        self.docs = []
        self.unique_fields = []
        self._next_id = 1

    # record which fields must be unique
    def create_index(self, keys, unique=False):
        if unique:
            for field, _ in keys:
                if field not in self.unique_fields:
                    self.unique_fields.append(field)

    # raise DuplicateKeyError if another document already has the same value in a unique field
    def _check_unique(self, doc, ignore=None):
        for field in self.unique_fields:
            value = get_path(doc, field)
            for existing in self.docs:
                if existing is not ignore and get_path(existing, field) == value:
                    raise DuplicateKeyError(f"duplicate value for {field}")

    # position of first document
    def _index_of(self, query):
        for i, doc in enumerate(self.docs):
            if matches(doc, query):
                return i
        return None

    # return all matching documents
    def find(self, query=None):
        return [copy.deepcopy(d) for d in self.docs if matches(d, query or {})]

    # insert a document
    def insert_one(self, doc):
        self._check_unique(doc)
        stored = copy.deepcopy(doc)
        stored["_id"] = self._next_id
        self._next_id += 1
        self.docs.append(stored)
        return FakeResult(inserted_id=stored["_id"])

    # apply a set update to the first document
    def update_one(self, query, update):
        i = self._index_of(query)
        if i is None:
            return FakeResult(matched_count=0)
        new_doc = {**self.docs[i], **update["$set"]}
        self._check_unique(new_doc, ignore=self.docs[i])
        self.docs[i] = new_doc
        return FakeResult(matched_count=1)

    # replcae a document or insert it
    def replace_one(self, query, new_doc, upsert=False):
        i = self._index_of(query)
        if i is not None:
            self._check_unique(new_doc, ignore=self.docs[i])
            stored = copy.deepcopy(new_doc)
            stored["_id"] = self.docs[i]["_id"]
            self.docs[i] = stored
            return FakeResult(matched_count=1)
        if upsert:
            return FakeResult(upserted_id=self.insert_one(new_doc).inserted_id)
        return FakeResult()

    # remove the first matching document
    def delete_one(self, query):
        i = self._index_of(query)
        if i is None:
            return FakeResult(deleted_count=0)
        del self.docs[i]
        return FakeResult(deleted_count=1)

    # remove every matching document
    def delete_many(self, query):
        before = len(self.docs)
        self.docs = [d for d in self.docs if not matches(d, query)]
        return FakeResult(deleted_count=before - len(self.docs))

# stands in for the MongoDBConnection
class FakeConnection:
    def __init__(self):
        self.collections = {}

    # report good connection
    def test_connection(self):
        return True

    # return the named collection
    def get_collection(self, name):
        return self.collections.setdefault(name, FakeCollection())

    def close(self):
        pass


# ---------- helpers and fixtures ----------

# use the fake connection
@pytest.fixture
def connection(monkeypatch):
    # one fake database shared by every DataManager created in the test
    conn = FakeConnection()
    monkeypatch.setattr(data_manager_module, "MongoDBConnection", lambda: conn)
    return conn

# DataManager
@pytest.fixture
def dm(connection):
    return DataManager()

#create user
@pytest.fixture
def alice(dm):
    return dm.create_user("alice", "hashed-pw")


@pytest.fixture
def bob(dm):
    return dm.create_user("bob", "hashed-pw")

# today date
def today_str():
    return datetime.now(ZoneInfo("Asia/Singapore")).strftime("%d-%m-%Y")

# Sample Data
def make_record(user_id, mental=30, date=None, time="09:00:00", record_id=None):
    """date=None gives a record stamped with the real current time (today)."""
    user_input = {
        "user_id": user_id, "sleep_duration": 7.0, "stress_level": 4,
        "focus_level": 6, "academic_workload": 5, "mood": "Calm",
        "social_activity_level": 6, "reflection": "Doing okay.",
    }
    ai_output = {
        "mental_wellness_risk_score": mental, "burnout_risk_score": 40,
        "sentiment": "Neutral", "crisis_alert": False,
        "primary_stressor": "Workload", "personalized_recommendations": "Rest well.",
    }
    logic_output = {
        "mental_wellness_risk_tier": "Low", "warnings": [], "route": "Self-care guidance",
        "counselling_recommendation": False, "display_messages": [],
    }
    if date is None:
        return AssessmentRecord(user_input, ai_output, logic_output)
    return AssessmentRecord(user_input, ai_output, logic_output,
                            record_id=record_id or str(uuid.uuid4()), date=date, time=time)


# ---------- user management ----------
# look up username and check
@pytest.mark.parametrize(
    "username, expected_found",
    [
        ("alice", True),
        ("nobody", False),
    ],
)

def test_user_lookup_by_username(dm, alice, username, expected_found):
    found = dm.get_user_by_username(username)
    assert (found is not None) is expected_found

# check id
def test_create_user_returns_id_that_resolves(dm):
    uid = dm.create_user("carol", "hashed-pw")
    assert uid is not None
    assert dm.get_user_by_id(uid).get_username() == "carol"

# check duplicate username
def test_duplicate_username_is_rejected(dm, alice):
    assert dm.create_user("alice", "another-pw") is None
    assert len(dm.get_users()) == 1

# only username and password can update
@pytest.mark.parametrize(
    "updates, expected_ok, expected_username",
    [
        ({"username": "alice2"}, True, "alice2"),
        ({"password": "new-hash"}, True, "alice"),
        ({"user_id": "hacked"}, False, "alice"),
        ({"username": "alice2", "user_id": "hacked"}, False, "alice"),
        ({}, False, "alice"),
        ("not-a-dict", False, "alice"),
    ],
)

#
def test_update_user(dm, alice, updates, expected_ok, expected_username):
    assert dm.update_user(alice, updates) is expected_ok
    assert dm.get_user_by_id(alice).get_username() == expected_username


def test_update_username_to_taken_name_is_rejected(dm, alice, bob):
    assert dm.update_user(alice, {"username": "bob"}) is False
    assert dm.get_user_by_id(alice).get_username() == "alice"


def test_delete_user_removes_only_their_records(dm, alice, bob):
    dm.save(make_record(alice, date="01-01-2026", record_id="a1"))
    dm.save(make_record(bob, date="01-01-2026", record_id="b1"))

    assert dm.delete_user(alice) is True

    assert dm.get_user_by_id(alice) is None
    assert dm.get_user_records(alice) == []
    assert len(dm.get_user_records(bob)) == 1


def test_delete_unknown_user_returns_false(dm):
    assert dm.delete_user("does-not-exist") is False


def test_users_and_records_reload_from_storage(connection, dm, alice):
    dm.save(make_record(alice, date="01-01-2026", record_id="r1"))

    # a fresh DataManager on the same database should load what was saved
    reloaded = DataManager()

    assert reloaded.get_user_by_username("alice").get_user_id() == alice
    assert [r.get_record_id() for r in reloaded.get_user_records(alice)] == ["r1"]


# ---------- assessment records ----------

def test_save_adds_record(dm, alice):
    assert dm.save(make_record(alice, date="01-01-2026", record_id="r1")) is True
    assert len(dm.get_records()) == 1


def test_save_rejects_non_record(dm):
    assert dm.save({"user_id": "x"}) is False


@pytest.mark.parametrize(
    "owner, date, expected_saved",
    [
        ("alice", None, True),            # today's record for the logged-in user
        ("bob", None, False),             # another user's record
        ("alice", "01-01-2026", False),   # not dated today
    ],
)
def test_replace_user_record_rules(dm, alice, bob, owner, date, expected_saved):
    owners = {"alice": alice, "bob": bob}
    record = make_record(owners[owner], date=date, record_id="r1")

    assert dm.replace_user_record(alice, record) is expected_saved
    assert len(dm.get_user_records(alice)) == (1 if expected_saved else 0)


def test_replace_user_record_overwrites_todays_record(dm, alice):
    dm.replace_user_record(alice, make_record(alice, mental=30))
    dm.replace_user_record(alice, make_record(alice, mental=55))

    records = dm.get_user_records(alice)
    assert len(records) == 1
    assert records[0].get_ai_output()["mental_wellness_risk_score"] == 55


def test_user_records_newest_first_and_per_user(dm, alice, bob):
    dm.save(make_record(alice, date="01-01-2026", record_id="a-old"))
    dm.save(make_record(alice, date="02-01-2026", record_id="a-new"))
    dm.save(make_record(bob, date="03-01-2026", record_id="b1"))

    ids = [r.get_record_id() for r in dm.get_user_records(alice)]

    assert ids == ["a-new", "a-old"]


@pytest.mark.parametrize(
    "saved_dates, expected_latest",
    [
        ([], None),
        (["01-01-2026"], "01-01-2026"),
        (["01-01-2026", "05-01-2026", "03-01-2026"], "05-01-2026"),
    ],
)
def test_get_latest_user_record(dm, alice, saved_dates, expected_latest):
    for i, date in enumerate(saved_dates):
        dm.save(make_record(alice, date=date, record_id=f"r{i}"))

    latest = dm.get_latest_user_record(alice)

    assert (None if latest is None else latest.get_date()) == expected_latest


def test_previous_attempts_exclude_today_and_are_oldest_first(dm, alice):
    dm.save(make_record(alice, date="01-01-2026", record_id="first"))
    dm.save(make_record(alice, date="02-01-2026", record_id="second"))
    dm.replace_user_record(alice, make_record(alice))  # today's, must be excluded

    attempts = dm.get_previous_attempts(alice)

    assert [a["record_id"] for a in attempts] == ["first", "second"]
    assert all(a["date"] != today_str() for a in attempts)


def test_user_int_records_extract_numeric_fields(dm, alice):
    dm.save(make_record(alice, mental=42, date="01-01-2026", record_id="r1"))

    rows = dm.get_user_int_records(dm.get_user_records(alice), alice)

    assert rows == [{
        "date": "01-01-2026",
        "sleep_duration": 7.0,
        "focus_level": 6,
        "stress_level": 4,
        "social_activity_level": 6,
        "mental_wellness_risk_score": 42,
        "burnout_risk_score": 40,
    }]


def test_user_int_records_only_include_requested_user(dm, alice, bob):
    dm.save(make_record(bob, date="01-01-2026", record_id="b1"))

    assert dm.get_user_int_records(dm.get_records(), alice) == []