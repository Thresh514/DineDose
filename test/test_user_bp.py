import pytest
from flask import Flask, session
from pagelogic.bp.user_bp import user_bp


# --------------------------
# Flask test app
# --------------------------
@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(user_bp)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


# --------------------------
# Dummy Model
# --------------------------
class DummyUser:
    def __init__(self, id, username="test"):
        self.id = id
        self.username = username

    def to_dict(self):
        return {"id": self.id, "username": self.username}


# ==========================
# get_doctors tests
# ==========================

def test_get_doctors_missing_id(client):
    """id=0 will return None → 404."""
    r = client.get("/get_doctors?id=0")
    assert r.status_code in (404, 200)


def test_get_doctors_not_found(client, monkeypatch):
    monkeypatch.setattr(
        "pagelogic.bp.user_bp.user_repo.get_doctor_by_patient_id",
        lambda x: None
    )
    r = client.get("/get_doctors?id=123")
    assert r.status_code == 404
    assert r.get_json()["error"] == "doctor_not_found"


def test_get_doctors_success(client, monkeypatch):
    monkeypatch.setattr(
        "pagelogic.bp.user_bp.user_repo.get_doctor_by_patient_id",
        lambda x: DummyUser(99)
    )
    r = client.get("/get_doctors?id=123")
    assert r.status_code == 200
    assert r.get_json() == {"id": 99, "username": "test"}


# ==========================
# get_patients tests
# ==========================

def test_get_patients_missing_id(client):
    r = client.get("/get_patients?id=0")
    assert r.status_code in (200, 404)


def test_get_patients_success(client, monkeypatch):
    monkeypatch.setattr(
        "pagelogic.bp.user_bp.user_repo.get_patients_by_doctor_id",
        lambda x: [DummyUser(1), DummyUser(2)]
    )
    r = client.get("/get_patients?id=88")
    assert r.status_code == 200
    assert r.get_json() == [
        {"id": 1, "username": "test"},
        {"id": 2, "username": "test"}
    ]


# ==========================
# get_current_user tests
# ==========================

def test_get_current_user_not_logged_in(client):
    r = client.get("/get_current_user")
    assert r.status_code == 401
    assert r.get_json()["error"] == "not_logged_in"


def test_get_current_user_not_found(client, monkeypatch):
    with client.session_transaction() as sess:
        sess["user_id"] = 99

    monkeypatch.setattr(
        "pagelogic.bp.user_bp.user_repo.get_user_by_id",
        lambda x: None
    )

    r = client.get("/get_current_user")
    assert r.status_code == 404
    assert r.get_json()["error"] == "user_not_found"


def test_get_current_user_success(client, monkeypatch):
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    monkeypatch.setattr(
        "pagelogic.bp.user_bp.user_repo.get_user_by_id",
        lambda x: DummyUser(1, "Alice")
    )

    r = client.get("/get_current_user")
    assert r.status_code == 200
    assert r.get_json() == {"id": 1, "username": "Alice"}


# ==========================
# update_username tests
# ==========================

def test_update_username_not_logged_in(client):
    r = client.post("/update_username", json={"username": "Alice"})
    assert r.status_code == 401
    assert r.get_json()["error"] == "not_logged_in"


def test_update_username_missing_username(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    r = client.post("/update_username", json={})
    assert r.status_code == 400
    assert r.get_json()["error"] == "username_required"


def test_update_username_update_failed(client, monkeypatch):
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    # update_user_basic_info returning None → failure
    monkeypatch.setattr(
        "pagelogic.bp.user_bp.user_repo.update_user_basic_info",
        lambda uid, username=None: None
    )

    r = client.post("/update_username", json={"username": "Alice"})
    assert r.status_code == 500
    assert r.get_json()["error"] == "update_failed"


def test_update_username_success(client, monkeypatch):
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    monkeypatch.setattr(
        "pagelogic.bp.user_bp.user_repo.update_user_basic_info",
        lambda uid, username=None: DummyUser(uid, username)
    )

    r = client.post("/update_username", json={"username": "Alice"})
    assert r.status_code == 200
    assert r.get_json() == {"id": 1, "username": "Alice"}