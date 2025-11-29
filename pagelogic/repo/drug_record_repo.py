from dataclasses import dataclass, asdict
from typing import Optional, List
from datetime import date, datetime, time as dt_time
from config import mydb

# ===================== dataclass model =====================

@dataclass
class drug_record:
    id: int
    user_id: int
    drug_id: int

    expected_date: date
    expected_time: Optional[dt_time]

    dosage_numeric: Optional[float]
    unit: Optional[str]

    plan_item_id: Optional[int]

    status: str             # e.g., 'TAKEN', 'ON_TIME', 'LATE', 'SKIPPED'
    notes: Optional[str]

    updated_at: Optional[datetime]

    def to_dict(self):
        """Serialize to JSON-friendly dict"""
        def serialize(obj):
            if isinstance(obj, (date, datetime)):
                return obj.isoformat()
            if isinstance(obj, dt_time):
                return obj.isoformat()
            return obj
        return {k: serialize(v) for k, v in asdict(self).items()}

# ===================== internal helper =====================

def _row_to_drug_record(cur, row) -> drug_record:
    columns = [desc[0] for desc in cur.description]
    rd = dict(zip(columns, row))

    return drug_record(
        id=rd["id"],
        user_id=rd["user_id"],
        drug_id=rd["drug_id"],

        expected_date=rd["expected_date"],
        expected_time=rd["expected_time"],

        dosage_numeric=rd["dosage_numeric"],
        unit=rd["unit"],

        plan_item_id=rd["plan_item_id"],

        status=rd["status"],          # e.g., 'TAKEN', 'ON_TIME', 'LATE', 'SKIPPED'
        notes=rd["notes"],

        updated_at=rd["updated_at"]
    )


# ===================== CRUD =====================

# ---------- CREATE ----------
def create_drug_record(
    user_id: int,
    drug_id: int,
    expected_date: date,
    expected_time: Optional[dt_time] = None,
    dosage_numeric: Optional[float] = None,
    unit: Optional[str] = None,
    plan_item_id: Optional[int] = None,
    status: Optional[str] = None,      # e.g., 'TAKEN', 'ON_TIME', 'LATE', 'SKIPPED'
    notes: Optional[str] = None
) -> int:

    conn = mydb()
    cur = conn.cursor()

    query = """
        INSERT INTO drug_records (
            user_id, drug_id, expected_date, expected_time,
            dosage_numeric, unit,
            plan_item_id, status, notes
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id;
    """

    cur.execute(query, (
        user_id, drug_id,
        expected_date, expected_time,
        dosage_numeric, unit,
        plan_item_id, status, notes # e.g., 'TAKEN', 'ON_TIME', 'LATE', 'SKIPPED'
    ))

    new_id = cur.fetchone()[0]
    conn.commit()

    cur.close()
    conn.close()

    return new_id


# ---------- GET BY ID ----------
def get_drug_record_by_id(record_id: int) -> Optional[drug_record]:
    conn = mydb()
    cur = conn.cursor()

    cur.execute("SELECT * FROM drug_records WHERE id = %s", (record_id,))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return None

    record = _row_to_drug_record(cur, row)

    cur.close()
    conn.close()
    return record


# ---------- GET LIST by USER ----------
def get_drug_records_by_user_id(user_id: int) -> List[drug_record]:
    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT * FROM drug_records
        WHERE user_id = %s
        ORDER BY expected_date DESC, expected_time DESC
    """
    cur.execute(query, (user_id,))
    rows = cur.fetchall()

    records = [_row_to_drug_record(cur, row) for row in rows]

    cur.close()
    conn.close()
    return records


# ---------- GET by DATE RANGE ----------
def get_drug_records_by_date_range(
    user_id: int,
    start: date,
    end: date
) -> List[drug_record]:

    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT * FROM drug_records
        WHERE user_id = %s
        AND expected_date BETWEEN %s AND %s
        ORDER BY expected_date, expected_time
    """

    cur.execute(query, (user_id, start, end))
    rows = cur.fetchall()

    records = [_row_to_drug_record(cur, row) for row in rows]

    cur.close()
    conn.close()
    return records


