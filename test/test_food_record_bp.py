import pytest
from flask import Flask
from datetime import date, time as dt_time
import pagelogic.bp.food_record_bp as bp


# ---------------------
# Dummy model
# ---------------------
class DummyRecord:
    def __init__(self, id=1):
        self.id = id

    def to_dict(self):
        return {"id": self.id}


# ---------------------
# Flask app
# ---------------------
@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(bp.food_record_bp)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


# ===============================================================
# create_food_record (GET)
# ===============================================================

def test_create_food_record_get_success(client, monkeypatch):
    monkeypatch.setattr(
        bp.food_record_repo,
        "create_food_record",
        lambda **k: 99
    )

    r = client.get("/create_food_record?user_id=3&food_id=7")
    assert r.status_code == 200
    assert r.get_json()["created_id"] == 99


# ===============================================================
# create_food_record (POST)
# ===============================================================

def test_create_food_record_post_missing_fields(client):
    r = client.post("/create_food_record", json={"user_id": 1})
    assert r.status_code == 400


def test_create_food_record_post_success(client, monkeypatch):
    monkeypatch.setattr(
        bp.food_record_repo,
        "create_food_record",
        lambda **k: 123
    )

    payload = {
        "user_id": 1,
        "food_id": 2,
        "eaten_date": "2025-01-15",
        "eaten_time": "08:30",
        "amount_numeric": 3.5,
        "unit": "g",
        "amount_literal": "half bowl",
        "notes": "test"
    }

    r = client.post("/create_food_record", json=payload)
    assert r.status_code == 200
    body = r.get_json()
    assert body["created_id"] == 123
    assert body["message"] == "Meal added successfully"


def test_create_food_record_post_bad_time(client, monkeypatch):
    monkeypatch.setattr(
        bp.food_record_repo,
        "create_food_record",
        lambda **k: 55
    )

    payload = {
        "user_id": 1,
        "food_id": 2,
        "eaten_time": "bad_time"
    }

    r = client.post("/create_food_record", json=payload)
    assert r.status_code == 200
    assert r.get_json()["created_id"] == 55


# ===============================================================
# get_food_record
# ===============================================================

def test_get_food_record_not_found(client, monkeypatch):
    monkeypatch.setattr(
        bp.food_record_repo,
        "get_food_record_by_id",
        lambda x: None
    )

    r = client.get("/get_food_record?id=5")
    assert r.status_code == 404


def test_get_food_record_success(client, monkeypatch):
    monkeypatch.setattr(
        bp.food_record_repo,
        "get_food_record_by_id",
        lambda x: DummyRecord(id=x)
    )

    r = client.get("/get_food_record?id=9")
    assert r.status_code == 200
    assert r.get_json()["id"] == 9


# ===============================================================
# get_food_records_by_user_id
# ===============================================================

def test_get_food_records_by_user_id(client, monkeypatch):
    monkeypatch.setattr(
        bp.food_record_repo,
        "get_food_records_by_user_id",
        lambda x: [DummyRecord(id=1), DummyRecord(id=2)]
    )

    r = client.get("/get_food_records_by_user_id?user_id=10")
    assert r.status_code == 200
    data = r.get_json()
    assert len(data) == 2
    assert data[0]["id"] == 1


# ===============================================================
# delete_food_record
# ===============================================================

def test_delete_food_record_not_found(client, monkeypatch):
    monkeypatch.setattr(
        bp.food_record_repo,
        "delete_food_record",
        lambda x: False
    )

    r = client.get("/delete_food_record?id=6")
    assert r.status_code == 404


def test_delete_food_record_success(client, monkeypatch):
    monkeypatch.setattr(
        bp.food_record_repo,
        "delete_food_record",
        lambda x: True
    )

    r = client.get("/delete_food_record?id=6")
    assert r.status_code == 200
    assert r.get_json()["id"] == 6


# ===============================================================
# update_food_record
# ===============================================================

def test_update_food_record_not_found(client, monkeypatch):
    monkeypatch.setattr(
        bp.food_record_repo,
        "update_food_record",
        lambda **k: False
    )

    r = client.get("/update_food_record?id=3&notes=test")
    assert r.status_code == 404


def test_update_food_record_success(client, monkeypatch):
    monkeypatch.setattr(
        bp.food_record_repo,
        "update_food_record",
        lambda **k: True
    )

    r = client.get("/update_food_record?id=3&notes=hello")
    assert r.status_code == 200
    assert r.get_json()["id"] == 3
