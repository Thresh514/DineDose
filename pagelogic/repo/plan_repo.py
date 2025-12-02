from dataclasses import dataclass, field, asdict, is_dataclass
from datetime import date, time as dt_time, datetime
from typing import List, Optional, Dict
from config import mydb
import utils.serializer as serializer


@dataclass
class plan_item_rule:
    id: int
    plan_item_id: int
    start_date: date
    end_date: Optional[date]
    repeat_type: str          # 'ONCE', 'DAILY', 'WEEKLY', 'PRN'
    interval_value: Optional[int]
    mon: bool
    tue: bool
    wed: bool
    thu: bool
    fri: bool
    sat: bool
    sun: bool
    # PostgreSQL time[] -> Python list[datetime.time] 或 list[str]
    times: Optional[List[dt_time]] = None

    def to_dict(self) -> dict:
        return serializer.serialize_for_json(self)

    def __str__(self) -> str:
        return (
            f"PlanItemRule("
            f"id={self.id}, "
            f"plan_item_id={self.plan_item_id}, "
            f"repeat_type={self.repeat_type}, "
            f"start_date={self.start_date}, "
            f"end_date={self.end_date}, "
            f"times={self.times}"
            f")"
        )


@dataclass
class plan_item:
    id: int
    plan_id: int
    drug_id: int
    drug_name: Optional[str]   # Not stored in DB, filled in logic layer
    dosage: int
    unit: str
    amount_literal: Optional[str]
    note: Optional[str]
    date: Optional["date"] = None
    time: Optional[dt_time] = None
    plan_item_rule: Optional["plan_item_rule"] = None

    def to_dict(self) -> dict:
        return serializer.serialize_for_json(self)

    def __str__(self) -> str:
        return (
            f"PlanItem("
            f"id={self.id}, "
            f"plan_id={self.plan_id}, "
            f"drug_id={self.drug_id}, "
            f"drug_name='{self.drug_name}', "
            f"dosage={self.dosage}{self.unit}, "
            f"date={self.date}, "
            f"time={self.time}, "
            f"rule_id={self.plan_item_rule.id if self.plan_item_rule else None}"
            f")"
        )


@dataclass
class plan:
    id: int
    patient_id: int
    doctor_id: int
    name: str
    description: Optional[str]
    doctor_name: Optional[str]
    patient_name: Optional[str]
    plan_items: List[plan_item] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"Plan("
            f"id={self.id}, "
            f"patient_id={self.patient_id}, "
            f"doctor_id={self.doctor_id}, "
            f"name='{self.name}', "
            f"patient_name='{self.patient_name}', "
            f"doctor_name='{self.doctor_name}', "
            f"plan_items_count={len(self.plan_items)}"
            f")"
        )

    def to_dict(self) -> dict:
        return serializer.serialize_for_json(self)


# ==================== repo functions ====================

def _row_to_dict(cur, row) -> dict:
    """Convert tuple row to dict, avoid DictCursor dependency."""
    columns = [desc[0] for desc in cur.description]
    return dict(zip(columns, row))


