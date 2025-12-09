# user_repo.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from config import mydb
import utils.serializer as serializer


# ==================== User dataclass ====================

@dataclass
class User:
    id: int
    username: Optional[str]
    email: str
    google_id: Optional[str]
    avatar_url: Optional[str]
    role: str          # 'patient' / 'doctor'
    is_verified: bool
    created_at: datetime

    def to_dict(self) -> dict:
        return serializer.serialize_for_json(self)

    def __str__(self) -> str:
        return (
            f"User("
            f"id={self.id}, "
            f"username={self.username!r}, "
            f"email={self.email!r}, "
            f"role={self.role!r}, "
            f"is_verified={self.is_verified}, "
            f"created_at={self.created_at}"
            f")"
        )


# ==================== repo functions ====================

def _row_to_user(cur, row) -> User:
    rd = serializer.row_to_dict(cur, row)
    return User(
        id=rd["id"],
        username=rd.get("username"),
        email=rd["email"],
        google_id=rd.get("google_id"),
        avatar_url=rd.get("avatar_url"),
        role=rd["role"],
        is_verified=rd["is_verified"],
        created_at=rd["created_at"],
    )


def get_user_by_id(user_id: int) -> Optional[User]:
    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT id, username, email, google_id, avatar_url,
               role, is_verified, created_at
        FROM "users"
        WHERE id = %s
    """
    cur.execute(query, (user_id,))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return None

    user = _row_to_user(cur, row)

    cur.close()
    conn.close()
    return user

def get_all_users() -> List[User]:
    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT id, username, email, google_id, avatar_url,
               role, is_verified, created_at
        FROM "users"
        ORDER BY created_at ASC
    """
    cur.execute(query)
    rows = cur.fetchall()

    users: List[User] = [_row_to_user(cur, row) for row in rows]

    cur.close()
    conn.close()
    return users

def get_user_by_email(email: str) -> Optional[User]:
    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT id, username, email, google_id, avatar_url,
               role, is_verified, created_at
        FROM "users"
        WHERE email = %s
    """
    cur.execute(query, (email,))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return None

    user = _row_to_user(cur, row)

    cur.close()
    conn.close()
    return user


def get_user_by_google_id(google_id: str) -> Optional[User]:
    """Only for users logged in with Google."""
    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT id, username, email, google_id, avatar_url,
               role, is_verified, created_at
        FROM "users"
        WHERE google_id = %s
    """
    cur.execute(query, (google_id,))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return None

    user = _row_to_user(cur, row)

    cur.close()
    conn.close()
    return user


def create_user(
    *,
    username: Optional[str],
    email: str,
    google_id: Optional[str],
    avatar_url: Optional[str],
    role: str,
    is_verified: bool = True,
) -> User:
    """Insert a user record and return User instance."""
    conn = mydb()
    cur = conn.cursor()

    query = """
        INSERT INTO "users" (username, email, google_id, avatar_url, role, is_verified)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, username, email, google_id, avatar_url,
                  role, is_verified, created_at
    """
    cur.execute(
        query,
        (username, email, google_id, avatar_url, role, is_verified),
    )

    row = cur.fetchone()
    conn.commit()

    user = _row_to_user(cur, row)

    cur.close()
    conn.close()
    return user


def update_user_basic_info(
    user_id: int,
    *,
    username: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> Optional[User]:
    """Update username/avatar_url, return updated User. Pass None for unchanged field."""
    # Dynamically build SET clause
    sets = []
    params = []

    if username is not None:
        sets.append("username = %s")
        params.append(username)
    if avatar_url is not None:
        sets.append("avatar_url = %s")
        params.append(avatar_url)

    if not sets:
        return get_user_by_id(user_id)

    params.append(user_id)

    conn = mydb()
    cur = conn.cursor()

    query = f"""
        UPDATE "users"
        SET {", ".join(sets)}
        WHERE id = %s
        RETURNING id, username, email, google_id, avatar_url,
                  role, is_verified, created_at
    """

    cur.execute(query, tuple(params))
    row = cur.fetchone()
    conn.commit()

    if not row:
        cur.close()
        conn.close()
        return None

    user = _row_to_user(cur, row)

    cur.close()
    conn.close()
    return user



def get_doctor_by_patient_id(patient_id: int) -> Optional[User]:
    """Given patient_id, find corresponding doctor via plan table. If multiple doctors, take one."""
    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT DISTINCT
            u.id, u.username, u.email, u.google_id, u.avatar_url,
            u.role, u.is_verified, u.created_at
        FROM "users" u
        JOIN plan p
            ON p.doctor_id = u.id
        WHERE p.patient_id = %s
          AND u.role = 'doctor'
        LIMIT 1
    """
    cur.execute(query, (patient_id,))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return None

    user = _row_to_user(cur, row)

    cur.close()
    conn.close()
    return user


def get_patients_by_doctor_id(doctor_id: int) -> List[User]:
    """Given doctor_id, find all patients managed by this doctor via plan table. Use DISTINCT to dedupe."""
    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT DISTINCT
            u.id, u.username, u.email, u.google_id, u.avatar_url,
            u.role, u.is_verified, u.created_at
        FROM "users" u
        JOIN plan p
            ON p.patient_id = u.id
        WHERE p.doctor_id = %s
          AND u.role = 'patient'
        ORDER BY u.created_at ASC
    """
    cur.execute(query, (doctor_id,))
    rows = cur.fetchall()

    patients: List[User] = [_row_to_user(cur, row) for row in rows]

    cur.close()
    conn.close()
    return patients


def get_users_by_ids(user_ids: List[int]) -> List[User]:
    """Batch query user_ids, return corresponding User list."""
    if not user_ids:
        return []

    conn = mydb()
    cur = conn.cursor()

    placeholders = ",".join(["%s"] * len(user_ids))
    query = f"""
        SELECT id, username, email, google_id, avatar_url,
               role, is_verified, created_at
        FROM "users"
        WHERE id IN ({placeholders})
    """

    cur.execute(query, tuple(user_ids))
    rows = cur.fetchall()

    users: List[User] = [_row_to_user(cur, row) for row in rows]

    cur.close()
    conn.close()
    return users
