import logging
from dataclasses import dataclass, asdict
from datetime import date, datetime, time as dt_time, timedelta, timezone
from typing import List, Optional, Tuple, Set

from pagelogic.service import plan_service
from pagelogic.repo import drug_record_repo
import pagelogic.repo.plan_repo as plan_repo
import pagelogic.repo.user_repo as user_repo
import pagelogic.repo.user_notification_repo as user_notification_repo
from utils.emailsender import send_email_ses


# =========================
# Data model for scheduler
# =========================

@dataclass
class ScheduledDose:
    """ A single expanded medication event with concrete date/time. """
    user_id: int
    plan_item_id: int
    expected_date: date
    expected_time: Optional[dt_time]

    drug_name: Optional[str]
    dosage: Optional[int]
    unit: Optional[str]


# =========================
# Step 1: collect scheduled doses
# =========================
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_scheduled_doses_within(days: int) -> List[ScheduledDose]:
    print("\n==================== STEP 1: Collect scheduled doses ====================")
    now = datetime.now()

    window_start = now
    window_end = now + timedelta(days=days)


    # 1) Fetch all users
    users = user_repo.get_all_users()
    user_ids = [user.id for user in users]

    # 2) Get plans for users
    plans = plan_repo.get_plans_by_user_ids(user_ids)

    # Filter users with a plan
    users_with_plans = [u for u in users if u.id in plans]

    # --------- 并发展开每个用户的 plan ---------
    def expand_user_plan(user) -> List[ScheduledDose]:
        """在单个线程里处理一个 user 的 plan，返回该用户的所有 ScheduledDose。"""
        print(f"\n[STEP1] Expanding plan for user_id={user.id}")

        plan = plan_service.get_user_plan(
            id=user.id,
            from_when=window_start,
            to_when=window_end,
        )

        if not plan:
            print(f"[STEP1]   No plan returned for user {user.id}")
            return []
        if not plan.plan_items:
            print(f"[STEP1]   Plan has no items for user {user.id}")
            return []

        print(f"[STEP1]   Expanded plan_items count={len(plan.plan_items)}")

        user_scheduled: List[ScheduledDose] = []
        for item in plan.plan_items:
            if item.date is None:
                continue

            sd = ScheduledDose(
                user_id=user.id,
                plan_item_id=item.id,
                expected_date=item.date,
                expected_time=item.time,
                drug_name=getattr(item, "drug_name", None),
                dosage=getattr(item, "dosage", None),
                unit=getattr(item, "unit", None),
            )
            print(f"[STEP1]   Added ScheduledDose: {sd}")
            user_scheduled.append(sd)

        return user_scheduled

    scheduled: List[ScheduledDose] = []

    # 控制线程数，避免把 DB 打爆
    max_workers = min(8, len(users_with_plans)) or 1

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_user_id = {
            executor.submit(expand_user_plan, user): user.id
            for user in users_with_plans
        }

        for future in as_completed(future_to_user_id):
            uid = future_to_user_id[future]
            try:
                user_doses = future.result()
                print(f"[STEP1]   User {uid} produced {len(user_doses)} doses")
                scheduled.extend(user_doses)
            except Exception as e:
                # 避免某个用户异常直接把整个 job 打崩
                print(f"[STEP1]   Error expanding plan for user {uid}: {e}")

    return scheduled

# =========================
# Step 2: diff scheduled vs completed
# =========================

def find_missed_doses(
    scheduled: List[ScheduledDose],
    recent_records: List[drug_record_repo.drug_record],
) -> List[ScheduledDose]:

    completed_keys = set()

    for record in recent_records:
        key = (
            record.user_id,
            record.plan_item_id,
            record.expected_date,
            record.expected_time,
        )
        completed_keys.add(key)

    missed = []

    for dose in scheduled:
        key = (
            dose.user_id,
            dose.plan_item_id,
            dose.expected_date,
            dose.expected_time,
        )
        if key not in completed_keys:
            missed.append(dose)

    return missed


# =========================
# Step 3: main entry
# =========================