def get_plan_by_user_id(user_id: int) -> Optional[plan]:
    """Get a plan instance by patient_id."""
    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT id, patient_id, doctor_id, name, description,
               doctor_name, patient_name
        FROM plan
        WHERE patient_id = %s
        LIMIT 1
    """
    cur.execute(query, (user_id,))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return None

    row_dict = _row_to_dict(cur, row)

    cur.close()
    conn.close()

    return plan(
        id=row_dict["id"],
        patient_id=row_dict["patient_id"],
        doctor_id=row_dict["doctor_id"],
        name=row_dict["name"],
        description=row_dict.get("description"),
        doctor_name=row_dict.get("doctor_name"),
        patient_name=row_dict.get("patient_name"),
    )

def get_plans_by_user_ids(user_ids: List[int]) -> List[plan]:
    """Get plan list for a group of patient_ids."""
    if not user_ids:
        return []

    conn = mydb()
    cur = conn.cursor()

    placeholders = ",".join(["%s"] * len(user_ids))
    query = f"""
        SELECT id, patient_id, doctor_id, name, description,
               doctor_name, patient_name
        FROM plan
        WHERE patient_id IN ({placeholders})
    """
    cur.execute(query, tuple(user_ids))
    rows = cur.fetchall()

    plans = dict()
    for row in rows:
        rd = _row_to_dict(cur, row)
        p = plan(
            id=rd["id"],
            patient_id=rd["patient_id"],
            doctor_id=rd["doctor_id"],
            name=rd["name"],
            description=rd.get("description"),
            doctor_name=rd.get("doctor_name"),
            patient_name=rd.get("patient_name"),
        )
        plans[rd["patient_id"]] = p

    cur.close()
    conn.close()
    return plans


def get_plan_by_id(plan_id: int) -> Optional[plan]:
    """Get a plan instance by plan.id."""
    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT id, patient_id, doctor_id, name, description,
               doctor_name, patient_name
        FROM plan
        WHERE id = %s
    """
    cur.execute(query, (plan_id,))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return None

    row_dict = _row_to_dict(cur, row)

    cur.close()
    conn.close()

    return plan(
        id=row_dict["id"],
        patient_id=row_dict["patient_id"],
        doctor_id=row_dict["doctor_id"],
        name=row_dict["name"],
        description=row_dict.get("description"),
        doctor_name=row_dict.get("doctor_name"),
        patient_name=row_dict.get("patient_name"),
    )


def get_all_plan_items_by_plan_id(plan_id: int) -> List[plan_item]:
    """Return all plan_item list for specified plan_id."""
    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT id, plan_id, drug_id, dosage, unit,
               amount_literal, note
        FROM plan_item
        WHERE plan_id = %s
    """
    cur.execute(query, (plan_id,))
    rows = cur.fetchall()

    items: List[plan_item] = []
    for row in rows:
        rd = _row_to_dict(cur, row)
        item = plan_item(
            id=rd["id"],
            plan_id=rd["plan_id"],
            drug_id=rd["drug_id"],
            drug_name=None,
            dosage=rd["dosage"],
            unit=rd["unit"],
            amount_literal=rd.get("amount_literal"),
            note=rd.get("note"),
            date=None,
            time=None,
            plan_item_rule=None,
        )
        items.append(item)

    cur.close()
    conn.close()
    return items

def get_all_plan_items() -> List[plan_item]:
    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT id, plan_id, drug_id, dosage, unit,
               amount_literal, note
        FROM plan_item
    """
    cur.execute(query)
    rows = cur.fetchall()

    items: List[plan_item] = []
    for row in rows:
        rd = _row_to_dict(cur, row)
        item = plan_item(
            id=rd["id"],
            plan_id=rd["plan_id"],
            drug_id=rd["drug_id"],
            drug_name=None,                     
            dosage=rd["dosage"],
            unit=rd["unit"],
            amount_literal=rd.get("amount_literal"),
            note=rd.get("note"),
            date=None,
            time=None,
            plan_item_rule=None,
        )
        items.append(item)

    cur.close()
    conn.close()
    print("[DEBUG] get_all_plan_items:", len(items))
    return items


