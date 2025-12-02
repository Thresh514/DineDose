import pytest
from datetime import datetime as real_datetime, date, time as dt_time, timedelta

import pagelogic.service.notify_service as svc


# =========================
# Fixtures
# =========================

@pytest.fixture
def scheduled_dose():
    return svc.ScheduledDose(
        user_id=1,
        plan_item_id=10,
        expected_date=date(2025, 1, 1),
        expected_time=dt_time(9, 0),
        drug_name="Aspirin",
        dosage=100,
        unit="mg",
    )


@pytest.fixture
def completed_record():
    class Rec:
        pass
    r = Rec()
    r.user_id = 1
    r.plan_item_id = 10
    r.expected_date = date(2025, 1, 1)
    r.expected_time = dt_time(9, 0)
    return r


# =========================
# find_missed_doses
# =========================

def test_find_missed_doses_all_missed(scheduled_dose):
    missed = svc.find_missed_doses(
        scheduled=[scheduled_dose],
        recent_records=[],
    )
    assert len(missed) == 1
    assert missed[0].plan_item_id == 10


def test_find_missed_doses_none_missed(scheduled_dose, completed_record):
    missed = svc.find_missed_doses(
        scheduled=[scheduled_dose],
        recent_records=[completed_record],
    )
    assert missed == []


# =========================
# build_email_body
# =========================

def test_build_email_body_with_time(scheduled_dose):
    body = svc.build_email_body(scheduled_dose, "Alice")
    assert "Aspirin" in body
    assert "Alice" in body
    assert "Dosage: 100 mg" in body
    assert "2025-01-01" in body


def test_build_email_body_default_time():
    dose = svc.ScheduledDose(
        user_id=2,
        plan_item_id=20,
        expected_date=date(2025, 1, 2),
        expected_time=None,
        drug_name=None,
        dosage=None,
        unit=None,
    )
    body = svc.build_email_body(dose, "")
    assert "Your medication" in body
    assert "2025-01-02" in body


# =========================
# send_notifications
# =========================

def test_send_notifications_no_missed():
    svc.send_notifications([], interval=60)


def test_send_notifications_config_missing(monkeypatch, scheduled_dose):
    monkeypatch.setattr(
        svc.user_repo,
        "get_users_by_ids",
        lambda ids: [],
    )
    monkeypatch.setattr(
        svc.user_notification_repo,
        "get_notification_configs_by_user_ids",
        lambda ids: {},
    )

    called = {"send": False}

    def fake_send(email, subject, body):
        called["send"] = True

    monkeypatch.setattr(svc, "send_email_ses", fake_send)

    svc.send_notifications([scheduled_dose], interval=60)
    assert called["send"] is False


def test_send_notifications_disabled(monkeypatch, scheduled_dose):
    class FakeUser:
        def __init__(self, uid):
            self.id = uid
            self.email = "a@test.com"
            self.username = "Alice"

    monkeypatch.setattr(
        svc.user_repo,
        "get_users_by_ids",
        lambda ids: [FakeUser(1)],
    )

    class FakeCfg:
        def __init__(self):
            self.enabled = False
            self.email_enabled = True
            self.notify_minutes = [0]

    monkeypatch.setattr(
        svc.user_notification_repo,
        "get_notification_configs_by_user_ids",
        lambda ids: {1: FakeCfg()},
    )

    called = {"send": False}

    def fake_send(email, subject, body):
        called["send"] = True

    monkeypatch.setattr(svc, "send_email_ses", fake_send)

    svc.send_notifications([scheduled_dose], interval=60)
    assert called["send"] is False


def test_send_notifications_no_offset_match(monkeypatch, scheduled_dose):
    class FakeUser:
        def __init__(self, uid):
            self.id = uid
            self.email = "a@test.com"
            self.username = "Alice"

    monkeypatch.setattr(
        svc.user_repo,
        "get_users_by_ids",
        lambda ids: [FakeUser(1)],
    )

    class FakeCfg:
        def __init__(self):
            self.enabled = True
            self.email_enabled = True
            self.notify_minutes = [300]

    monkeypatch.setattr(
        svc.user_notification_repo,
        "get_notification_configs_by_user_ids",
        lambda ids: {1: FakeCfg()},
    )

    fake_now = real_datetime(2025, 1, 1, 0, 0, 0)

    class FakeDateTime:
        @classmethod
        def now(cls, tz=None):
            return fake_now

        @classmethod
        def combine(cls, d, t):
            return real_datetime.combine(d, t)

    monkeypatch.setattr(svc, "datetime", FakeDateTime)

    called = {"send": False}

    def fake_send(email, subject, body):
        called["send"] = True

    monkeypatch.setattr(svc, "send_email_ses", fake_send)

    svc.send_notifications([scheduled_dose], interval=60)
    assert called["send"] is False


