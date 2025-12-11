import pytest
from datetime import date, time, datetime
from pagelogic.service.plan_service import (
    get_raw_plan,
    get_user_plan,
    fill_date_and_time
)

# --------------------------------
# Fake Model Classes
# --------------------------------

class FakePlan:
    def __init__(self, id):
        self.id = id
        self.plan_items = None


class FakePlanItem:
    def __init__(self, id, plan_id=1, drug_id=1, drug_name=None,
                 dosage=1, unit="mg", amount_literal=None, note=None):
        self.id = id
        self.plan_id = plan_id
        self.drug_id = drug_id
        self.drug_name = drug_name
        self.dosage = dosage
        self.unit = unit
        self.amount_literal = amount_literal
        self.note = note
        self.plan_item_rule = None


class FakeRule:
    def __init__(
        self,
        start_date,
        end_date=None,
        repeat_type="ONCE",
        interval_value=None,
        mon=False, tue=False, wed=False, thu=False,
        fri=False, sat=False, sun=False,
        times=None
    ):
        self.start_date = start_date
        self.end_date = end_date
        self.repeat_type = repeat_type
        self.interval_value = interval_value
        self.mon = mon
        self.tue = tue
        self.wed = wed
        self.thu = thu
        self.fri = fri
        self.sat = sat
        self.sun = sun
        self.times = times or []


class FakeDrug:
    def __init__(self, id, generic_name):
        self.id = id
        self.generic_name = generic_name


# Returned objects from plan_repo.plan_item must have .date / .time
class FakeGeneratedItem:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# --------------------------------
# Test get_raw_plan
# --------------------------------

def test_get_raw_plan_no_plan(monkeypatch):
    monkeypatch.setattr(
        "pagelogic.service.plan_service.plan_repo.get_plan_by_user_id",
        lambda x: None
    )

    assert get_raw_plan(99) is None


def test_get_raw_plan_success(monkeypatch):
    plan = FakePlan(id=10)

    items = [
        FakePlanItem(1, drug_id=111),
        FakePlanItem(2, drug_id=222)
    ]

    rules = {
        1: [FakeRule(start_date=date(2025, 1, 1))],
        2: []
    }

    drugs = [
        FakeDrug(111, "DrugA"),
        FakeDrug(222, "DrugB")
    ]

    monkeypatch.setattr(
        "pagelogic.service.plan_service.plan_repo.get_plan_by_user_id",
        lambda uid: plan
    )
    monkeypatch.setattr(
        "pagelogic.service.plan_service.plan_repo.get_all_plan_items_by_plan_id",
        lambda pid: items
    )
    monkeypatch.setattr(
        "pagelogic.service.plan_service.plan_repo.get_plan_item_rules_by_plan_id",
        lambda pid: rules
    )
    monkeypatch.setattr(
        "pagelogic.service.plan_service.drug_repo.get_drugs_by_ids_locally",
        lambda ids: drugs
    )

    result = get_raw_plan(5)

    assert len(result.plan_items) == 2
    assert result.plan_items[0].drug_name == "DrugA"
    assert result.plan_items[1].drug_name == "DrugB"
    assert result.plan_items[0].plan_item_rule.start_date == date(2025, 1, 1)
    assert result.plan_items[1].plan_item_rule is None


# --------------------------------
# Test get_user_plan
# --------------------------------

def test_get_user_plan_success(monkeypatch):
    plan = FakePlan(id=10)

    items = [
        FakePlanItem(1, drug_id=111),
        FakePlanItem(2, drug_id=222)
    ]

    rules = {
        1: [FakeRule(start_date=date(2025, 1, 1))],
        2: [FakeRule(start_date=date(2025, 1, 2))]
    }

    drugs = [
        FakeDrug(111, "DrugA"),
        FakeDrug(222, "DrugB")
    ]

    monkeypatch.setattr(
        "pagelogic.service.plan_service.plan_repo.get_plan_by_user_id",
        lambda uid: plan
    )
    monkeypatch.setattr(
        "pagelogic.service.plan_service.plan_repo.get_all_plan_items_by_plan_id",
        lambda pid: items
    )
    monkeypatch.setattr(
        "pagelogic.service.plan_service.plan_repo.get_plan_item_rules_by_plan_id",
        lambda pid: rules
    )
    monkeypatch.setattr(
        "pagelogic.service.plan_service.drug_repo.get_drugs_by_ids_locally",
        lambda ids: drugs
    )
    monkeypatch.setattr(
        "pagelogic.service.plan_service.fill_date_and_time",
        lambda items, rules_map, fw, tw: [
            FakePlanItem(1, drug_id=111, drug_name="DrugA"),
            FakePlanItem(2, drug_id=222, drug_name="DrugB"),
        ]
    )

    result = get_user_plan(
        id=5,
        from_when=date(2025, 1, 1),
        to_when=date(2025, 2, 1)
    )

    assert len(result.plan_items) == 2
    assert result.plan_items[0].drug_name == "DrugA"
    assert result.plan_items[1].drug_name == "DrugB"


