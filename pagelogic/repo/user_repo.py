# user_repo.py
from dataclasses import dataclass, asdict, is_dataclass
from datetime import datetime, date, time as dt_time
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
    """
    只针对使用 Google 登录的用户。
    """
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
    """
    插入一条 user 记录并返回 User 实例。

    """
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
    """
    更新 username / avatar_url，返回更新后的 User。
    如果只想改其中一个，另一个传 None 表示不变。
    """
    # 动态拼 set 子句
    sets = []
    params = []

    if username is not None:
        sets.append("username = %s")
        params.append(username)
    if avatar_url is not None:
        sets.append("avatar_url = %s")
        params.append(avatar_url)

    if not sets:
        # 没有要更新的字段，直接返回当前 user
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
    """
    给定 patient_id，查这个 patient 对应的 doctor。
    这里通过 plan 表上的 (patient_id, doctor_id) 关系来反查 User。
    如果有多个 doctor，就先随便拿一个（可以按需要再加 ORDER BY）。
    """
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
    """
    给定 doctor_id，查出所有由这个 doctor 负责的 patient 列表。
    通过 plan 表上的 (doctor_id, patient_id) 关系反查 User。
    用 DISTINCT 去重，避免同一个 patient 有多个 plan。
    """
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