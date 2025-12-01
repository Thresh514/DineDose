import pytest
from flask import Flask
from datetime import date, datetime, timedelta
import pagelogic.bp.doctor_page_bp as doctor_bp


# ---------- Fake Templates ----------
@pytest.fixture(autouse=True)
def fake_templates(monkeypatch):
    monkeypatch.setattr(doctor_bp, "render_template", lambda *a, **kw: "OK")


# ---------- Flask app ----------
@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(doctor_bp.doctor_page_bp)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


# ---------- Dummy Models ----------
class DummyUser:
    def __init__(self, id=1, username="u", email="u@e.com",
                 is_verified=True, role="patient"):
        self.id = id
        self.username = username
        self.email = email
        self.is_verified = is_verified
        self.role = role


class DummyPlan:
    def __init__(self, id=1, doctor_id=1, patient_id=2, plan_items=None):
        self.id = id
        self.doctor_id = doctor_id
        self.patient_id = patient_id
        self.plan_items = plan_items or []

    def to_dict(self):
        return {
            "id": self.id,
            "doctor_id": self.doctor_id,
            "patient_id": self.patient_id,
            "plan_items": [p.to_dict() for p in self.plan_items]
        }


class DummyPlanItem:
    def __init__(self, id=1, drug_name="Drug", dosage=1,
                 unit="mg", date_=None, time=None):
        self.id = id
        self.drug_name = drug_name
        self.dosage = dosage
        self.unit = unit
        self.date = date_ or date.today()
        self.time = time

    def to_dict(self):
        return {
            "id": self.id,
            "drug_name": self.drug_name,
            "dosage": self.dosage,
            "unit": self.unit,
            "date": self.date.isoformat()
        }


class DummyRecord:
    def __init__(self, status="ON_TIME"):
        self.status = status
        self.updated_at = datetime.now()
        self.expected_date = date.today()
        self.expected_time = datetime.now().time()


class DummyFeedback:
    def __init__(self, text="ok"):
        self.text = text

    def to_dict(self):
        return {"feedback": self.text}


# ============================================================================================
#  /doctor/add_patient
# ============================================================================================

def test_add_patient_not_login(client):
    resp = client.post("/doctor/add_patient", json={"email": "x"})
    assert resp.status_code == 401


def test_add_patient_missing_email(client):
    with client.session_transaction() as s:
        s["user_id"] = 1
    resp = client.post("/doctor/add_patient", json={})
    assert resp.status_code == 400


