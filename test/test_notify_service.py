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
    # 含有基本信息
    assert "Aspirin" in body
    assert "Alice" in body
    assert "Dosage: 100 mg" in body
    assert "2025-01-01" in body


def test_build_email_body_default_time():
    # expected_time 为 None，应该用早上 9 点
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
    # 默认药名 & 默认时间
    assert "Your medication" in body
    # 只要不报错即可，顺便检查日期格式存在
    assert "2025-01-02" in body


# =========================
# send_notifications
# =========================

def test_send_notifications_no_missed():
    # 不应抛错，直接返回
    svc.send_notifications([], interval=60)


def test_send_notifications_config_missing(monkeypatch, scheduled_dose):
    # user_notification_repo 返回空 dict → 不发送
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
    # config 存在但 enabled / email_enabled 为 False → 不发
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
    # offset 远离当前时间 → 本次 run 不触发
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
            self.notify_minutes = [300]  # 很远

    monkeypatch.setattr(
        svc.user_notification_repo,
        "get_notification_configs_by_user_ids",
        lambda ids: {1: FakeCfg()},
    )

    # 固定当前时间：远离 target_dt
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
    """
    设计时间：scheduled_dt + offset 刚好在 [0, interval) 秒内。
    """
    # user / config
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
            # offset = +30 分钟
            self.notify_minutes = [30]

    monkeypatch.setattr(
        svc.user_notification_repo,
        "get_notification_configs_by_user_ids",
        lambda ids: {1: FakeCfg()},
    )

    # 让 now 落在 target_dt - 30 秒
    # scheduled_dt = 2025-01-01 09:00, offset +30 分钟 -> target_dt = 09:30
    # now = 09:29:40, interval=60 -> diff=20 秒满足 [0,60)
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
    """
    完整路径：notify_jobs -> get_scheduled_doses_within -> get_recent_completed_drug_records
      -> find_missed_doses -> send_notifications
    我们把里面的调用都 mock 掉，只检查调用顺序。
    """
    # Step1
    monkeypatch.setattr(
        svc,
        "get_scheduled_doses_within",
        lambda days: [scheduled_dose],
    )

    # Step2
    monkeypatch.setattr(
        svc.drug_record_repo,
        "get_recent_completed_drug_records",
        lambda days: [],
    )

    # Step3
    monkeypatch.setattr(
        svc,
        "find_missed_doses",
        lambda scheduled, recent: [scheduled_dose],
    )

    # Step4
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
    """
    测试有一个 user，有一个 plan，有一个 plan_item，
    最终生成一个 ScheduledDose。
    """

    # 1) mock user_repo.get_all_users
    class FakeUser:
        def __init__(self, uid):
            self.id = uid

    monkeypatch.setattr(
        svc.user_repo,
        "get_all_users",
        lambda: [FakeUser(1)],
    )

    # 2) mock plan_repo.get_plans_by_user_ids
    monkeypatch.setattr(
        svc.plan_repo,
        "get_plans_by_user_ids",
        lambda user_ids: {1: "dummy_plan"},
    )

    # 3) mock plan_service.get_user_plan
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
        # 简单返回一个有 1 个 item 的 plan
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
    """
    测试：user 有，但 plan_repo 返回 {}，或 plan_service 返回 None → 无结果
    """

    class FakeUser:
        def __init__(self, uid):
            self.id = uid

    # 有一个 user
    monkeypatch.setattr(
        svc.user_repo,
        "get_all_users",
        lambda: [FakeUser(1)],
    )

    # 没有任何 plan
    monkeypatch.setattr(
        svc.plan_repo,
        "get_plans_by_user_ids",
        lambda user_ids: {},
    )

    # 即使被调用也返回 None（保险一点）
    monkeypatch.setattr(
        svc.plan_service,
        "get_user_plan",
        lambda id, from_when, to_when: None,
    )

    doses = svc.get_scheduled_doses_within(days=1)
    assert doses == []
