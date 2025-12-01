import pytest
from datetime import date, time as dt_time
import pagelogic.repo.plan_repo as plan_repo


# ===============================================
# Fake DB layer
# ===============================================
class FakeCursor:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.index = -1
        self.last_query = None
        self.params = None
        self.rowcount = 0
        # default columns for plan table
        self.description = [
            ("id",),
            ("patient_id",),
            ("doctor_id",),
            ("name",),
            ("description",),
            ("doctor_name",),
            ("patient_name",),
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
        self.cursor_obj = cursor
        self.committed = False
        self.rolled_back = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass


# ===============================================
# Fixtures
# ===============================================
@pytest.fixture
def sample_plan_row():
    return (
        1,       # id
        10,      # patient_id
        99,      # doctor_id
        "PlanA", # name
        "desc",  # description
        "DrX",   # doctor_name
        "Alice"  # patient_name
    )


@pytest.fixture
def fake_conn(sample_plan_row):
    cursor = FakeCursor(rows=[sample_plan_row])
    return FakeConn(cursor)


# ===============================================
# Tests for helper: _row_to_dict
# ===============================================
def test__row_to_dict(sample_plan_row):
    cursor = FakeCursor(rows=[sample_plan_row])
    d = plan_repo._row_to_dict(cursor, sample_plan_row)
    assert d["id"] == 1
    assert d["patient_id"] == 10


# ===============================================
# get_plan_by_user_id
# ===============================================
def test_get_plan_by_user_id_found(monkeypatch, fake_conn):
    monkeypatch.setattr(plan_repo, "mydb", lambda: fake_conn)

    p = plan_repo.get_plan_by_user_id(10)
    assert p is not None
    assert p.id == 1
    assert p.patient_id == 10
    assert fake_conn.cursor_obj.params == (10,)


def test_get_plan_by_user_id_not_found(monkeypatch):
    cursor = FakeCursor(rows=[])
    conn = FakeConn(cursor)
    monkeypatch.setattr(plan_repo, "mydb", lambda: conn)

    p = plan_repo.get_plan_by_user_id(10)
    assert p is None


# ===============================================
# get_plan_by_id
# ===============================================
def test_get_plan_by_id_found(monkeypatch, fake_conn):
    monkeypatch.setattr(plan_repo, "mydb", lambda: fake_conn)
    p = plan_repo.get_plan_by_id(1)
    assert p.id == 1
    assert fake_conn.cursor_obj.params == (1,)


def test_get_plan_by_id_not_found(monkeypatch):
    cursor = FakeCursor(rows=[])
    conn = FakeConn(cursor)
    monkeypatch.setattr(plan_repo, "mydb", lambda: conn)
    p = plan_repo.get_plan_by_id(100)
    assert p is None


# ===============================================
# get_plans_by_user_ids
# ===============================================
def test_get_plans_by_user_ids_found(monkeypatch, sample_plan_row):
    cursor = FakeCursor(rows=[sample_plan_row])
    conn = FakeConn(cursor)
    monkeypatch.setattr(plan_repo, "mydb", lambda: conn)

    res = plan_repo.get_plans_by_user_ids([10])
    assert len(res) == 1
    assert res[10].id == 1


def test_get_plans_by_user_ids_empty_input():
    res = plan_repo.get_plans_by_user_ids([])
    assert res == []


# ===============================================
# get_all_plan_items
# ===============================================
def test_get_all_plan_items(monkeypatch):
    # row = id, plan_id, drug_id, dosage, unit, amount_literal, note
    row = (1, 100, 2000, 10, "mg", "literal", "note")
    cursor = FakeCursor(rows=[row])
    cursor.description = [
        ("id",), ("plan_id",), ("drug_id",),
        ("dosage",), ("unit",), ("amount_literal",), ("note",)
    ]
    conn = FakeConn(cursor)
    monkeypatch.setattr(plan_repo, "mydb", lambda: conn)

    items = plan_repo.get_all_plan_items()
    assert len(items) == 1
    assert items[0].id == 1
    assert items[0].dosage == 10


# ===============================================
# get_all_plan_items_by_plan_id
# ===============================================
def test_get_all_plan_items_by_plan_id(monkeypatch):
    row = (1, 100, 2000, 10, "mg", None, None)
    cursor = FakeCursor(rows=[row])
    cursor.description = [
        ("id",), ("plan_id",), ("drug_id",),
        ("dosage",), ("unit",), ("amount_literal",), ("note",)
    ]
    conn = FakeConn(cursor)
    monkeypatch.setattr(plan_repo, "mydb", lambda: conn)

    items = plan_repo.get_all_plan_items_by_plan_id(100)
    assert len(items) == 1
    assert items[0].plan_id == 100


# ===============================================
# get_plan_item_rules_by_plan_id
# ===============================================
def test_get_plan_item_rules_by_plan_id_no_rule(monkeypatch):
    # plan_item_id exists, rule_id=None (LEFT JOIN)
    row = (1, None, None, None, None, None, None, None, None, None, None, None, None, None)
    cursor = FakeCursor(rows=[row])
    cursor.description = [
        ("plan_item_id",), ("rule_id",), ("rule_plan_item_id",),
        ("rule_start_date",), ("rule_end_date",), ("rule_repeat_type",),
        ("rule_interval_value",), ("rule_mon",), ("rule_tue",),
        ("rule_wed",), ("rule_thu",), ("rule_fri",), ("rule_sat",),
        ("rule_sun",), 
        ("rule_times",),
    ]
    conn = FakeConn(cursor)
    monkeypatch.setattr(plan_repo, "mydb", lambda: conn)

    res = plan_repo.get_plan_item_rules_by_plan_id(100)
    assert res[1] == []  # rule is empty list


def test_get_plan_item_rules_by_plan_id_with_rule(monkeypatch):
    # rule exists
    row = (
        1,       # plan_item_id
        10,      # rule_id
        1,       # rule_plan_item_id
        date(2025,1,1), None, "DAILY", 1,
        True, False, False, False, False, False, False,
        [dt_time(12,0)]
    )
    cursor = FakeCursor(rows=[row])
    cursor.description = [
        ("plan_item_id",), ("rule_id",), ("rule_plan_item_id",),
        ("rule_start_date",), ("rule_end_date",), ("rule_repeat_type",),
        ("rule_interval_value",), ("rule_mon",), ("rule_tue",),
        ("rule_wed",), ("rule_thu",), ("rule_fri",), ("rule_sat",),
        ("rule_sun",), ("rule_times",),
    ]
    conn = FakeConn(cursor)
    monkeypatch.setattr(plan_repo, "mydb", lambda: conn)

    res = plan_repo.get_plan_item_rules_by_plan_id(100)
    rule = res[1][0]
    assert rule.id == 10
    assert rule.times == [dt_time(12,0)]


# ===============================================
# create_plan_item_with_rules
# ===============================================
def test_create_plan_item_with_rules_success(monkeypatch):
    # first fetchone for plan_item_id
    row_item = (123,)
    cursor = FakeCursor(rows=[row_item])
    conn = FakeConn(cursor)

    monkeypatch.setattr(plan_repo, "mydb", lambda: conn)

    new_id = plan_repo.create_plan_item_with_rules(
        plan_id=1,
        drug_id=10,
        dosage=20,
        unit="mg",
        amount_literal=None,
        note=None,
        rules=[
            {
                "start_date": date(2025,1,1),
                "end_date": None,
                "repeat_type": "DAILY",
                "interval_value": 1,
                "mon": True, "tue": False, "wed": False, 
                "thu": False, "fri": False, "sat": False, "sun": False,
                "times": [dt_time(12,0)],
            }
        ]
    )

    assert new_id == 123
    assert conn.committed is True


def test_create_plan_item_with_rules_exception(monkeypatch):
    cursor = FakeCursor(rows=[(123,)])
    conn = FakeConn(cursor)

    def bad_execute(*args, **kwargs):
        raise Exception("DB error")

    monkeypatch.setattr(cursor, "execute", bad_execute)
    monkeypatch.setattr(plan_repo, "mydb", lambda: conn)

    with pytest.raises(Exception):
        plan_repo.create_plan_item_with_rules(
            1, 10, 20, "mg", None, None, []
        )

    assert conn.rolled_back is True


# ===============================================
# update_plan_item_with_rules
# ===============================================
def test_update_plan_item_with_rules_success(monkeypatch):
    cursor = FakeCursor(rows=[(1,)])
    cursor.rowcount = 1  # simulate update success
    conn = FakeConn(cursor)
    monkeypatch.setattr(plan_repo, "mydb", lambda: conn)

    ok = plan_repo.update_plan_item_with_rules(
        1, 1, 10, 20, "mg", None, None, []
    )
    assert ok is True
    assert conn.committed is True


def test_update_plan_item_with_rules_not_found(monkeypatch):
    cursor = FakeCursor(rows=[(1,)])
    cursor.rowcount = 0  # simulate update 0 rows
    conn = FakeConn(cursor)
    monkeypatch.setattr(plan_repo, "mydb", lambda: conn)

    ok = plan_repo.update_plan_item_with_rules(
        1, 1, 10, 20, "mg", None, None, []
    )
    assert ok is False
    assert conn.rolled_back is True


def test_update_plan_item_with_rules_exception(monkeypatch):
    cursor = FakeCursor()
    conn = FakeConn(cursor)

    def bad_execute(*args, **kwargs):
        raise Exception("DB err")

    monkeypatch.setattr(cursor, "execute", bad_execute)
    monkeypatch.setattr(plan_repo, "mydb", lambda: conn)

    with pytest.raises(Exception):
        plan_repo.update_plan_item_with_rules(
            1,1,10,20,"mg",None,None,[]
        )

    assert conn.rolled_back is True


# ===============================================
# delete_plan_item_and_rules
# ===============================================
def test_delete_plan_item_and_rules_success(monkeypatch):
    cursor = FakeCursor()
    cursor.rowcount = 1  # simulate delete success
    conn = FakeConn(cursor)
    monkeypatch.setattr(plan_repo, "mydb", lambda: conn)

    ok = plan_repo.delete_plan_item_and_rules(1)
    assert ok is True
    assert conn.committed is True


def test_delete_plan_item_and_rules_not_found(monkeypatch):
    cursor = FakeCursor()
    cursor.rowcount = 0
    conn = FakeConn(cursor)

    monkeypatch.setattr(plan_repo, "mydb", lambda: conn)

    ok = plan_repo.delete_plan_item_and_rules(1)
    assert ok is False


def test_delete_plan_item_and_rules_exception(monkeypatch):
    cursor = FakeCursor()
    conn = FakeConn(cursor)

    def bad_execute(*args, **kwargs):
        raise Exception("Bad DB")

    monkeypatch.setattr(cursor, "execute", bad_execute)
    monkeypatch.setattr(plan_repo, "mydb", lambda: conn)

    with pytest.raises(Exception):
        plan_repo.delete_plan_item_and_rules(1)

    assert conn.rolled_back is True