def get_plan_item_rules_by_plan_id(plan_id: int) -> Dict[int, List[plan_item_rule]]:
    """Get dictionary of plan_item_id -> [plan_item_rule, ...] by plan_id."""
    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT 
            pi.id AS plan_item_id,
            pir.id AS rule_id,
            pir.plan_item_id AS rule_plan_item_id,
            pir.start_date AS rule_start_date,
            pir.end_date AS rule_end_date,
            pir.repeat_type AS rule_repeat_type,
            pir.interval_value AS rule_interval_value,
            pir.mon AS rule_mon,
            pir.tue AS rule_tue,
            pir.wed AS rule_wed,
            pir.thu AS rule_thu,
            pir.fri AS rule_fri,
            pir.sat AS rule_sat,
            pir.sun AS rule_sun,
            pir.times AS rule_times
        FROM plan_item pi
        LEFT JOIN plan_item_rule pir
        ON pi.id = pir.plan_item_id
        WHERE pi.plan_id = %s;
    """

    cur.execute(query, (plan_id,))
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    cur.close()
    conn.close()

    item_id_to_rules: Dict[int, List[plan_item_rule]] = {}

    for row in rows:
        rd = dict(zip(columns, row))
        item_id = rd["plan_item_id"]

        # plan_item may exist without rule (LEFT JOIN)
        if rd["rule_id"] is None:
            item_id_to_rules.setdefault(item_id, [])
            continue

        rule_obj = plan_item_rule(
            id=rd["rule_id"],
            plan_item_id=rd["rule_plan_item_id"],
            start_date=rd["rule_start_date"],
            end_date=rd["rule_end_date"],
            repeat_type=rd["rule_repeat_type"],
            interval_value=rd["rule_interval_value"],
            mon=rd["rule_mon"],
            tue=rd["rule_tue"],
            wed=rd["rule_wed"],
            thu=rd["rule_thu"],
            fri=rd["rule_fri"],
            sat=rd["rule_sat"],
            sun=rd["rule_sun"],
            times=rd["rule_times"],
        )

        item_id_to_rules.setdefault(item_id, []).append(rule_obj)

    return item_id_to_rules


from typing import Any

# ====== Internal helper: parse time string ======
def _parse_time_str(t: str) -> dt_time:
    parts = t.split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0
    second = int(parts[2]) if len(parts) > 2 else 0
    return dt_time(hour, minute, second)


# ====== CREATE: new plan_item + corresponding rules ======
def create_plan_item_with_rules(
    plan_id: int,
    drug_id: int,
    dosage: int,
    unit: str,
    amount_literal: Optional[str],
    note: Optional[str],
    rules: List[Dict[str, Any]],
) -> int:
    """Create a plan_item and insert corresponding plan_item_rule list at once."""
    conn = mydb()
    cur = conn.cursor()

    try:
        # Insert plan_item first
        insert_item_sql = """
            INSERT INTO plan_item (plan_id, drug_id, dosage, unit, amount_literal, note)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
        """
        cur.execute(
            insert_item_sql,
            (plan_id, drug_id, dosage, unit, amount_literal, note),
        )
        new_item_id = cur.fetchone()[0]

        # Insert corresponding rule
        insert_rule_sql = """
            INSERT INTO plan_item_rule (
                plan_item_id,
                start_date, end_date,
                repeat_type, interval_value,
                mon, tue, wed, thu, fri, sat, sun,
                times
            )
            VALUES (
                %s,
                %s, %s,
                %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s
            )
        """

        for r in rules:
            times_list = r.get("times") or []
            cur.execute(
                insert_rule_sql,
                (
                    new_item_id,
                    r["start_date"],
                    r.get("end_date"),
                    r["repeat_type"],
                    r.get("interval_value"),
                    r.get("mon", False),
                    r.get("tue", False),
                    r.get("wed", False),
                    r.get("thu", False),
                    r.get("fri", False),
                    r.get("sat", False),
                    r.get("sun", False),
                    times_list,
                ),
            )

        conn.commit()
        return new_item_id
    except Exception as e:
        conn.rollback()
        print("create_plan_item_with_rules ERROR:", e)
        raise
    finally:
        cur.close()
        conn.close()


# ====== UPDATE: modify plan_item + replace all rules ======
def update_plan_item_with_rules(
    item_id: int,
    plan_id: int,
    drug_id: int,
    dosage: int,
    unit: str,
    amount_literal: Optional[str],
    note: Optional[str],
    rules: List[Dict[str, Any]],
) -> bool:
    """Modify plan_item basic info, delete all existing rules, then insert new rule list."""
    conn = mydb()
    cur = conn.cursor()

    try:
        # Update plan_item
        update_item_sql = """
            UPDATE plan_item
            SET plan_id = %s,
                drug_id = %s,
                dosage = %s,
                unit = %s,
                amount_literal = %s,
                note = %s
            WHERE id = %s
        """
        cur.execute(
            update_item_sql,
            (plan_id, drug_id, dosage, unit, amount_literal, note, item_id),
        )

        if cur.rowcount == 0:
            conn.rollback()
            return False

        # Delete old rules
        cur.execute("DELETE FROM plan_item_rule WHERE plan_item_id = %s", (item_id,))

        # Insert new rules
        insert_rule_sql = """
            INSERT INTO plan_item_rule (
                plan_item_id,
                start_date, end_date,
                repeat_type, interval_value,
                mon, tue, wed, thu, fri, sat, sun,
                times
            )
            VALUES (
                %s,
                %s, %s,
                %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s
            )
        """

        for r in rules:
            times_list = r.get("times") or []
            cur.execute(
                insert_rule_sql,
                (
                    item_id,
                    r["start_date"],
                    r.get("end_date"),
                    r["repeat_type"],
                    r.get("interval_value"),
                    r.get("mon", False),
                    r.get("tue", False),
                    r.get("wed", False),
                    r.get("thu", False),
                    r.get("fri", False),
                    r.get("sat", False),
                    r.get("sun", False),
                    times_list,
                ),
            )

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print("update_plan_item_with_rules ERROR:", e)
        raise
    finally:
        cur.close()
        conn.close()


# ====== DELETE: delete plan_item + corresponding rules ======
def delete_plan_item_and_rules(item_id: int) -> bool:
    conn = mydb()
    cur = conn.cursor()
    try:
        # Delete rule first
        cur.execute("DELETE FROM plan_item_rule WHERE plan_item_id = %s", (item_id,))
        # Then delete item
        cur.execute("DELETE FROM plan_item WHERE id = %s", (item_id,))
        deleted = cur.rowcount > 0
        conn.commit()
        return deleted
    except Exception as e:
        conn.rollback()
        print("delete_plan_item_and_rules ERROR:", e)
        raise
    finally:
        cur.close()
        conn.close()


# ====== CREATE: create plan ======
def create_plan(
    patient_id: int,
    doctor_id: int,
    name: str = "Default Plan",
    description: Optional[str] = None,
    doctor_name: Optional[str] = None,
    patient_name: Optional[str] = None,
) -> plan:
    """Create a new plan, establish doctor-patient relationship. Return existing plan if patient already has one."""
    conn = mydb()
    cur = conn.cursor()
    
    try:
        # Check if plan already exists
        existing = get_plan_by_user_id(patient_id)
        if existing:
            cur.close()
            conn.close()
            return existing
        
        # Create new plan
        query = """
            INSERT INTO plan (patient_id, doctor_id, name, description, doctor_name, patient_name)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, patient_id, doctor_id, name, description, doctor_name, patient_name
        """
        cur.execute(
            query,
            (patient_id, doctor_id, name, description, doctor_name, patient_name),
        )
        row = cur.fetchone()
        conn.commit()
        
        row_dict = _row_to_dict(cur, row)
        new_plan = plan(
            id=row_dict["id"],
            patient_id=row_dict["patient_id"],
            doctor_id=row_dict["doctor_id"],
            name=row_dict["name"],
            description=row_dict.get("description"),
            doctor_name=row_dict.get("doctor_name"),
            patient_name=row_dict.get("patient_name"),
        )
        
        cur.close()
        conn.close()
        return new_plan
    except Exception as e:
        conn.rollback()
        print("create_plan ERROR:", e)
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()