# --------------------------------
# fill_date_and_time Tests
# --------------------------------

def test_fill_date_and_time_no_rules():
    item = FakePlanItem(1)
    result = fill_date_and_time([item], {}, date(2025, 1, 1), date(2025, 1, 31))
    assert result == []


def test_fill_single_rule_object(monkeypatch):
    item = FakePlanItem(1)

    class SingleRule:
        repeat_type = "ONCE"
        start_date = date(2025, 1, 5)
        end_date = None
        times = [time(8, 0)]

    rules = {1: SingleRule()}

    monkeypatch.setattr(
        "pagelogic.service.plan_service.plan_repo.plan_item",
        lambda **kw: FakeGeneratedItem(**kw)
    )

    result = fill_date_and_time(
        [item], rules, date(2025, 1, 1), date(2025, 1, 31)
    )

    assert len(result) == 1
    assert result[0].date == date(2025, 1, 5)


def test_fill_date_range_none(monkeypatch):
    item = FakePlanItem(1)
    rule = FakeRule(start_date=date(2025, 1, 10), times=[time(9)])

    monkeypatch.setattr(
        "pagelogic.service.plan_service.plan_repo.plan_item",
        lambda **kw: FakeGeneratedItem(**kw)
    )

    result = fill_date_and_time([item], {1: [rule]}, None, None)

    assert len(result) == 1


def test_fill_times_string_format(monkeypatch):
    item = FakePlanItem(1)
    rule = FakeRule(start_date=date(2025, 1, 1), times=["08:30"])

    monkeypatch.setattr(
        "pagelogic.service.plan_service.plan_repo.plan_item",
        lambda **kw: FakeGeneratedItem(**kw)
    )

    result = fill_date_and_time([item], {1: [rule]}, date(2025, 1, 1), date(2025, 1, 2))

    assert result[0].time == "08:30"


def test_fill_times_string_invalid(monkeypatch):
    item = FakePlanItem(1)
    rule = FakeRule(start_date=date(2025, 1, 1), times=["not-a-time"])

    monkeypatch.setattr(
        "pagelogic.service.plan_service.plan_repo.plan_item",
        lambda **kw: FakeGeneratedItem(**kw)
    )

    result = fill_date_and_time([item], {1: [rule]}, date(2025, 1, 1), date(2025, 1, 2))

    assert result[0].time == "not-a-time"


def test_fill_rule_outside_range():
    item = FakePlanItem(1)
    rule = FakeRule(start_date=date(2030, 1, 1))

    result = fill_date_and_time(
        [item], {1: [rule]}, date(2025, 1, 1), date(2025, 12, 31)
    )

    assert result == []


def test_fill_weekly_no_flags(monkeypatch):
    item = FakePlanItem(1)
    rule = FakeRule(start_date=date(2025, 1, 1), repeat_type="WEEKLY", times=[time(8)])

    monkeypatch.setattr(
        "pagelogic.service.plan_service.plan_repo.plan_item",
        lambda **kw: FakeGeneratedItem(**kw)
    )

    result = fill_date_and_time(
        [item], {1: [rule]}, date(2025, 1, 1), date(2025, 1, 7)
    )

    assert result == []


def test_fill_daily_default_interval(monkeypatch):
    item = FakePlanItem(1)
    rule = FakeRule(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 3),
        repeat_type="DAILY",
        times=[time(7)]
    )

    monkeypatch.setattr(
        "pagelogic.service.plan_service.plan_repo.plan_item",
        lambda **kw: FakeGeneratedItem(**kw)
    )

    result = fill_date_and_time(
        [item], {1: [rule]}, date(2025, 1, 1), date(2025, 1, 31)
    )

    assert len(result) == 3


def test_get_user_plan_full_flow(monkeypatch):
    plan = FakePlan(id=10)
    items = [FakePlanItem(1, drug_id=111)]
    rules = {1: [FakeRule(start_date=date(2025, 1, 1), times=[time(9)])]}
    drugs = [FakeDrug(111, "AAA")]

    monkeypatch.setattr(
        "pagelogic.service.plan_service.plan_repo.get_plan_by_user_id",
        lambda uid: plan
    )
    monkeypatch.setattr(
        "pagelogic.service.plan_service.plan_repo.get_all_plan_items_by_plan_id",
        lambda pid: items
    )
    monkeypatch.setattr(
        "pagelogic.service.plan_service.plan_repo.get_plan_item_rules_by_plan_id",
        lambda pid: rules
    )
    monkeypatch.setattr(
        "pagelogic.service.plan_service.drug_repo.get_drugs_by_ids_locally",
        lambda ids: drugs
    )
    monkeypatch.setattr(
        "pagelogic.service.plan_service.plan_repo.plan_item",
        lambda **kw: FakeGeneratedItem(**kw)
    )

    result = get_user_plan(1, date(2025, 1, 1), date(2025, 1, 2))

    assert len(result.plan_items) == 1
    assert result.plan_items[0].drug_name == "AAA"