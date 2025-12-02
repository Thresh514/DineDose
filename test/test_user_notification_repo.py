import pytest
from datetime import date
import pagelogic.repo.user_notification_repo as repo
from pagelogic.repo.user_notification_repo import NotificationConfig


# =====================================================
# Fake DB
# =====================================================
class FakeCursor:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.description = [
            ("user_id",),
            ("enabled",),
            ("email_enabled",),
            ("notify_minutes",),
            ("timezone",),
        ]
        self.last_query = None
        self.params = None
        self.rowcount = 0

    def execute(self, query, params=None):
        self.last_query = query
        self.params = params

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows

    def close(self):
        pass


class FakeConn:
    def __init__(self, cursor):
        self.c = cursor
        self.committed = False

    def cursor(self):
        return self.c

    def commit(self):
        self.committed = True

    def close(self):
        pass


# =====================================================
# Fixtures
# =====================================================
@pytest.fixture
def sample_row():
    return (
        10,               # user_id
        True,             # enabled
        True,             # email_enabled
        [30, 10, 0],      # notify_minutes
        "UTC"             # timezone
    )


# =====================================================
# _row_to_notification_config
# =====================================================
def test_row_to_notification_config(sample_row):
    cur = FakeCursor(rows=[sample_row])
    cfg = repo._row_to_notification_config(cur, sample_row)

    assert cfg.user_id == 10
    assert cfg.enabled is True
    assert cfg.notify_minutes == [30, 10, 0]
    assert cfg.timezone == "UTC"


# =====================================================
# _validate_notification_config
# =====================================================
def test_validate_ok():
    cfg = NotificationConfig(1, True, True, [10, 0, -10], "UTC")
    repo._validate_notification_config(cfg)   # no exception


def test_validate_non_list():
    cfg = NotificationConfig(1, True, True, 123, "UTC")
    with pytest.raises(ValueError):
        repo._validate_notification_config(cfg)


def test_validate_bad_type():
    cfg = NotificationConfig(1, True, True, [10, "wrong"], "UTC")
    with pytest.raises(ValueError):
        repo._validate_notification_config(cfg)


def test_validate_bad_range():
    cfg = NotificationConfig(1, True, True, [9999], "UTC")
    with pytest.raises(ValueError):
        repo._validate_notification_config(cfg)


def test_validate_no_timezone():
    cfg = NotificationConfig(1, True, True, [10], "")
    with pytest.raises(ValueError):
        repo._validate_notification_config(cfg)


# =====================================================
# default_notification_config
# =====================================================
def test_default_notification_config():
    cfg = repo.default_notification_config(5)

    assert cfg.user_id == 5
    assert cfg.enabled is True
    assert cfg.email_enabled is True
    assert cfg.timezone == "UTC"
    assert cfg.notify_minutes == [30, 10, 0, -10, -30]


# =====================================================
# get_notification_config
# =====================================================
def test_get_config_found(monkeypatch, sample_row):
    cur = FakeCursor(rows=[sample_row])
    conn = FakeConn(cur)

    monkeypatch.setattr(repo, "mydb", lambda: conn)

    cfg = repo.get_notification_config(10)
    assert cfg.user_id == 10


def test_get_config_not_found(monkeypatch):
    cur = FakeCursor(rows=[])
    conn = FakeConn(cur)

    monkeypatch.setattr(repo, "mydb", lambda: conn)

    cfg = repo.get_notification_config(999)
    assert cfg is None


# =====================================================
# get_notification_configs_by_user_ids
# =====================================================
def test_get_configs_by_ids(monkeypatch, sample_row):
    cur = FakeCursor(rows=[sample_row])
    conn = FakeConn(cur)

    monkeypatch.setattr(repo, "mydb", lambda: conn)
    monkeypatch.setattr(repo, "config", type("X", (), {"FLASK_ENV": "dev"}))

    res = repo.get_notification_configs_by_user_ids([10])
    assert 10 in res


def test_get_configs_by_ids_empty():
    assert repo.get_notification_configs_by_user_ids([]) == {}


# =====================================================
# create_notification_config
# =====================================================
def test_create_notification_config(monkeypatch):
    cfg = NotificationConfig(3, True, True, [10], "UTC")

    cur = FakeCursor()
    conn = FakeConn(cur)

    monkeypatch.setattr(repo, "mydb", lambda: conn)

    repo.create_notification_config(cfg)

    assert conn.committed is True
    assert cur.params == (3, True, True, [10], "UTC")


# =====================================================
# update_notification_config
# =====================================================
def test_update_notification_config(monkeypatch):
    cfg = NotificationConfig(2, False, False, [-10], "UTC")

    cur = FakeCursor()
    conn = FakeConn(cur)

    monkeypatch.setattr(repo, "mydb", lambda: conn)

    repo.update_notification_config(cfg)

    assert conn.committed is True
    assert cur.params[-1] == 2


# =====================================================
# upsert_notification_config
# =====================================================
def test_upsert_notification_config(monkeypatch):
    cfg = NotificationConfig(4, True, False, [0], "UTC")

    cur = FakeCursor()
    conn = FakeConn(cur)

    monkeypatch.setattr(repo, "mydb", lambda: conn)

    repo.upsert_notification_config(cfg)

    assert conn.committed is True
    assert cur.params[0] == 4


# =====================================================
# get_or_create_default_notification_config
# =====================================================
def test_get_or_create_existing(monkeypatch, sample_row):
    cur = FakeCursor(rows=[sample_row])
    conn = FakeConn(cur)

    monkeypatch.setattr(repo, "mydb", lambda: conn)

    cfg = repo.get_or_create_default_notification_config(10)
    assert cfg.user_id == 10


def test_get_or_create_create_default(monkeypatch):
    cur1 = FakeCursor(rows=[])
    conn1 = FakeConn(cur1)

    cur2 = FakeCursor()
    conn2 = FakeConn(cur2)

    calls = []
    def fake_mydb():
        calls.append(1)
        return conn1 if len(calls) == 1 else conn2

    monkeypatch.setattr(repo, "mydb", fake_mydb)

    cfg = repo.get_or_create_default_notification_config(99)

    assert cfg.user_id == 99
    assert conn2.committed is True
    assert cur2.params[0] == 99
