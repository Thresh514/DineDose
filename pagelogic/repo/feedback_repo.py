from dataclasses import dataclass, asdict
from typing import Optional, List
from datetime import date, datetime
from config import mydb

# ===================== dataclass model =====================

@dataclass
class doctor_feedback:
    id: int
    patient_id: int
    doctor_id: int
    feedback_date: date
    feedback: str
    created_at: datetime

    def to_dict(self):
        """Serialize to JSON-friendly dict"""
        def serialize(obj):
            if isinstance(obj, (date, datetime)):
                return obj.isoformat()
            return obj
        return {k: serialize(v) for k, v in asdict(self).items()}

# ===================== internal helper =====================

def _row_to_feedback(cur, row) -> doctor_feedback:
    columns = [desc[0] for desc in cur.description]
    rd = dict(zip(columns, row))

    return doctor_feedback(
        id=rd["id"],
        patient_id=rd["patient_id"],
        doctor_id=rd["doctor_id"],
        feedback_date=rd["feedback_date"],
        feedback=rd["feedback"],
        created_at=rd["created_at"]
    )


# ===================== CRUD =====================

# ---------- CREATE or UPDATE ----------
def create_or_update_feedback(
    patient_id: int,
    doctor_id: int,
    feedback_date: date,
    feedback: str
) -> doctor_feedback:
    """Create or update feedback for a day (only one per day). Use ON CONFLICT to handle unique constraint."""
    conn = mydb()
    cur = conn.cursor()

    query = """
        INSERT INTO doctor_feedbacks (
            patient_id, doctor_id, feedback_date, feedback
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (patient_id, feedback_date)
        DO UPDATE SET feedback = EXCLUDED.feedback,
                      created_at = CURRENT_TIMESTAMP
        RETURNING *;
    """

    cur.execute(query, (patient_id, doctor_id, feedback_date, feedback))
    row = cur.fetchone()
    
    result = _row_to_feedback(cur, row)
    conn.commit()

    cur.close()
    conn.close()

    return result


# ---------- GET BY DATE ----------
def get_feedback_by_date(
    patient_id: int,
    feedback_date: date
) -> Optional[doctor_feedback]:
    """Get feedback for a day."""
    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT * FROM doctor_feedbacks
        WHERE patient_id = %s AND feedback_date = %s
        LIMIT 1
    """
    cur.execute(query, (patient_id, feedback_date))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return None

    feedback = _row_to_feedback(cur, row)

    cur.close()
    conn.close()
    return feedback


# ---------- GET BY DATE RANGE ----------
def get_feedbacks_by_date_range(
    patient_id: int,
    start_date: date,
    end_date: date
) -> List[doctor_feedback]:
    """Get all feedbacks within date range."""
    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT * FROM doctor_feedbacks
        WHERE patient_id = %s
        AND feedback_date BETWEEN %s AND %s
        ORDER BY feedback_date DESC
    """
    cur.execute(query, (patient_id, start_date, end_date))
    rows = cur.fetchall()

    feedbacks = [_row_to_feedback(cur, row) for row in rows]

    cur.close()
    conn.close()
    return feedbacks


# ---------- DELETE ----------
def delete_feedback(patient_id: int, feedback_date: date) -> bool:
    """Delete feedback for a day."""
    conn = mydb()
    cur = conn.cursor()

    query = """
        DELETE FROM doctor_feedbacks
        WHERE patient_id = %s AND feedback_date = %s
    """
    cur.execute(query, (patient_id, feedback_date))
    deleted = cur.rowcount > 0

    conn.commit()
    cur.close()
    conn.close()

    return deleted

