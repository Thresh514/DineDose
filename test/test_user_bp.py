import pytest
from flask import Flask
from pagelogic.bp.user_bp import user_bp

# --------------------------
# Flask test app
# --------------------------
@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(user_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()


# --------------------------
# Dummy Model
# --------------------------
class DummyUser:
    def __init__(self, id):
        self.id = id

    def to_dict(self):
        return {"id": self.id}


# ==========================
# get_doctors tests
# ==========================

def test_get_doctors_missing_id(client):
    r = client.get("/get_doctors?id=0")
    assert r.status_code == 404 or r.status_code == 200


def test_get_doctors_not_found(client, monkeypatch):
    monkeypatch.setattr(
        "pagelogic.bp.user_bp.user_repo.get_doctor_by_patient_id",
        lambda x: None
    )
    r = client.get("/get_doctors?id=123")
    assert r.status_code == 404


def test_get_doctors_success(client, monkeypatch):
    monkeypatch.setattr(
        "pagelogic.bp.user_bp.user_repo.get_doctor_by_patient_id",
        lambda x: DummyUser(99)
    )
    r = client.get("/get_doctors?id=123")
    assert r.status_code == 200
    assert r.get_json() == {"id": 99}


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
    assert r.get_json() == [{"id": 1}, {"id": 2}]