# ---------- DELETE ----------
def delete_drug_record(record_id: int) -> bool:
    conn = mydb()
    cur = conn.cursor()

    cur.execute("DELETE FROM drug_records WHERE id = %s", (record_id,))
    deleted = cur.rowcount > 0

    conn.commit()
    cur.close()
    conn.close()

    return deleted


# ---------- UPDATE ----------
def update_drug_record(
    record_id: int,
    status: str, # e.g., 'TAKEN', 'ON_TIME', 'LATE', 'SKIPPED'
    dosage_numeric: Optional[float],
    unit: Optional[str],
    notes: Optional[str]
) -> bool:

    conn = mydb()
    cur = conn.cursor()

    query = """
        UPDATE drug_records
        SET dosage_numeric = %s,
            unit = %s,
            status = %s,
            notes = %s,
            updated_at = NOW()
        WHERE id = %s
    """

    cur.execute(query, (
        dosage_numeric, unit,
        status, notes, # e.g., 'TAKEN', 'ON_TIME', 'LATE', 'SKIPPED'
        record_id
    ))

    updated = cur.rowcount > 0

    conn.commit()
    cur.close()
    conn.close()

    return updated


# ---------- GET by unique key (user + plan_item + date + time) ----------
def get_drug_record_by_unique_key(
    user_id: int,
    plan_item_id: int,
    expected_date: date,
    expected_time: Optional[dt_time]
) -> Optional[drug_record]:
    """
    用于 /mark_drug_taken：
    按 (user_id, plan_item_id, expected_date, expected_time) 找唯一记录。
    """
    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT *
        FROM drug_records
        WHERE user_id = %s
          AND plan_item_id = %s
          AND expected_date = %s
          AND (
                (expected_time IS NULL AND %s IS NULL)
             OR (expected_time = %s)
          )
        LIMIT 1
    """
    cur.execute(query, (user_id, plan_item_id, expected_date, expected_time, expected_time))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return None

    record = _row_to_drug_record(cur, row)

    cur.close()
    conn.close()

    return record


def get_drug_record_by_unique(
    user_id: int,
    plan_item_id: int,
    expected_date: date,
    expected_time: Optional[dt_time]
) -> Optional[drug_record]:
    """
    查是否已经有同一个 user / plan_item / expected_date / expected_time 的记录。
    用于防止重复打勾。
    """
    conn = mydb()
    cur = conn.cursor()

    if expected_time is None:
        query = """
            SELECT * FROM drug_records
            WHERE user_id = %s
              AND plan_item_id = %s
              AND expected_date = %s
              AND expected_time IS NULL
            LIMIT 1
        """
        cur.execute(query, (user_id, plan_item_id, expected_date))
    else:
        query = """
            SELECT * FROM drug_records
            WHERE user_id = %s
              AND plan_item_id = %s
              AND expected_date = %s
              AND expected_time = %s
            LIMIT 1
        """
        cur.execute(query, (user_id, plan_item_id, expected_date, expected_time))

    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return None

    record = _row_to_drug_record(cur, row)
    cur.close()
    conn.close()
    return record

def get_recent_completed_drug_records(
    user_id: int,
    limit: int = 10
) -> List[drug_record]:
    """
    获取用户最近完成的药物记录，按时间降序排列。
    """
    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT *
        FROM drug_records
        WHERE user_id = %s
          AND status = 'TAKEN'
        ORDER BY expected_date DESC, expected_time DESC
        LIMIT %s
    """

    cur.execute(query, (user_id, limit))
    rows = cur.fetchall()

    records = [_row_to_drug_record(cur, row) for row in rows]

    cur.close()
    conn.close()
    return records