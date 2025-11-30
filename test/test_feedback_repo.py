import pytest
from datetime import date, datetime
import pagelogic.repo.feedback_repo as feedback_repo


# --------------------------
# Fake DB Objects
# --------------------------
class FakeCursor:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.index = -1
        self.last_query = None
        self.params = None
        self.rowcount = 0
        # simulate pg description
        self.description = [
            ("id",), ("patient_id",), ("doctor_id",),
            ("feedback_date",), ("feedback",), ("created_at",)
        ]

    def execute(self, query, params=None):
        self.last_query = query
        self.params = params

    def fetchone(self):
        if not self.rows:
            return None
        return self.rows[0]

    def fetchall(self):
        return self.rows

    def close(self):
        pass


class FakeConn:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def close(self):
        pass


# --------------------------
# Fixtures
# --------------------------
@pytest.fixture
def sample_row():
    return (
        1,               # id
        10,              # patient_id
        99,              # doctor_id
        date(2025, 1, 1),# feedback_date
        "Good job",      # feedback
        datetime(2025, 1, 1, 12, 0, 0), # created_at
    )


# --------------------------
# Tests for CREATE/UPDATE
# --------------------------
def test_create_or_update_feedback(monkeypatch, sample_row):
    fake_cursor = FakeCursor(rows=[sample_row])
    fake_conn = FakeConn(fake_cursor)

    monkeypatch.setattr(feedback_repo, "mydb", lambda: fake_conn)

    result = feedback_repo.create_or_update_feedback(
        patient_id=10,
        doctor_id=99,
        feedback_date=date(2025, 1, 1),
        feedback="Good job"
    )

    assert result.id == 1
    assert result.patient_id == 10
    assert result.feedback == "Good job"
    assert fake_conn.committed is True


# --------------------------
# Tests: GET BY DATE
# --------------------------
def test_get_feedback_by_date_found(monkeypatch, sample_row):
    fake_cursor = FakeCursor(rows=[sample_row])
    fake_conn = FakeConn(fake_cursor)

    monkeypatch.setattr(feedback_repo, "mydb", lambda: fake_conn)

    fb = feedback_repo.get_feedback_by_date(10, date(2025, 1, 1))
    assert fb is not None
    assert fb.id == 1


def test_get_feedback_by_date_not_found(monkeypatch):
    fake_cursor = FakeCursor(rows=[])
    fake_conn = FakeConn(fake_cursor)
    monkeypatch.setattr(feedback_repo, "mydb", lambda: fake_conn)

    fb = feedback_repo.get_feedback_by_date(10, date(2025, 1, 1))
    assert fb is None


# --------------------------
# Tests: GET DATE RANGE
# --------------------------
def test_get_feedbacks_by_date_range(monkeypatch, sample_row):
    rows = [sample_row, sample_row]  # two rows
    fake_cursor = FakeCursor(rows=rows)
    fake_conn = FakeConn(fake_cursor)
    monkeypatch.setattr(feedback_repo, "mydb", lambda: fake_conn)

    res = feedback_repo.get_feedbacks_by_date_range(
        10,
        date(2025, 1, 1),
        date(2025, 1, 31)
    )
    assert len(res) == 2
    assert res[0].id == 1


# --------------------------
# Tests: DELETE
# --------------------------
def test_delete_feedback_success(monkeypatch):
    fake_cursor = FakeCursor()
    fake_cursor.rowcount = 1
    fake_conn = FakeConn(fake_cursor)
    monkeypatch.setattr(feedback_repo, "mydb", lambda: fake_conn)

    ok = feedback_repo.delete_feedback(10, date(2025, 1, 1))
    assert ok is True
    assert fake_conn.committed is True


def test_delete_feedback_not_found(monkeypatch):
    fake_cursor = FakeCursor()
    fake_cursor.rowcount = 0
    fake_conn = FakeConn(fake_cursor)
    monkeypatch.setattr(feedback_repo, "mydb", lambda: fake_conn)

    ok = feedback_repo.delete_feedback(10, date(2025, 1, 1))
    assert ok is False


# --------------------------
# Tests: _row_to_feedback
# --------------------------
def test_row_to_feedback_parsing(sample_row):
    fake_cursor = FakeCursor(rows=[sample_row])
    fb = feedback_repo._row_to_feedback(fake_cursor, sample_row)

    assert fb.id == 1
    assert fb.patient_id == 10
    assert fb.feedback == "Good job"

