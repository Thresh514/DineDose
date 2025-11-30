import pytest
from datetime import date, time, datetime
import pagelogic.repo.food_record_repo as food_record_repo


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

        # 模拟 PostgreSQL 的 cursor.description
        self.description = [
            ("id",), ("user_id",), ("food_id",),
            ("eaten_date",), ("eaten_time",),
            ("amount_numeric",), ("unit",),
            ("amount_literal",), ("source",),
            ("plan_item_id",), ("notes",),
            ("created_at",), ("status",)
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
        10,              # user_id
        200,             # food_id
        date(2025, 1, 1),# eaten_date
        time(12, 30),    # eaten_time
        150.0,           # amount_numeric
        "g",             # unit
        "150g rice",     # amount_literal
        "manual",        # source
        None,            # plan_item_id
        "good",          # notes
        datetime(2025, 1, 1, 12, 0, 0),  # created_at
        "TAKEN"          # status
    )


# --------------------------
# CREATE
# --------------------------
def test_create_food_record(monkeypatch, sample_row):
    fake_cursor = FakeCursor(rows=[(5,)])   # returning id=5
    fake_conn = FakeConn(fake_cursor)

    monkeypatch.setattr(food_record_repo, "mydb", lambda: fake_conn)

    new_id = food_record_repo.create_food_record(
        user_id=10,
        food_id=200,
        eaten_date=date(2025, 1, 1),
        eaten_time=None,
        amount_numeric=100.0,
        unit="g",
        amount_literal="100g",
        source="manual",
        plan_item_id=None,
        notes="ok",
        status="TAKEN"
    )

    assert new_id == 5
    assert fake_conn.committed is True


# --------------------------
# GET BY ID
# --------------------------
def test_get_food_record_by_id_found(monkeypatch, sample_row):
    fake_cursor = FakeCursor(rows=[sample_row])
    fake_conn = FakeConn(fake_cursor)
    monkeypatch.setattr(food_record_repo, "mydb", lambda: fake_conn)

    record = food_record_repo.get_food_record_by_id(1)
    assert record is not None
    assert record.id == 1
    assert record.amount_literal == "150g rice"


def test_get_food_record_by_id_not_found(monkeypatch):
    fake_cursor = FakeCursor(rows=[])
    fake_conn = FakeConn(fake_cursor)
    monkeypatch.setattr(food_record_repo, "mydb", lambda: fake_conn)

    record = food_record_repo.get_food_record_by_id(99)
    assert record is None


# --------------------------
# GET BY USER
# --------------------------
def test_get_food_records_by_user_id(monkeypatch, sample_row):
    rows = [sample_row, sample_row]
    fake_cursor = FakeCursor(rows=rows)
    fake_conn = FakeConn(fake_cursor)
    monkeypatch.setattr(food_record_repo, "mydb", lambda: fake_conn)

    records = food_record_repo.get_food_records_by_user_id(10)
    assert len(records) == 2
    assert records[0].food_id == 200


# --------------------------
# GET DATE RANGE
# --------------------------
def test_get_food_records_by_date_range(monkeypatch, sample_row):
    rows = [sample_row]
    fake_cursor = FakeCursor(rows=rows)
    fake_conn = FakeConn(fake_cursor)
    monkeypatch.setattr(food_record_repo, "mydb", lambda: fake_conn)

    records = food_record_repo.get_food_records_by_date_range(
        10,
        date(2025, 1, 1),
        date(2025, 1, 10),
    )
    assert len(records) == 1
    assert records[0].status == "TAKEN"


# --------------------------
# DELETE
# --------------------------
def test_delete_food_record_success(monkeypatch):
    fake_cursor = FakeCursor()
    fake_cursor.rowcount = 1
    fake_conn = FakeConn(fake_cursor)
    monkeypatch.setattr(food_record_repo, "mydb", lambda: fake_conn)

    ok = food_record_repo.delete_food_record(1)
    assert ok is True
    assert fake_conn.committed is True


def test_delete_food_record_not_found(monkeypatch):
    fake_cursor = FakeCursor()
    fake_cursor.rowcount = 0
    fake_conn = FakeConn(fake_cursor)
    monkeypatch.setattr(food_record_repo, "mydb", lambda: fake_conn)

    ok = food_record_repo.delete_food_record(1)
    assert ok is False


# --------------------------
# UPDATE
# --------------------------
def test_update_food_record_success(monkeypatch):
    fake_cursor = FakeCursor()
    fake_cursor.rowcount = 1
    fake_conn = FakeConn(fake_cursor)
    monkeypatch.setattr(food_record_repo, "mydb", lambda: fake_conn)

    ok = food_record_repo.update_food_record(
        record_id=1,
        amount_numeric=100.0,
        unit="g",
        amount_literal="100g",
        notes="updated",
        status="TAKEN"
    )
    assert ok is True
    assert fake_conn.committed is True


def test_update_food_record_not_found(monkeypatch):
    fake_cursor = FakeCursor()
    fake_cursor.rowcount = 0
    fake_conn = FakeConn(fake_cursor)
    monkeypatch.setattr(food_record_repo, "mydb", lambda: fake_conn)

    ok = food_record_repo.update_food_record(
        record_id=999,
        amount_numeric=None,
        unit=None,
        amount_literal=None,
        notes=None,
        status="TAKEN"
    )
    assert ok is False


# --------------------------
# internal helper
# --------------------------
def test_row_to_food_record(sample_row):
    fake_cursor = FakeCursor()
    record = food_record_repo._row_to_food_record(fake_cursor, sample_row)

    assert record.id == 1
    assert record.user_id == 10
    assert record.food_id == 200
    assert record.amount_literal == "150g rice"
    assert record.status == "TAKEN"
