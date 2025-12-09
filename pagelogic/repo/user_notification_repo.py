# notification_config_repo.py
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
from config import mydb


# ================== dataclass model ==================

@dataclass
class NotificationConfig:
    user_id: int
    enabled: bool
    email_enabled: bool
    notify_minutes: List[int]
    timezone: str

    def to_dict(self) -> dict:
        return asdict(self)

    def __str__(self) -> str:
        return (
            f"NotificationConfig(user_id={self.user_id}, "
            f"enabled={self.enabled}, "
            f"email_enabled={self.email_enabled}, "
            f"notify_minutes={self.notify_minutes}, "
            f"timezone='{self.timezone}')"
        )


# ================== Internal helper functions ==================

def _row_to_notification_config(cur, row) -> NotificationConfig:
    """Convert a tuple row to NotificationConfig dataclass."""
    columns = [desc[0] for desc in cur.description]
    rd = dict(zip(columns, row))
    return NotificationConfig(
        user_id=rd["user_id"],
        enabled=rd["enabled"],
        email_enabled=rd["email_enabled"],
        notify_minutes=rd["notify_minutes"] or [],
        timezone=rd["timezone"],
    )


def _validate_notification_config(cfg: NotificationConfig) -> None:
    """Simple validation, raise if invalid."""
    if not isinstance(cfg.notify_minutes, list):
        raise ValueError("notify_minutes must be List[int]")

    for n in cfg.notify_minutes:
        if not isinstance(n, int):
            raise ValueError("Elements in notify_minutes must be int")
        if n < -1440 or n > 1440:
            raise ValueError("notify_minutes out of allowed range [-1440, 1440]")

    if not cfg.timezone:
        raise ValueError("timezone cannot be empty")


def default_notification_config(user_id: int) -> NotificationConfig:
    """Default notification config for new users."""
    return NotificationConfig(
        user_id=user_id,
        enabled=True,
        email_enabled=True,
        notify_minutes=[30, 10, 0, -10, -30],
        timezone="UTC",
    )


# ================== repo functions ==================

def get_notification_config(user_id: int) -> Optional[NotificationConfig]:
    """Get notification config for a single user; returns None if not found."""
    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT
            user_id,
            enabled,
            email_enabled,
            notify_minutes,
            timezone
        FROM user_med_notification_settings
        WHERE user_id = %s
    """

    cur.execute(query, (user_id,))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return None

    cfg = _row_to_notification_config(cur, row)

    cur.close()
    conn.close()
    return cfg


def get_notification_configs_by_user_ids(user_ids: List[int]) -> Dict[int, NotificationConfig]:
    """Batch query notification configs for a group of users. Returns {user_id: NotificationConfig}."""
    if not user_ids:
        return {}

    conn = mydb()
    cur = conn.cursor()

    placeholders = ",".join(["%s"] * len(user_ids))
    query = f"""
        SELECT
            user_id,
            enabled,
            email_enabled,
            notify_minutes,
            timezone
        FROM user_med_notification_settings
        WHERE user_id IN ({placeholders})
    """

    cur.execute(query, tuple(user_ids))
    rows = cur.fetchall()

    res: Dict[int, NotificationConfig] = {}
    for row in rows:
        cfg = _row_to_notification_config(cur, row)
        res[cfg.user_id] = cfg

    cur.close()
    conn.close()
    return res


def create_notification_config(cfg: NotificationConfig) -> None:
    """Insert only, insert if no conflict."""
    _validate_notification_config(cfg)

    conn = mydb()
    cur = conn.cursor()

    query = """
        INSERT INTO user_med_notification_settings
            (user_id, enabled, email_enabled, notify_minutes, timezone)
        VALUES (%s, %s, %s, %s, %s)
    """

    cur.execute(
        query,
        (
            cfg.user_id,
            cfg.enabled,
            cfg.email_enabled,
            cfg.notify_minutes,
            cfg.timezone,
        ),
    )

    conn.commit()
    cur.close()
    conn.close()


def update_notification_config(cfg: NotificationConfig) -> None:
    """Update an existing config."""
    _validate_notification_config(cfg)

    conn = mydb()
    cur = conn.cursor()

    query = """
        UPDATE user_med_notification_settings
        SET
            enabled = %s,
            email_enabled = %s,
            notify_minutes = %s,
            timezone = %s,
            updated_at = NOW()
        WHERE user_id = %s
    """

    cur.execute(
        query,
        (
            cfg.enabled,
            cfg.email_enabled,
            cfg.notify_minutes,
            cfg.timezone,
            cfg.user_id,
        ),
    )

    conn.commit()
    cur.close()
    conn.close()


def upsert_notification_config(cfg: NotificationConfig) -> None:
    """Update if exists, insert if not. Requires PRIMARY KEY / UNIQUE constraint on user_id."""
    _validate_notification_config(cfg)

    conn = mydb()
    cur = conn.cursor()

    query = """
        INSERT INTO user_med_notification_settings
            (user_id, enabled, email_enabled, notify_minutes, timezone)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            enabled = EXCLUDED.enabled,
            email_enabled = EXCLUDED.email_enabled,
            notify_minutes = EXCLUDED.notify_minutes,
            timezone = EXCLUDED.timezone,
            updated_at = NOW()
    """

    cur.execute(
        query,
        (
            cfg.user_id,
            cfg.enabled,
            cfg.email_enabled,
            cfg.notify_minutes,
            cfg.timezone,
        ),
    )

    conn.commit()
    cur.close()
    conn.close()


def get_or_create_default_notification_config(user_id: int) -> NotificationConfig:
    """Insert default if no record exists."""
    cfg = get_notification_config(user_id)
    if cfg is not None:
        return cfg

    cfg = default_notification_config(user_id)
    create_notification_config(cfg)
    return cfg