def notify_jobs(days:int, interval:int) -> None:
    print("\n==================== NOTIFY JOB START ====================")
    print(f"[MAIN] Running notify_jobs(days={days})")

    # Step 1
    scheduled_doses = get_scheduled_doses_within(days)

    # Step 2
    recent_records = drug_record_repo.get_recent_completed_drug_records(days)

    # Step 3
    missed_doses = find_missed_doses(scheduled_doses, recent_records)

    # Step 4
    send_notifications(missed_doses, interval)


# =========================
# Step 4: send notifications
# =========================
# interval: seconds between checks
def send_notifications(missed_doses: List[ScheduledDose], interval: int) -> None:
    """
    对每个 missed dose：
    - 对每个 offset in notify_minutes：
        target_dt = scheduled_dt + offset(min)
        如果 |target_dt - now| < interval（秒）则本次 cron 触发一次通知
    """
    print("\n==================== STEP 4: Sending notifications ====================")

    if not missed_doses:
        return

    # 当前时间（本地时间）
    now = datetime.now()
    interval_seconds = interval

    user_ids = {dose.user_id for dose in missed_doses}

    users = user_repo.get_users_by_ids(list(user_ids))
    user_id_to_email = {u.id: u.email for u in users}
    user_id_to_name = {u.id: u.username for u in users}

    user_id_to_config = user_notification_repo.get_notification_configs_by_user_ids(
        list(user_ids)
    )
    print("[STEP4] Loaded notification configs:")
    for uid, cfg in user_id_to_config.items():
        print(f"  user_id={uid}, notify_minutes={cfg.notify_minutes}, enabled={cfg.enabled}")

    for dose in missed_doses:
        cfg = user_id_to_config.get(dose.user_id)
        if not cfg:
            continue
        if not cfg.enabled or not cfg.email_enabled:
            continue

        # 计划服药时间（本地）
        scheduled_time = dose.expected_time or dt_time(9, 0)
        scheduled_dt = datetime.combine(dose.expected_date, scheduled_time)

        # 是否本次 cron 需要触发这个 dose 的通知
        should_send = False

        for offset in cfg.notify_minutes:
            target_dt = scheduled_dt + timedelta(minutes=offset)
            diff_seconds = (target_dt - now).total_seconds()

            print(
                f"[STEP4]   check offset={offset}: "
                f"target_dt={target_dt}, diff_seconds={diff_seconds}"
            )

            # 只在「提前 interval 秒之内」这一段时间触发一次
            if 0 <= diff_seconds < interval_seconds:
                print(f"(diff_seconds={diff_seconds} is < {interval_seconds} and is >= 0), will notify.")
                should_send = True
                break

        if not should_send:
            print("[STEP4]   No offset matched in this run, skipping")
            continue

        email = user_id_to_email.get(dose.user_id)
        if not email:
            continue

        user_name = user_id_to_name.get(dose.user_id, "")
        subject = "DineDose Medication Reminder"
        body = build_email_body(dose, user_name)

        send_email_ses(email, subject, body)


# =========================
# Email body
# =========================

def build_email_body(dose: ScheduledDose, user_name: str) -> str:
    scheduled_time = dose.expected_time or dt_time(9, 0)
    scheduled_dt = datetime.combine(dose.expected_date, scheduled_time)
    scheduled_str = scheduled_dt.strftime("%Y-%m-%d %H:%M")

    drug_name = dose.drug_name or "Your medication"
    display_name = user_name or "User"

    dosage_part = ""
    if dose.dosage and dose.unit:
        dosage_part = f" (Dosage: {dose.dosage} {dose.unit})"

    return (
        f"Hello {display_name},\n\n"
        f"This is a medication reminder from DineDose:\n"
        f"- Medication: {drug_name}{dosage_part}\n"
        f"- Scheduled time: {scheduled_str}\n\n"
        f"Please confirm whether you have taken this medication.\n"
        f"If you have already taken it, you can ignore this email.\n\n"
        f"— DineDose Team"
    )