# notification_config_repo.py

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
from config import mydb
import config


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


# ================== 内部工具函数 ==================

def _row_to_notification_config(cur, row) -> NotificationConfig:
    """
    把一行 tuple 转成 NotificationConfig dataclass。
    和 drug 那套一样，通过 cur.description 拿列名。
    """
    columns = [desc[0] for desc in cur.description]
    rd = dict(zip(columns, row))

    # rd["notify_minutes"] 在 PostgreSQL 里是 list / array，直接用即可
    return NotificationConfig(
        user_id=rd["user_id"],
        enabled=rd["enabled"],
        email_enabled=rd["email_enabled"],
        notify_minutes=rd["notify_minutes"] or [],
        timezone=rd["timezone"],
    )


def _validate_notification_config(cfg: NotificationConfig) -> None:
    """
    做一点简单的校验，不合法直接 raise。
    """
    if not isinstance(cfg.notify_minutes, list):
        raise ValueError("notify_minutes 必须是 List[int]")

    for n in cfg.notify_minutes:
        if not isinstance(n, int):
            raise ValueError("notify_minutes 中的元素必须是 int")
        if n < -1440 or n > 1440:
            raise ValueError("notify_minutes 超出允许范围 [-1440, 1440]")

    if not cfg.timezone:
        raise ValueError("timezone 不能为空")


def default_notification_config(user_id: int) -> NotificationConfig:
    """
    新用户默认通知配置。
    """
    return NotificationConfig(
        user_id=user_id,
        enabled=True,
        email_enabled=True,
        notify_minutes=[30, 10, 0, -10, -30],
        timezone="UTC",
    )


# ================== repo functions ==================

def get_notification_config(user_id: int) -> Optional[NotificationConfig]:
    """
    查单个 user 的通知配置，不存在返回 None。
    """
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
    """
    批量查一组 user 的通知配置。
    返回 { user_id: NotificationConfig }，方便在 send_notifications 里用。
    """
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
    """
    只做 insert，不存在冲突就插入。
    """
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
            cfg.notify_minutes,  # integer[]，直接传 list 即可（Postgres）
            cfg.timezone,
        ),
    )

    conn.commit()
    cur.close()
    conn.close()


def update_notification_config(cfg: NotificationConfig) -> None:
    """
    更新一条已存在的配置。
    """
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
    """
    存在则更新，不存在则插入。
    依赖 user_id 上有 PRIMARY KEY / UNIQUE 约束。
    """
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
    """
    没有记录就插一条默认的。
    """
    cfg = get_notification_config(user_id)
    if cfg is not None:
        return cfg

    cfg = default_notification_config(user_id)
    create_notification_config(cfg)
    return cfg