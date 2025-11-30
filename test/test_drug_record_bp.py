import pytest
from flask import Flask
from datetime import date, time
import pagelogic.bp.drug_record_bp as bp


# ------------------------------
# Fake repo class
# ------------------------------

class DummyRecord:
    def __init__(self, id=1, user_id=1, drug_id=2):
        self.id = id
        self.user_id = user_id
        self.drug_id = drug_id

    def to_dict(self):
        return {"id": self.id, "drug_id": self.drug_id, "user_id": self.user_id}


# ------------------------------
# Fixtures
# ------------------------------

@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(bp.drug_record_bp)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


# =====================================================================================
# /get_drug_record_by_id
# =====================================================================================

def test_get_drug_record_missing_id(client):
    r = client.get("/get_drug_record_by_id")
    assert r.status_code == 400


def test_get_drug_record_not_found(client, monkeypatch):
    monkeypatch.setattr(bp.drug_record_repo,
                        "get_drug_record_by_id",
                        lambda x: None)
    r = client.get("/get_drug_record_by_id?id=10")
    assert r.status_code == 404


def test_get_drug_record_success(client, monkeypatch):
    dummy = DummyRecord(id=5)
    monkeypatch.setattr(bp.drug_record_repo,
                        "get_drug_record_by_id",
                        lambda x: dummy)
    r = client.get("/get_drug_record_by_id?id=5")
    assert r.status_code == 200
    assert r.get_json()["id"] == 5


# =====================================================================================
# /get_drug_records_by_user_id
# =====================================================================================

def test_records_by_uid_missing(client):
    r = client.get("/get_drug_records_by_user_id")
    assert r.status_code == 400


def test_records_by_uid_success(client, monkeypatch):
    monkeypatch.setattr(bp.drug_record_repo,
                        "get_drug_records_by_user_id",
                        lambda uid: [DummyRecord(id=1), DummyRecord(id=2)])

    r = client.get("/get_drug_records_by_user_id?user_id=1")
    assert r.status_code == 200
    assert len(r.get_json()) == 2


# =====================================================================================
# /delete_drug_record
# =====================================================================================

def test_delete_missing(client):
    r = client.get("/delete_drug_record")
    assert r.status_code == 400


def test_delete_not_found(client, monkeypatch):
    monkeypatch.setattr(bp.drug_record_repo,
                        "delete_drug_record",
                        lambda rid: False)
    r = client.get("/delete_drug_record?id=9")
    assert r.status_code == 404


def test_delete_success(client, monkeypatch):
    monkeypatch.setattr(bp.drug_record_repo,
                        "delete_drug_record",
                        lambda rid: True)
    r = client.get("/delete_drug_record?id=9")
    assert r.status_code == 200


# =====================================================================================
# /update_drug_record
# =====================================================================================

def test_update_missing_id(client):
    r = client.get("/update_drug_record")
    assert r.status_code == 400


def test_update_invalid_dosage(client):
    r = client.get("/update_drug_record?id=1&dosage_numeric=abc")
    assert r.status_code == 400


def test_update_not_found(client, monkeypatch):
    monkeypatch.setattr(bp.drug_record_repo,
                        "update_drug_record",
                        lambda **k: False)
    r = client.get("/update_drug_record?id=5")
    assert r.status_code == 404


def test_update_success(client, monkeypatch):
    monkeypatch.setattr(bp.drug_record_repo,
                        "update_drug_record",
                        lambda **k: True)
    r = client.get("/update_drug_record?id=5&status=TAKEN&dosage_numeric=1.5")
    assert r.status_code == 200


# =====================================================================================
# /create_drug_record_test
# =====================================================================================

def test_create_record_test(client, monkeypatch):
    monkeypatch.setattr(bp.drug_record_repo,
                        "create_drug_record",
                        lambda **k: 99)
    r = client.get("/create_drug_record_test?user_id=2&drug_id=1001")
    assert r.status_code == 200
    assert r.get_json()["id"] == 99


# =====================================================================================
# POST /create_drug_record
# =====================================================================================

def test_create_missing_json(client):
    r = client.post(
        "/create_drug_record",
        data="",                       
        content_type="application/json"
    )
    assert r.status_code == 400



def test_create_missing_required(client):
    r = client.post("/create_drug_record", json={"user_id": 1})
    assert r.status_code == 400


def test_create_success(client, monkeypatch):
    monkeypatch.setattr(bp.drug_record_repo,
                        "create_drug_record",
                        lambda **k: 55)
    payload = {
        "user_id": 1,
        "drug_id": 2,
        "taken_date": "2024-01-01",
        "taken_time": "12:30:00"
    }
    r = client.post("/create_drug_record", json=payload)
    assert r.status_code == 200
    assert r.get_json()["id"] == 55


# =====================================================================================
# POST /mark_drug_taken
# =====================================================================================

def test_mark_missing_fields(client):
    r = client.post("/mark_drug_taken", json={})
    assert r.status_code == 400


def test_mark_invalid_ids(client):
    r = client.post("/mark_drug_taken", json={
        "user_id": "x",
        "drug_id": 2,
        "plan_item_id": 3,
        "expected_date": "2024-01-01"
    })
    assert r.status_code == 400


def test_mark_invalid_date(client):
    r = client.post("/mark_drug_taken", json={
        "user_id": 1,
        "drug_id": 2,
        "plan_item_id": 3,
        "expected_date": "BAD"
    })
    assert r.status_code == 400


def test_mark_invalid_time(client):
    r = client.post("/mark_drug_taken", json={
        "user_id": 1,
        "drug_id": 2,
        "plan_item_id": 3,
        "expected_date": "2024-01-01",
        "expected_time": "25:99"
    })
    assert r.status_code == 400


def test_mark_toggle_existing(client, monkeypatch):
    dummy = DummyRecord(id=123)

    monkeypatch.setattr(bp.drug_record_repo,
                        "get_drug_record_by_unique",
                        lambda **k: dummy)

    monkeypatch.setattr(bp.drug_record_repo,
                        "delete_drug_record",
                        lambda rid: True)

    r = client.post("/mark_drug_taken", json={
        "user_id": 1,
        "drug_id": 2,
        "plan_item_id": 3,
        "expected_date": "2024-01-01"
    })
    assert r.status_code == 200
    assert r.get_json()["action"] == "deleted"


def test_mark_create_invalid_status(client, monkeypatch):
    monkeypatch.setattr(bp.drug_record_repo,
                        "get_drug_record_by_unique",
                        lambda **k: None)

    r = client.post("/mark_drug_taken", json={
        "user_id": 1,
        "drug_id": 2,
        "plan_item_id": 3,
        "expected_date": "2024-01-01",
        "status": "WRONG"
    })
    assert r.status_code == 400


def test_mark_create_success(client, monkeypatch):
    monkeypatch.setattr(bp.drug_record_repo,
                        "get_drug_record_by_unique",
                        lambda **k: None)

    monkeypatch.setattr(bp.drug_record_repo,
                        "create_drug_record",
                        lambda **k: 789)

    r = client.post("/mark_drug_taken", json={
        "user_id": 1,
        "drug_id": 2,
        "plan_item_id": 3,
        "expected_date": "2024-01-01",
        "status": "ON_TIME",
        "timing_flag": "EARLY"
    })
    assert r.status_code == 200
    assert r.get_json()["id"] == 789
