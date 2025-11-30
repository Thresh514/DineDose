import pytest
from datetime import datetime
import pagelogic.repo.user_repo as repo


# =====================================================
# Fake DB
# =====================================================
class FakeCursor:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.last_query = None
        self.params = None
        self.rowcount = 0

        self.description = [
            ("id",), ("username",), ("email",), ("google_id",),
            ("avatar_url",), ("role",), ("is_verified",), ("created_at",)
        ]

    def execute(self, query, params=None):
        self.last_query = query
        self.params = params

        # ---- 模拟 “UPDATE ... RETURNING …” ----
        if query.strip().startswith("UPDATE") and "RETURNING" in query:

            # 如果没有 row，表示更新不到任何 user -> fetchone 会返回 None
            if not self.rows:
                self.rows = []
                self.rowcount = 0
                return

            # 取 UPDATE 语句中的新值
            new_username = None
            new_avatar = None

            if "username = %s" in query:
                new_username = params[0]

            if "avatar_url = %s" in query:
                if new_username is None:
                    new_avatar = params[0]
                else:
                    new_avatar = params[1]

            # 原 row
            orig = list(self.rows[0])

            # 修改字段
            if new_username is not None:
                orig[1] = new_username     # username
            if new_avatar is not None:
                orig[4] = new_avatar       # avatar_url

            # UPDATE return result only 1 row
            self.rows = [tuple(orig)]
            self.rowcount = 1

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
        1,                 # id
        "alice",           # username
        "a@example.com",   # email
        "g123",            # google_id
        "http://img",      # avatar_url
        "patient",         # role
        True,              # is_verified
        datetime(2025, 1, 1, 12, 0, 0),
    )


# =====================================================
# _row_to_user
# =====================================================
def test_row_to_user(sample_row):
    cur = FakeCursor(rows=[sample_row])
    u = repo._row_to_user(cur, sample_row)

    assert u.id == 1
    assert u.username == "alice"
    assert u.email == "a@example.com"
    assert u.role == "patient"


# =====================================================
# get_user_by_id
# =====================================================
def test_get_user_by_id_found(monkeypatch, sample_row):
    cur = FakeCursor(rows=[sample_row])
    conn = FakeConn(cur)

    monkeypatch.setattr(repo, "mydb", lambda: conn)

    u = repo.get_user_by_id(1)
    assert u is not None
    assert u.id == 1


def test_get_user_by_id_not_found(monkeypatch):
    cur = FakeCursor(rows=[])
    conn = FakeConn(cur)

    monkeypatch.setattr(repo, "mydb", lambda: conn)

    u = repo.get_user_by_id(999)
    assert u is None


# =====================================================
# get_all_users
# =====================================================
def test_get_all_users(monkeypatch, sample_row):
    cur = FakeCursor(rows=[sample_row, sample_row])
    conn = FakeConn(cur)

    monkeypatch.setattr(repo, "mydb", lambda: conn)

    users = repo.get_all_users()
    assert len(users) == 2
    assert users[0].id == 1


# =====================================================
# get_user_by_email
# =====================================================
def test_get_user_by_email_found(monkeypatch, sample_row):
    cur = FakeCursor(rows=[sample_row])
    conn = FakeConn(cur)

    monkeypatch.setattr(repo, "mydb", lambda: conn)

    u = repo.get_user_by_email("a@example.com")
    assert u is not None
    assert u.email == "a@example.com"


def test_get_user_by_email_not_found(monkeypatch):
    cur = FakeCursor(rows=[])
    conn = FakeConn(cur)

    monkeypatch.setattr(repo, "mydb", lambda: conn)

    u = repo.get_user_by_email("none")
    assert u is None


# =====================================================
# get_user_by_google_id
# =====================================================
def test_get_user_by_google_id_found(monkeypatch, sample_row):
    cur = FakeCursor(rows=[sample_row])
    conn = FakeConn(cur)

    monkeypatch.setattr(repo, "mydb", lambda: conn)

    u = repo.get_user_by_google_id("g123")
    assert u.google_id == "g123"