def test_send_notifications_send_once(monkeypatch, scheduled_dose):
    class FakeUser:
        def __init__(self, uid):
            self.id = uid
            self.email = "a@test.com"
            self.username = "Alice"

    monkeypatch.setattr(
        svc.user_repo,
        "get_users_by_ids",
        lambda ids: [FakeUser(1)],
    )

    class FakeCfg:
        def __init__(self):
            self.enabled = True
            self.email_enabled = True
            self.notify_minutes = [30]

    monkeypatch.setattr(
        svc.user_notification_repo,
        "get_notification_configs_by_user_ids",
        lambda ids: {1: FakeCfg()},
    )

    fake_now = real_datetime(2025, 1, 1, 9, 29, 40)

    class FakeDateTime:
        @classmethod
        def now(cls, tz=None):
            return fake_now

        @classmethod
        def combine(cls, d, t):
            return real_datetime.combine(d, t)

    monkeypatch.setattr(svc, "datetime", FakeDateTime)

    sent = {}

    def fake_send(email, subject, body):
        sent["email"] = email
        sent["subject"] = subject
        sent["body"] = body

    monkeypatch.setattr(svc, "send_email_ses", fake_send)

    svc.send_notifications([scheduled_dose], interval=60)

    assert sent["email"] == "a@test.com"
    assert "Aspirin" in sent["body"]
    assert "DineDose Medication Reminder" in sent["subject"]


# =========================
# notify_jobs
# =========================

def test_notify_jobs_happy_path(monkeypatch, scheduled_dose):
    monkeypatch.setattr(
        svc,
        "get_scheduled_doses_within",
        lambda days: [scheduled_dose],
    )

    monkeypatch.setattr(
        svc.drug_record_repo,
        "get_recent_completed_drug_records",
        lambda days: [],
    )

    monkeypatch.setattr(
        svc,
        "find_missed_doses",
        lambda scheduled, recent: [scheduled_dose],
    )

    called = {"missed": None, "interval": None}

    def fake_send_notifications(missed, interval):
        called["missed"] = missed
        called["interval"] = interval

    monkeypatch.setattr(
        svc,
        "send_notifications",
        fake_send_notifications,
    )

    svc.notify_jobs(days=3, interval=120)
    assert called["missed"] is not None
    assert called["interval"] == 120
    assert called["missed"][0].plan_item_id == 10


# =========================
# get_scheduled_doses_within
# =========================

def test_get_scheduled_doses_within_basic(monkeypatch):
    class FakeUser:
        def __init__(self, uid):
            self.id = uid

    monkeypatch.setattr(
        svc.user_repo,
        "get_all_users",
        lambda: [FakeUser(1)],
    )

    monkeypatch.setattr(
        svc.plan_repo,
        "get_plans_by_user_ids",
        lambda user_ids: {1: "dummy_plan"},
    )

    class FakePlanItem:
        def __init__(self):
            self.id = 10
            self.date = date(2025, 1, 1)
            self.time = dt_time(9, 0)
            self.drug_name = "Aspirin"
            self.dosage = 50
            self.unit = "mg"

    class FakePlan:
        def __init__(self):
            self.plan_items = [FakePlanItem()]

    def fake_get_user_plan(id, from_when, to_when):
        return FakePlan()

    monkeypatch.setattr(
        svc.plan_service,
        "get_user_plan",
        fake_get_user_plan,
    )

    doses = svc.get_scheduled_doses_within(days=1)
    assert len(doses) == 1
    d = doses[0]
    assert isinstance(d, svc.ScheduledDose)
    assert d.user_id == 1
    assert d.plan_item_id == 10
    assert d.drug_name == "Aspirin"


def test_get_scheduled_doses_within_no_plan(monkeypatch):
    class FakeUser:
        def __init__(self, uid):
            self.id = uid

    monkeypatch.setattr(
        svc.user_repo,
        "get_all_users",
        lambda: [FakeUser(1)],
    )

    monkeypatch.setattr(
        svc.plan_repo,
        "get_plans_by_user_ids",
        lambda user_ids: {},
    )

    monkeypatch.setattr(
        svc.plan_service,
        "get_user_plan",
        lambda id, from_when, to_when: None,
    )

    doses = svc.get_scheduled_doses_within(days=1)
    assert doses == []
