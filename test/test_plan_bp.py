import pytest
from datetime import date, time as dt_time
from flask import Flask
from pagelogic.bp.plan_bp import plan_bp
from pagelogic.bp import plan_bp as plan_module


# -------------------------
# Dummy Plan object
# -------------------------
class DummyPlan:
    def __init__(self, id=1):
        self.id = id

    def to_dict(self):
        return {"id": self.id}


# -------------------------
# Flask test client fixture
# -------------------------
@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(plan_bp)
    app.testing = True
    return app.test_client()


# ==========================================================
# 1. /get_user_plan
# ==========================================================

def test_get_user_plan_ok(client, monkeypatch):
    monkeypatch.setattr(plan_module.plan_service, "get_user_plan",
                        lambda *args: DummyPlan(5))

    r = client.get("/get_user_plan?id=2&from=2025-11-01&to=2025-12-01")
    assert r.status_code == 200
    assert r.get_json()["id"] == 5


def test_get_user_plan_no_dates(client, monkeypatch):
    monkeypatch.setattr(plan_module.plan_service, "get_user_plan",
                        lambda *args: DummyPlan(8))

    r = client.get("/get_user_plan?id=3")
    assert r.status_code == 200
    assert r.get_json()["id"] == 8


# ==========================================================
# 2. /get_raw_plan
# ==========================================================

def test_get_raw_plan_missing_id(client):
    r = client.get("/get_raw_plan")
    assert r.status_code == 400


def test_get_raw_plan_invalid_id(client):
    r = client.get("/get_raw_plan?id=abc")
    assert r.status_code == 400


def test_get_raw_plan_not_found(client, monkeypatch):
    monkeypatch.setattr(
        plan_module.plan_service,
        "get_raw_plan",
        lambda *args: None
    )
    r = client.get("/get_raw_plan?id=3")
    assert r.status_code == 404


def test_get_raw_plan_success(client, monkeypatch):
    monkeypatch.setattr(plan_module.plan_service,
                        "get_raw_plan",
                        lambda uid: DummyPlan(10))
    r = client.get("/get_raw_plan?id=3")
    assert r.status_code == 200
    assert r.get_json()["id"] == 10


# ==========================================================
# 3. POST /plan_item  (create)
# ==========================================================

def test_create_plan_item_no_ids(client):
    r = client.post("/plan_item", json={})
    assert r.status_code == 400


def test_create_plan_item_patient_id_but_no_plan(client, monkeypatch):
    monkeypatch.setattr(plan_module.plan_repo,
                        "get_plan_by_user_id",
                        lambda uid: None)
    r = client.post("/plan_item", json={"patient_id": 99})
    assert r.status_code == 404


def test_create_plan_item_missing_required_fields(client):
    r = client.post("/plan_item", json={"plan_id": 1})
    assert r.status_code == 400


def test_create_plan_item_invalid_ints(client):
    r = client.post("/plan_item", json={
        "plan_id": "xx",
        "drug_id": 1,
        "dosage": 2,
        "unit": "mg"
    })
    assert r.status_code == 400


def test_create_plan_item_invalid_start_date(client):
    payload = {
        "plan_id": 1,
        "drug_id": 2,
        "dosage": 10,
        "unit": "mg",
        "rules": [{"start_date": "abc"}]
    }
    r = client.post("/plan_item", json=payload)
    assert r.status_code == 400


def test_create_plan_item_invalid_end_date(client):
    payload = {
        "plan_id": 1,
        "drug_id": 2,
        "dosage": 10,
        "unit": "mg",
        "rules": [{
            "start_date": "2025-01-01",
            "end_date": "abc"
        }]
    }
    r = client.post("/plan_item", json=payload)
    assert r.status_code == 400


def test_create_plan_item_invalid_time(client):
    payload = {
        "plan_id": 1,
        "drug_id": 2,
        "dosage": 10,
        "unit": "mg",
        "rules": [{
            "start_date": "2025-01-01",
            "times": ["25:00:00"]
        }]
    }
    r = client.post("/plan_item", json=payload)
    assert r.status_code == 400


def test_create_plan_item_success(client, monkeypatch):
    monkeypatch.setattr(plan_module.plan_repo,
                        "create_plan_item_with_rules",
                        lambda **k: 123)

    r = client.post("/plan_item", json={
        "plan_id": 1,
        "drug_id": 10,
        "dosage": 20,
        "unit": "mg",
        "rules": [{
            "start_date": "2025-01-01",
            "times": ["12:00:00"]
        }]
    })
    assert r.status_code == 201
    assert r.get_json()["plan_item_id"] == 123


# ==========================================================
# 4. PUT /plan_item/<id>  (update)
# ==========================================================

def test_update_plan_item_missing_id(client):
    r = client.put("/plan_item/3", json={})
    assert r.status_code == 400


def test_update_plan_item_plan_not_found(client, monkeypatch):
    monkeypatch.setattr(plan_module.plan_repo,
                        "get_plan_by_user_id",
                        lambda uid: None)
    r = client.put("/plan_item/3", json={"patient_id": 99})
    assert r.status_code == 404


def test_update_plan_item_invalid_start_date(client):
    r = client.put("/plan_item/3", json={
        "plan_id": 1,
        "drug_id": 1,
        "dosage": 1,
        "unit": "mg",
        "rules": [{"start_date": "abc"}]
    })
    assert r.status_code == 400


def test_update_plan_item_invalid_time(client):
    r = client.put("/plan_item/3", json={
        "plan_id": 1,
        "drug_id": 2,
        "dosage": 5,
        "unit": "mg",
        "rules": [{
            "start_date": "2025-01-01",
            "times": ["25:00:00"]
        }]
    })
    assert r.status_code == 400


def test_update_plan_item_repo_not_found(client, monkeypatch):
    monkeypatch.setattr(plan_module.plan_repo,
                        "update_plan_item_with_rules",
                        lambda **kw: False)

    r = client.put("/plan_item/3", json={
        "plan_id": 1,
        "drug_id": 2,
        "dosage": 5,
        "unit": "mg",
        "rules": [{
            "start_date": "2025-01-01"
        }]
    })
    assert r.status_code == 404


def test_update_plan_item_success(client, monkeypatch):
    monkeypatch.setattr(plan_module.plan_repo,
                        "update_plan_item_with_rules",
                        lambda **kw: True)

    r = client.put("/plan_item/3", json={
        "plan_id": 1,
        "drug_id": 2,
        "dosage": 5,
        "unit": "mg",
        "rules": [{
            "start_date": "2025-01-01"
        }]
    })
    assert r.status_code == 200
    assert r.get_json()["message"] == "plan_item updated"


# ==========================================================
# 5. DELETE /plan_item/<id>
# ==========================================================

def test_delete_plan_item_fail(client, monkeypatch):
    monkeypatch.setattr(plan_module.plan_repo,
                        "delete_plan_item_and_rules",
                        lambda *a: False)
    r = client.delete("/plan_item/33")
    assert r.status_code == 404


def test_delete_plan_item_success(client, monkeypatch):
    monkeypatch.setattr(plan_module.plan_repo,
                        "delete_plan_item_and_rules",
                        lambda *a: True)
    r = client.delete("/plan_item/33")
    assert r.status_code == 200
    assert r.get_json()["message"] == "plan_item deleted"
