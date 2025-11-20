from dataclasses import dataclass, asdict
from typing import Optional, List
from datetime import date, time as dt_time, datetime
from config import mydb

@dataclass
class food_record:
    id: int
    user_id: int
    food_id: int
    eaten_date: date
    eaten_time: Optional[dt_time]
    amount_numeric: Optional[float]
    unit: Optional[str]
    amount_literal: Optional[str]
    source: str
    plan_item_id: Optional[int]
    notes: Optional[str]
    created_at: Optional[datetime]
    status: Optional[str]  # e.g., 'TAKEN', 'ON_TIME', 'LATE', 'SKIPPED'

    def to_dict(self):
        def serialize(obj):
            if isinstance(obj, (date, datetime)):
                return obj.isoformat()
            if isinstance(obj, dt_time):
                return obj.isoformat()
            return obj
        return {k: serialize(v) for k, v in asdict(self).items()}
    

# =============== Internal helper ===============
def _row_to_food_record(cur, row) -> food_record:
    columns = [desc[0] for desc in cur.description]
    rd = dict(zip(columns, row))

    return food_record(
        id=rd["id"],
        user_id=rd["user_id"],
        food_id=rd["food_id"],
        eaten_date=rd["eaten_date"],
        eaten_time=rd["eaten_time"],
        amount_numeric=rd["amount_numeric"],
        unit=rd["unit"],
        amount_literal=rd["amount_literal"],
        source=rd["source"],
        plan_item_id=rd["plan_item_id"],
        notes=rd["notes"],
        created_at=rd["created_at"],
        status=rd["status"],
    )

# ---- CREATE ----
def create_food_record(
    user_id: int,
    food_id: int,
    eaten_date: date,
    eaten_time: Optional[dt_time] = None,
    amount_numeric: Optional[float] = None,
    unit: Optional[str] = None,
    amount_literal: Optional[str] = None,
    source: str = "manual",
    plan_item_id: Optional[int] = None,
    notes: Optional[str] = None,
    status: Optional[str] = None,
) -> int:
    conn = mydb()
    cur = conn.cursor()

    query = """
    INSERT INTO food_records (
        user_id, food_id, eaten_date, eaten_time,
        amount_numeric, unit, amount_literal,
        source, plan_item_id, notes, status
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    RETURNING id;
    """

    cur.execute(
        query,
        (
            user_id, food_id, eaten_date, eaten_time,
            amount_numeric, unit, amount_literal,
            source, plan_item_id, notes, status
        )
    )

    record_id = cur.fetchone()[0]
    conn.commit()

    cur.close()
    conn.close()

    return record_id

# ---- READ ----
def get_food_record_by_id(record_id: int) -> Optional[food_record]:
    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT *
        FROM food_records
        WHERE id = %s
    """

    cur.execute(query, (record_id,))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return None

    record = _row_to_food_record(cur, row)

    cur.close()
    conn.close()
    return record



def get_food_records_by_user_id(user_id: int) -> List[food_record]:
    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT *
        FROM food_records
        WHERE user_id = %s
        ORDER BY eaten_date DESC, eaten_time DESC
    """

    cur.execute(query, (user_id,))
    rows = cur.fetchall()

    records = [_row_to_food_record(cur, row) for row in rows]

    cur.close()
    conn.close()
    return records

# ---- GET by DATE RANGE ----
def get_food_records_by_date_range(
    user_id: int,
    start: date,
    end: date,
) -> List[food_record]:
    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT *
        FROM food_records
        WHERE user_id = %s
        AND eaten_date BETWEEN %s AND %s
        ORDER BY eaten_date, eaten_time
    """

    cur.execute(query, (user_id, start, end))
    rows = cur.fetchall()

    records = [_row_to_food_record(cur, row) for row in rows]

    cur.close()
    conn.close()
    return records


# ---- DELETE ----
def delete_food_record(record_id: int) -> bool:
    conn = mydb()
    cur = conn.cursor()

    cur.execute("DELETE FROM food_records WHERE id = %s", (record_id,))
    deleted = cur.rowcount > 0

    conn.commit()
    cur.close()
    conn.close()

    return deleted

# ---- UPDATE (optional) ----
def update_food_record(
    record_id: int,
    amount_numeric: Optional[float],
    unit: Optional[str],
    amount_literal: Optional[str],
    notes: Optional[str],
    status: Optional[str],
) -> bool:
    conn = mydb()
    cur = conn.cursor()

    query = """
        UPDATE food_records
        SET amount_numeric = %s,
            unit = %s,
            amount_literal = %s,
            notes = %s,
            status = %s
        WHERE id = %s
    """

    cur.execute(
        query,
        (amount_numeric, unit, amount_literal, notes, status, record_id)
    )

    updated = cur.rowcount > 0
    conn.commit()

    cur.close()
    conn.close()
    return updated