def test_get_user_by_google_id_not_found(monkeypatch):
    cur = FakeCursor(rows=[])
    conn = FakeConn(cur)

    monkeypatch.setattr(repo, "mydb", lambda: conn)

    u = repo.get_user_by_google_id("none")
    assert u is None


# =====================================================
# create_user
# =====================================================
def test_create_user(monkeypatch, sample_row):
    cur = FakeCursor(rows=[sample_row])
    conn = FakeConn(cur)

    monkeypatch.setattr(repo, "mydb", lambda: conn)

    u = repo.create_user(
        username="alice",
        email="a@example.com",
        google_id="g123",
        avatar_url="img",
        role="patient",
        is_verified=True,
    )

    assert u.id == 1
    assert conn.committed is True
    assert cur.params[1] == "a@example.com"


# =====================================================
# update_user_basic_info
# =====================================================
def test_update_user_basic_info_update_both(monkeypatch, sample_row):
    cur = FakeCursor(rows=[sample_row])
    conn = FakeConn(cur)

    monkeypatch.setattr(repo, "mydb", lambda: conn)

    u = repo.update_user_basic_info(
        1,
        username="newname",
        avatar_url="new.png"
    )

    assert u.username == "newname"
    assert conn.committed is True


def test_update_user_basic_info_update_one(monkeypatch, sample_row):
    cur = FakeCursor(rows=[sample_row])
    conn = FakeConn(cur)
    monkeypatch.setattr(repo, "mydb", lambda: conn)

    u = repo.update_user_basic_info(
        1,
        username="newname"
    )

    assert u.username == "newname"


def test_update_user_basic_info_no_fields(monkeypatch, sample_row):
    # should call get_user_by_id internally
    cur1 = FakeCursor(rows=[sample_row])
    conn1 = FakeConn(cur1)

    monkeypatch.setattr(repo, "mydb", lambda: conn1)

    u = repo.update_user_basic_info(1)
    assert u.id == 1


def test_update_user_basic_info_not_found(monkeypatch):
    cur = FakeCursor(rows=[])
    conn = FakeConn(cur)
    monkeypatch.setattr(repo, "mydb", lambda: conn)

    u = repo.update_user_basic_info(
        1,
        username="abc"
    )

    assert u is None


# =====================================================
# get_doctor_by_patient_id
# =====================================================
def test_get_doctor_by_patient_id_found(monkeypatch, sample_row):
    cur = FakeCursor(rows=[sample_row])
    conn = FakeConn(cur)
    monkeypatch.setattr(repo, "mydb", lambda: conn)

    doc = repo.get_doctor_by_patient_id(10)
    assert doc.id == 1


def test_get_doctor_by_patient_id_not_found(monkeypatch):
    cur = FakeCursor(rows=[])
    conn = FakeConn(cur)
    monkeypatch.setattr(repo, "mydb", lambda: conn)

    doc = repo.get_doctor_by_patient_id(10)
    assert doc is None


# =====================================================
# get_patients_by_doctor_id
# =====================================================
def test_get_patients_by_doctor_id(monkeypatch, sample_row):
    cur = FakeCursor(rows=[sample_row, sample_row])
    conn = FakeConn(cur)
    monkeypatch.setattr(repo, "mydb", lambda: conn)

    pts = repo.get_patients_by_doctor_id(1)
    assert len(pts) == 2


# =====================================================
# get_users_by_ids
# =====================================================
def test_get_users_by_ids(monkeypatch, sample_row):
    cur = FakeCursor(rows=[sample_row])
    conn = FakeConn(cur)
    monkeypatch.setattr(repo, "mydb", lambda: conn)

    res = repo.get_users_by_ids([1])
    assert len(res) == 1


def test_get_users_by_ids_empty():
    assert repo.get_users_by_ids([]) == []
