import pytest
from datetime import date, datetime, time as dt_time, timedelta

from pagelogic.repo import drug_record_repo
from pagelogic.repo.drug_record_repo import drug_record


# ============================
# Fake DB + Fake Cursor
# ============================
class FakeCursor:
    def __init__(self, description, rows, rowcount=1):
        self.description = description
        self.rows = rows
        self._idx = 0
        self.rowcount = rowcount

    def execute(self, *args, **kwargs):
        pass

    def fetchone(self):
        if not self.rows:
            return None
        if self._idx >= len(self.rows):
            return None
        r = self.rows[self._idx]
        self._idx += 1
        return r

    def fetchall(self):
        return self.rows

    def close(self): pass


class FakeConn:
    def __init__(self, cursor):
        self.cursor_obj = cursor

    def cursor(self):
        return self.cursor_obj

    def commit(self): pass

    def close(self): pass


# Helper: generate a sample row & description
def sample_row(id=1, user_id=10, drug_id=20, expected_time=dt_time(12, 0)):
    return (
        id,
        user_id,
        drug_id,
        date(2025, 1, 2),
        expected_time,
        100.5,
        "mg",
        99,
        "TAKEN",
        "note",
        datetime(2025, 1, 3, 10, 20, 30)
    )


sample_description = [
    ("id",),
    ("user_id",),
    ("drug_id",),
    ("expected_date",),
    ("expected_time",),
    ("dosage_numeric",),
    ("unit",),
    ("plan_item_id",),
    ("status",),
    ("notes",),
    ("updated_at",),
]


# ============================
# Tests
# ============================

def test_create_drug_record(monkeypatch):
    cursor = FakeCursor(sample_description, [(123,)])
    conn = FakeConn(cursor)

    monkeypatch.setattr(drug_record_repo, "mydb", lambda: conn)

    new_id = drug_record_repo.create_drug_record(
        user_id=5,
        drug_id=10,
        expected_date=date(2025, 1, 1),
        expected_time=None,
        dosage_numeric=50,
        unit="mg",
        plan_item_id=3,
        status="TAKEN",
        notes="ok"
    )

    assert new_id == 123


def test_get_drug_record_by_id_found(monkeypatch):
    cursor = FakeCursor(sample_description, [sample_row()])
    conn = FakeConn(cursor)
    monkeypatch.setattr(drug_record_repo, "mydb", lambda: conn)

    r = drug_record_repo.get_drug_record_by_id(1)
    assert isinstance(r, drug_record)
    assert r.user_id == 10
    assert r.status == "TAKEN"


def test_get_drug_record_by_id_not_found(monkeypatch):
    cursor = FakeCursor(sample_description, [])
    conn = FakeConn(cursor)
    monkeypatch.setattr(drug_record_repo, "mydb", lambda: conn)

    r = drug_record_repo.get_drug_record_by_id(1)
    assert r is None


def test_get_drug_records_by_user_id(monkeypatch):
    rows = [
        sample_row(id=1),
        sample_row(id=2),
    ]
    cursor = FakeCursor(sample_description, rows)
    conn = FakeConn(cursor)

    monkeypatch.setattr(drug_record_repo, "mydb", lambda: conn)

    records = drug_record_repo.get_drug_records_by_user_id(10)
    assert len(records) == 2
    assert records[0].id == 1
    assert records[1].id == 2


def test_get_drug_records_by_date_range(monkeypatch):
    rows = [sample_row()]
    cursor = FakeCursor(sample_description, rows)
    conn = FakeConn(cursor)

    monkeypatch.setattr(drug_record_repo, "mydb", lambda: conn)

    records = drug_record_repo.get_drug_records_by_date_range(
        10,
        date(2025, 1, 1),
        date(2025, 1, 5)
    )
    assert len(records) == 1
    assert isinstance(records[0], drug_record)


def test_delete_drug_record_success(monkeypatch):
    cursor = FakeCursor(sample_description, [], rowcount=1)
    conn = FakeConn(cursor)
    monkeypatch.setattr(drug_record_repo, "mydb", lambda: conn)

    ok = drug_record_repo.delete_drug_record(1)
    assert ok is True


def test_delete_drug_record_not_found(monkeypatch):
    cursor = FakeCursor(sample_description, [], rowcount=0)
    conn = FakeConn(cursor)
    monkeypatch.setattr(drug_record_repo, "mydb", lambda: conn)

    ok = drug_record_repo.delete_drug_record(1)
    assert ok is False


def test_update_drug_record_success(monkeypatch):
    cursor = FakeCursor(sample_description, [], rowcount=1)
    conn = FakeConn(cursor)
    monkeypatch.setattr(drug_record_repo, "mydb", lambda: conn)

    ok = drug_record_repo.update_drug_record(
        record_id=1,
        status="TAKEN",
        dosage_numeric=10.0,
        unit="mg",
        notes="done"
    )
    assert ok is True


def test_update_drug_record_not_found(monkeypatch):
    cursor = FakeCursor(sample_description, [], rowcount=0)
    conn = FakeConn(cursor)
    monkeypatch.setattr(drug_record_repo, "mydb", lambda: conn)

    ok = drug_record_repo.update_drug_record(
        1, "TAKEN", 10.0, "mg", "done"
    )
    assert ok is False


def test_get_drug_record_by_unique_key_found(monkeypatch):
    cursor = FakeCursor(sample_description, [sample_row()])
    conn = FakeConn(cursor)
    monkeypatch.setattr(drug_record_repo, "mydb", lambda: conn)

    result = drug_record_repo.get_drug_record_by_unique_key(
        1, 99, date(2025, 1, 2), dt_time(12, 0)
    )
    assert result is not None
    assert isinstance(result, drug_record)


def test_get_drug_record_by_unique_key_not_found(monkeypatch):
    cursor = FakeCursor(sample_description, [])
    conn = FakeConn(cursor)
    monkeypatch.setattr(drug_record_repo, "mydb", lambda: conn)

    result = drug_record_repo.get_drug_record_by_unique_key(
        1, 99, date(2025, 1, 2), None
    )
    assert result is None


def test_get_drug_record_by_unique_found(monkeypatch):
    cursor = FakeCursor(sample_description, [sample_row()])
    conn = FakeConn(cursor)
    monkeypatch.setattr(drug_record_repo, "mydb", lambda: conn)

    result = drug_record_repo.get_drug_record_by_unique(
        1, 99, date(2025, 1, 2), dt_time(12, 0)
    )
    assert result is not None


def test_get_drug_record_by_unique_not_found(monkeypatch):
    cursor = FakeCursor(sample_description, [])
    conn = FakeConn(cursor)
    monkeypatch.setattr(drug_record_repo, "mydb", lambda: conn)

    result = drug_record_repo.get_drug_record_by_unique(
        1, 99, date(2025, 1, 2), None
    )
    assert result is None


def test_get_recent_completed_drug_records(monkeypatch):
    rows = [
        sample_row(id=1),
        sample_row(id=2),
    ]
    cursor = FakeCursor(sample_description, rows)
    conn = FakeConn(cursor)
    monkeypatch.setattr(drug_record_repo, "mydb", lambda: conn)

    records = drug_record_repo.get_recent_completed_drug_records(7)
    assert len(records) == 2
    assert all(isinstance(r, drug_record) for r in records)
