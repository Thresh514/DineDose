import pytest
from datetime import date, time, datetime
from pagelogic.service.plan_service import fill_date_and_time


# ---------- Fake classes to avoid DB dependencies ----------
class FakePlanItem:
    def __init__(self, id, plan_id=1, drug_id=1, drug_name="TestDrug",
                 dosage=1, unit="mg", amount_literal=None, note=None):
        self.id = id
        self.plan_id = plan_id
        self.drug_id = drug_id
        self.drug_name = drug_name
        self.dosage = dosage
        self.unit = unit
        self.amount_literal = amount_literal
        self.note = note


class FakeRule:
    def __init__(
        self,
        start_date,
        end_date=None,
        repeat_type="ONCE",
        interval_value=None,
        mon=False, tue=False, wed=False, thu=False,
        fri=False, sat=False, sun=False,
        times=None,
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
        self.times = times


# ------------------------------------------------------------
# TEST CASE 1: ONCE
# ------------------------------------------------------------
def test_fill_once_rule():
    item = FakePlanItem(1)
    rule = FakeRule(
        start_date=date(2025, 1, 10),
        repeat_type="ONCE",
        times=[time(8, 0)]
    )

    result = fill_date_and_time(
        [item],
        {1: [rule]},
        date(2025, 1, 1),
        date(2025, 1, 31)
    )

    assert len(result) == 1
    assert result[0].date == date(2025, 1, 10)
    assert result[0].time == time(8, 0)


# ------------------------------------------------------------
# TEST CASE 2: ONCE (NO times)
# ------------------------------------------------------------
def test_fill_once_no_times():
    item = FakePlanItem(1)
    rule = FakeRule(
        start_date=date(2025, 1, 15),
        repeat_type="ONCE",
        times=None
    )

    result = fill_date_and_time(
        [item],
        {1: [rule]},
        date(2025, 1, 1),
        date(2025, 1, 30)
    )

    assert len(result) == 1
    assert result[0].date == date(2025, 1, 15)
    assert result[0].time is None


# ------------------------------------------------------------
# TEST CASE 3: DAILY WITH INTERVAL
# ------------------------------------------------------------
def test_fill_daily_interval():
    item = FakePlanItem(1)
    rule = FakeRule(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 5),
        repeat_type="DAILY",
        interval_value=2,
        times=[time(9, 0)]
    )

    result = fill_date_and_time(
        [item],
        {1: [rule]},
        date(2025, 1, 1),
        date(2025, 1, 31)
    )

    expected_dates = [
        date(2025, 1, 1),
        date(2025, 1, 3),
        date(2025, 1, 5),
    ]

    assert len(result) == len(expected_dates)
    for r, d in zip(result, expected_dates):
        assert r.date == d
        assert r.time == time(9, 0)


# ------------------------------------------------------------
# TEST CASE 4: DAILY NO TIMES
# ------------------------------------------------------------
def test_fill_daily_no_times():
    item = FakePlanItem(1)
    rule = FakeRule(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 3),
        repeat_type="DAILY",
        interval_value=1,
        times=None
    )

    result = fill_date_and_time(
        [item],
        {1: [rule]},
        date(2025, 1, 1),
        date(2025, 1, 31)
    )

    assert len(result) == 3
    for r in result:
        assert r.time is None


# ------------------------------------------------------------
# TEST CASE 5: WEEKLY
# ------------------------------------------------------------
def test_fill_weekly_rule():
    item = FakePlanItem(1)
    rule = FakeRule(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 14),
        repeat_type="WEEKLY",
        mon=True, wed=True, fri=True,
        times=[time(7, 0)]
    )

    result = fill_date_and_time(
        [item],
        {1: [rule]},
        date(2025, 1, 1),
        date(2025, 1, 31)
    )

    expected_dates = [
        date(2025, 1, 1),  # Wed
        date(2025, 1, 3),  # Fri
        date(2025, 1, 6),  # Mon
        date(2025, 1, 8),  # Wed
        date(2025, 1, 10), # Fri
        date(2025, 1, 13), # Mon
    ]

    assert len(result) == len(expected_dates)
    for r, d in zip(result, expected_dates):
        assert r.date == d
        assert r.time == time(7, 0)


# ------------------------------------------------------------
# TEST CASE 6: PRN
# ------------------------------------------------------------
def test_fill_prn_rule():
    item = FakePlanItem(1)
    rule = FakeRule(
        start_date=date(2025, 1, 1),
        repeat_type="PRN",
    )

    result = fill_date_and_time(
        [item],
        {1: [rule]},
        date(2025, 1, 1),
        date(2025, 1, 31)
    )

    assert len(result) == 1
    assert result[0].date is None
    assert result[0].time is None


# ------------------------------------------------------------
# TEST CASE 7: STRING DATE RANGE (covers fromisoformat branch)
# ------------------------------------------------------------
def test_fill_string_date_range():
    item = FakePlanItem(1)
    rule = FakeRule(
        start_date=date(2025, 1, 10),
        repeat_type="ONCE",
        times=[time(10, 0)]
    )

    result = fill_date_and_time(
        [item],
        {1: [rule]},
        "2025-01-01",     # string instead of date
        "2025-01-31"
    )

    assert len(result) == 1
    assert result[0].date == date(2025, 1, 10)


# ------------------------------------------------------------
# TEST CASE 8: DATE RANGE OUT OF BOUNDS (empty result)
# ------------------------------------------------------------
def test_fill_out_of_range():
    item = FakePlanItem(1)
    rule = FakeRule(
        start_date=date(2025, 5, 1),
        repeat_type="ONCE",
        times=[time(10, 0)]
    )

    result = fill_date_and_time(
        [item],
        {1: [rule]},
        date(2025, 1, 1),
        date(2025, 2, 1)
    )

    assert len(result) == 0