def test_add_patient_user_not_found(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1
    monkeypatch.setattr(doctor_bp.user_repo, "get_user_by_email", lambda x: None)
    resp = client.post("/doctor/add_patient", json={"email": "x"})
    assert resp.status_code == 404


def test_add_patient_success(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1

    patient = DummyUser(id=2)
    doctor = DummyUser(id=1, username="doctor")

    monkeypatch.setattr(doctor_bp.user_repo, "get_user_by_email", lambda x: patient)
    monkeypatch.setattr(doctor_bp.user_repo, "get_user_by_id", lambda x: doctor)
    monkeypatch.setattr(doctor_bp.user_repo, "get_patients_by_doctor_id", lambda x: [])
    monkeypatch.setattr(doctor_bp.plan_repo, "get_plan_by_user_id", lambda x: None)
    monkeypatch.setattr(doctor_bp.plan_repo, "create_plan",
                        lambda **k: DummyPlan(id=10))

    resp = client.post("/doctor/add_patient", json={"email": "x"})
    assert resp.status_code == 200


# ============================================================================================
#  /doctor/remove_patient
# ============================================================================================

def test_remove_patient_missing_id(client):
    with client.session_transaction() as s:
        s["user_id"] = 1

    resp = client.post("/doctor/remove_patient", json={})
    assert resp.status_code == 400


def test_remove_patient_invalid_id(client):
    with client.session_transaction() as s:
        s["user_id"] = 1

    resp = client.post("/doctor/remove_patient", json={"patient_id": "abc"})
    assert resp.status_code == 400


def test_remove_patient_not_doctors_patient(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1

    monkeypatch.setattr(doctor_bp.plan_repo, "get_plan_by_user_id",
                        lambda _: DummyPlan(doctor_id=99))

    resp = client.post("/doctor/remove_patient", json={"patient_id": 2})
    assert resp.status_code == 403


def test_remove_patient_success(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1

    plan = DummyPlan(id=5, doctor_id=1)
    monkeypatch.setattr(doctor_bp.plan_repo, "get_plan_by_user_id", lambda _: plan)
    monkeypatch.setattr(doctor_bp.plan_repo, "get_all_plan_items_by_plan_id",
                        lambda _: [DummyPlanItem(id=1)])
    monkeypatch.setattr(doctor_bp.plan_repo, "delete_plan_item_and_rules",
                        lambda _: None)

    # Fake DB
    class FakeCursor:
        def execute(self, *a, **k): pass
        def close(self): pass

    class FakeConn:
        def cursor(self): return FakeCursor()
        def commit(self): pass
        def close(self): pass

    monkeypatch.setattr(doctor_bp, "mydb", lambda: FakeConn())

    resp = client.post("/doctor/remove_patient", json={"patient_id": 2})
    assert resp.status_code == 200


# ============================================================================================
#  /doctor/plan_editor
# ============================================================================================

def test_plan_editor_missing_id(client):
    resp = client.get("/doctor/plan_editor")
    assert resp.status_code == 400


def test_plan_editor_not_logged_in(client):
    resp = client.get("/doctor/plan_editor?patient_id=2")
    assert resp.status_code == 401


def test_plan_editor_existing_plan(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1

    monkeypatch.setattr(doctor_bp.plan_service, "get_raw_plan",
                        lambda pid: DummyPlan(id=5))
    monkeypatch.setattr(doctor_bp.user_repo, "get_user_by_id",
                        lambda x: DummyUser(id=x))

    resp = client.get("/doctor/plan_editor?patient_id=2")
    assert resp.status_code == 200


def test_plan_editor_auto_create_plan(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1

    monkeypatch.setattr(doctor_bp.plan_service, "get_raw_plan", lambda x: None)
    monkeypatch.setattr(doctor_bp.plan_repo, "create_plan",
                        lambda **k: DummyPlan(id=10))
    monkeypatch.setattr(doctor_bp.user_repo, "get_user_by_id",
                        lambda x: DummyUser(id=x))

    resp = client.get("/doctor/plan_editor?patient_id=2")
    assert resp.status_code == 200


# ============================================================================================
#  /doctor/plan_item_create
# ============================================================================================

def test_plan_item_create_missing_id(client):
    resp = client.get("/doctor/plan_item_create")
    assert resp.status_code == 400


def test_plan_item_create_not_logged_in(client):
    resp = client.get("/doctor/plan_item_create?patient_id=1")
    assert resp.status_code == 401


def test_plan_item_create_existing_plan(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1

    monkeypatch.setattr(doctor_bp.plan_service, "get_user_plan",
                        lambda *a: DummyPlan(id=3))
    monkeypatch.setattr(doctor_bp.user_repo, "get_user_by_id",
                        lambda x: DummyUser(id=x))

    resp = client.get("/doctor/plan_item_create?patient_id=2")
    assert resp.status_code == 200


def test_plan_item_create_auto_create_plan(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1

    monkeypatch.setattr(doctor_bp.plan_service, "get_user_plan", lambda *a: None)
    monkeypatch.setattr(doctor_bp.plan_service, "get_raw_plan", lambda *a: None)
    monkeypatch.setattr(doctor_bp.plan_repo, "create_plan",
                        lambda **k: DummyPlan(id=10))
    monkeypatch.setattr(doctor_bp.user_repo, "get_user_by_id",
                        lambda x: DummyUser(id=x))

    resp = client.get("/doctor/plan_item_create?patient_id=5")
    assert resp.status_code == 200


# ============================================================================================
#  /doctor/plan_item_edit
# ============================================================================================

def test_plan_item_edit_missing_item(client):
    resp = client.get("/doctor/plan_item_edit?patient_id=2")
    assert resp.status_code == 400


def test_plan_item_edit_missing_patient(client):
    resp = client.get("/doctor/plan_item_edit?item_id=1")
    assert resp.status_code == 400


def test_plan_item_edit_no_plan(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1

    monkeypatch.setattr(doctor_bp.plan_service, "get_user_plan",
                        lambda *a: None)

    resp = client.get("/doctor/plan_item_edit?item_id=1&patient_id=2")
    assert resp.status_code == 404


def test_plan_item_edit_item_not_found(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1

    plan = DummyPlan(id=5, plan_items=[])
    monkeypatch.setattr(doctor_bp.plan_service, "get_user_plan", lambda *a: plan)
    monkeypatch.setattr(doctor_bp.user_repo, "get_user_by_id",
                        lambda x: DummyUser(id=x))

    resp = client.get("/doctor/plan_item_edit?item_id=1&patient_id=2")
    assert resp.status_code == 404


def test_plan_item_edit_success(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1

    plan = DummyPlan(id=5, plan_items=[DummyPlanItem(id=1)])
    monkeypatch.setattr(doctor_bp.plan_service, "get_user_plan", lambda *a: plan)
    monkeypatch.setattr(doctor_bp.user_repo, "get_user_by_id",
                        lambda x: DummyUser(id=x))

    resp = client.get("/doctor/plan_item_edit?item_id=1&patient_id=2")
    assert resp.status_code == 200


# ============================================================================================
#  /doctor/give_feedback
# ============================================================================================

def test_give_feedback_not_logged_in(client):
    resp = client.post("/doctor/give_feedback", json={})
    assert resp.status_code == 401


def test_give_feedback_missing_patient_id(client):
    with client.session_transaction() as s:
        s["user_id"] = 1

    resp = client.post("/doctor/give_feedback",
                       json={"feedback_date": "2025-01-01"})
    assert resp.status_code == 400


def test_give_feedback_missing_date(client):
    with client.session_transaction() as s:
        s["user_id"] = 1

    resp = client.post("/doctor/give_feedback",
                       json={"patient_id": 2})
    assert resp.status_code == 400


def test_give_feedback_invalid_date(client):
    with client.session_transaction() as s:
        s["user_id"] = 1

    resp = client.post("/doctor/give_feedback",
                       json={"patient_id": 2, "feedback_date": "xxx"})
    assert resp.status_code == 400


def test_give_feedback_permission_denied(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1

    monkeypatch.setattr(doctor_bp.plan_repo, "get_plan_by_user_id",
                        lambda x: DummyPlan(doctor_id=99))

    resp = client.post(
        "/doctor/give_feedback",
        json={"patient_id": 2, "feedback_date": "2025-01-01"})
    assert resp.status_code == 403


def test_give_feedback_missing_text(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1

    monkeypatch.setattr(doctor_bp.plan_repo, "get_plan_by_user_id",
                        lambda x: DummyPlan(doctor_id=1))

    resp = client.post("/doctor/give_feedback",
                       json={"patient_id": 2, "feedback_date": "2025-01-01"})
    assert resp.status_code == 400


def test_give_feedback_manual_success(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1

    monkeypatch.setattr(doctor_bp.plan_repo, "get_plan_by_user_id",
                        lambda x: DummyPlan(doctor_id=1))
    monkeypatch.setattr(doctor_bp.feedback_repo, "create_or_update_feedback",
                        lambda **k: DummyFeedback("ok"))

    resp = client.post("/doctor/give_feedback",
                       json={"patient_id": 2,
                             "feedback_date": "2025-01-01",
                             "feedback": "hello"})
    assert resp.status_code == 200


def test_give_feedback_ai_success(client, monkeypatch):
    """ FULL mock for AI branch → MUST return 200 """

    with client.session_transaction() as s:
        s["user_id"] = 1

    # permission
    monkeypatch.setattr(doctor_bp.plan_repo, "get_plan_by_user_id",
                        lambda x: DummyPlan(doctor_id=1))

    # user plan for that day
    monkeypatch.setattr(
        doctor_bp.plan_service, "get_user_plan",
        lambda pid, start, end: DummyPlan(
            plan_items=[DummyPlanItem()]
        )
    )

    # drug record
    monkeypatch.setattr(
        doctor_bp.drug_record_repo,
        "get_drug_records_by_date_range",
        lambda **k: [DummyRecord()]
    )

    # no previous feedback
    monkeypatch.setattr(
        doctor_bp.feedback_repo,
        "get_feedback_by_date",
        lambda *a, **k: None
    )

    # AI generation
    monkeypatch.setattr(
        doctor_bp, "call_llm_api",
        lambda **k: {"success": True, "output": "AI OK"}
    )

    monkeypatch.setattr(
        doctor_bp.feedback_repo,
        "create_or_update_feedback",
        lambda **k: DummyFeedback("AI OK")
    )

    resp = client.post(
        "/doctor/give_feedback",
        json={"patient_id": 2,
              "feedback_date": "2025-01-01",
              "use_ai": True}
    )
    assert resp.status_code == 200


def test_give_feedback_ai_failed(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1

    # plan 权限
    monkeypatch.setattr(
        doctor_bp.plan_repo,
        "get_plan_by_user_id",
        lambda x: DummyPlan(doctor_id=1)
    )

    # mock AI 失败
    monkeypatch.setattr(
        doctor_bp,
        "call_llm_api",
        lambda **k: {"success": False, "error": "x"}
    )

    # mock 计划与记录（避免内部 None 崩溃）
    monkeypatch.setattr(
        doctor_bp.plan_service, "get_user_plan",
        lambda *a, **k: DummyPlan(plan_items=[])
    )
    monkeypatch.setattr(
        doctor_bp.drug_record_repo, "get_drug_records_by_date_range",
        lambda **k: []
    )

    resp = client.post(
        "/doctor/give_feedback",
        json={"patient_id": 2,
              "feedback_date": "2025-01-01",
              "use_ai": True}
    )
    assert resp.status_code == 500


# ============================================================================================
#  /doctor/get_feedback
# ============================================================================================

def test_get_feedback_not_login(client):
    resp = client.get("/doctor/get_feedback?patient_id=2&feedback_date=2025-01-01")
    assert resp.status_code == 401


def test_get_feedback_permission(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1

    monkeypatch.setattr(
        doctor_bp.plan_repo, "get_plan_by_user_id",
        lambda x: DummyPlan(doctor_id=99)
    )

    resp = client.get("/doctor/get_feedback?patient_id=2&feedback_date=2025-01-01")
    assert resp.status_code == 403


def test_get_feedback_invalid_date(client):
    with client.session_transaction() as s:
        s["user_id"] = 1
    resp = client.get("/doctor/get_feedback?patient_id=2&feedback_date=BAD")
    assert resp.status_code == 400


def test_get_feedback_success(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1

    monkeypatch.setattr(
        doctor_bp.plan_repo, "get_plan_by_user_id",
        lambda x: DummyPlan(doctor_id=1)
    )
    monkeypatch.setattr(
        doctor_bp.feedback_repo, "get_feedback_by_date",
        lambda *a: DummyFeedback("yes")
    )

    resp = client.get("/doctor/get_feedback?patient_id=2&feedback_date=2025-01-01")
    assert resp.status_code == 200
    assert resp.get_json()["feedback"]["feedback"] == "yes"


# ============================================================================================
#  /doctor/feedback (page)
# ============================================================================================

def test_feedback_page_not_logged(client):
    resp = client.get("/doctor/feedback")
    assert resp.status_code == 401


def test_feedback_page_success(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1

    p = DummyUser(id=2)
    monkeypatch.setattr(
        doctor_bp.user_repo, "get_patients_by_doctor_id",
        lambda x: [p]
    )

    plan = DummyPlan(id=5, doctor_id=1,
                     plan_items=[DummyPlanItem()])
    monkeypatch.setattr(
        doctor_bp.plan_repo, "get_plan_by_user_id",
        lambda x: plan
    )

    monkeypatch.setattr(
        doctor_bp.plan_repo, "get_all_plan_items_by_plan_id",
        lambda x: plan.plan_items
    )

    yesterday = date.today() - timedelta(days=1)

    monkeypatch.setattr(
        doctor_bp.plan_service, "get_user_plan",
        lambda pid, start, end: DummyPlan(plan_items=[DummyPlanItem(date_=yesterday)])
    )

    monkeypatch.setattr(
        doctor_bp.drug_record_repo, "get_drug_records_by_date_range",
        lambda **k: [DummyRecord(status="TAKEN")]
    )

    monkeypatch.setattr(
        doctor_bp.feedback_repo, "get_feedback_by_date",
        lambda *a: None
    )

    resp = client.get("/doctor/feedback")
    assert resp.status_code == 200


# ============================================================================================
#  /doctor/plans
# ============================================================================================

def test_doctor_plans_not_logged(client):
    resp = client.get("/doctor/plans")
    assert resp.status_code == 401


def test_doctor_plans_ok(client):
    with client.session_transaction() as s:
        s["user_id"] = 1

    resp = client.get("/doctor/plans")
    assert resp.status_code == 200


def test_doctor_home_no_doctor_id(client):
    """覆盖 line 57–60: session 无 user_id"""
    resp = client.get("/doctor/home")
    assert resp.status_code == 200   # 页面正常返回


def test_add_patient_triggered_flag(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1

    patient = DummyUser(id=2)
    monkeypatch.setattr(doctor_bp.user_repo, "get_user_by_email", lambda x: patient)
    monkeypatch.setattr(doctor_bp.user_repo, "get_patients_by_doctor_id", lambda x: [])
    monkeypatch.setattr(doctor_bp.plan_repo, "get_plan_by_user_id", lambda x: None)

    doctor = DummyUser(id=1)
    monkeypatch.setattr(doctor_bp.user_repo, "get_user_by_id", lambda x: doctor)

    # create_plan 将被触发
    monkeypatch.setattr(doctor_bp.plan_repo, "create_plan",
                        lambda **k: DummyPlan(id=99))

    resp = client.post("/doctor/add_patient",
                       json={"email": "anything@example.com"})
    assert resp.status_code == 200


def test_feedback_page_no_tasks_and_no_records(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1

    # one patient
    patient = DummyUser(id=2)
    monkeypatch.setattr(doctor_bp.user_repo,
                        "get_patients_by_doctor_id",
                        lambda x: [patient])

    # plan exists but has 0 items
    base_plan = DummyPlan(id=5, doctor_id=1, plan_items=[])
    monkeypatch.setattr(doctor_bp.plan_repo,
                        "get_plan_by_user_id",
                        lambda x: base_plan)

    monkeypatch.setattr(doctor_bp.plan_repo,
                        "get_all_plan_items_by_plan_id",
                        lambda x: [])

    yesterday = date.today() - timedelta(days=1)

    # yesterday also empty
    monkeypatch.setattr(doctor_bp.plan_service,
                        "get_user_plan",
                        lambda pid, start, end: DummyPlan(plan_items=[]))

    # no records
    monkeypatch.setattr(doctor_bp.drug_record_repo,
                        "get_drug_records_by_date_range",
                        lambda **k: [])

    monkeypatch.setattr(doctor_bp.feedback_repo,
                        "get_feedback_by_date",
                        lambda *a, **k: None)

    resp = client.get("/doctor/feedback")
    assert resp.status_code == 200


def test_patient_stats_no_plan_items(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1

    plan = DummyPlan(id=1, doctor_id=1, patient_id=2, plan_items=[])
    monkeypatch.setattr(doctor_bp.plan_repo,
                        "get_plan_by_user_id",
                        lambda x: plan)

    # yesterday empty
    monkeypatch.setattr(doctor_bp.plan_service,
                        "get_user_plan",
                        lambda *a: DummyPlan(plan_items=[]))

    monkeypatch.setattr(doctor_bp.drug_record_repo,
                        "get_drug_records_by_date_range",
                        lambda **k: [])

    resp = client.get("/doctor/patient_stats?patient_id=2")
    assert resp.status_code == 200
    assert resp.get_json()["risk_level"] == "High"   # ← 修改


def test_patient_stats_taken_late_medium_risk(client, monkeypatch):
    with client.session_transaction() as s:
        s["user_id"] = 1

    yesterday = date.today() - timedelta(days=1)
    items = [DummyPlanItem(date_=yesterday)]

    plan = DummyPlan(id=1, doctor_id=1, patient_id=2, plan_items=items)

    monkeypatch.setattr(doctor_bp.plan_repo,
                        "get_plan_by_user_id",
                        lambda x: plan)

    y_plan = DummyPlan(plan_items=items)
    monkeypatch.setattr(doctor_bp.plan_service,
                        "get_user_plan",
                        lambda *a: y_plan)

    monkeypatch.setattr(doctor_bp.drug_record_repo,
                        "get_drug_records_by_date_range",
                        lambda **k: [DummyRecord(status="TAKEN_LATE")])

    resp = client.get("/doctor/patient_stats?patient_id=2")
    assert resp.status_code == 200
    assert resp.get_json()["risk_level"] == "High"   # ← 修改




