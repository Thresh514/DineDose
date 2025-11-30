import logging
from dataclasses import dataclass
from datetime import date, datetime, time as dt_time, timedelta, timezone
from typing import List, Optional

from pagelogic.service import plan_service
from pagelogic.repo import drug_record_repo
import pagelogic.repo.plan_repo as plan_repo
import pagelogic.repo.user_repo as user_repo
import pagelogic.repo.user_notification_repo as user_notification_repo
from utils.emailsender import send_email_ses

from concurrent.futures import ThreadPoolExecutor, as_completed

# Always use the same reference time zone
UTC_MINUS_5 = timezone(timedelta(hours=-5))


def get_now() -> datetime:
    """Return the current time interpreted as UTC-5, but stored as a naive datetime."""
    return datetime.now(UTC_MINUS_5).replace(tzinfo=None)


@dataclass
class ScheduledDose:
    user_id: int
    plan_item_id: int
    expected_date: date
    expected_time: Optional[dt_time]
    drug_name: Optional[str]
    dosage: Optional[int]
    unit: Optional[str]


# ----------------------------------------------------
# Step 1 — Collect scheduled doses
# ----------------------------------------------------

def get_scheduled_doses_within(days: int, now: datetime) -> List[ScheduledDose]:
    window_start = now
    window_end = now + timedelta(days=days)

    users = user_repo.get_all_users()
    user_ids = [u.id for u in users]

    plans = plan_repo.get_plans_by_user_ids(user_ids)
    users_with_plans = [u for u in users if u.id in plans]

    def expand_user_plan(user) -> List[ScheduledDose]:
        plan = plan_service.get_user_plan(
            id=user.id,
            from_when=window_start,
            to_when=window_end,
        )
        if not plan or not plan.plan_items:
            return []

        result: List[ScheduledDose] = []
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
            result.append(sd)
        return result

    scheduled: List[ScheduledDose] = []

    max_workers = min(8, len(users_with_plans)) or 1
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_uid = {
            executor.submit(expand_user_plan, user): user.id
            for user in users_with_plans
        }

        for future in as_completed(future_to_uid):
            try:
                scheduled.extend(future.result())
            except Exception as e:
                print(f"[STEP1] Error expanding plan: {e}")

    return scheduled


# ----------------------------------------------------
# Step 2 — Find missed doses
# ----------------------------------------------------

def find_missed_doses(
    scheduled: List[ScheduledDose],
    recent_records: List[drug_record_repo.drug_record],
) -> List[ScheduledDose]:

    completed = {
        (r.user_id, r.plan_item_id, r.expected_date, r.expected_time)
        for r in recent_records
    }

    missed: List[ScheduledDose] = []
    for dose in scheduled:
        key = (dose.user_id, dose.plan_item_id, dose.expected_date, dose.expected_time)
        if key not in completed:
            missed.append(dose)

    return missed


# ----------------------------------------------------
# Step 3 — Main job entry
# ----------------------------------------------------

def notify_jobs(days: int, interval: int) -> None:
    now = get_now()
    print(f"[STEP0] notify_jobs started at {now.isoformat()}")

    scheduled = get_scheduled_doses_within(days, now)
    print(f"[STEP1] Retrieved {len(scheduled)} scheduled doses within {days} days.")

    recent = drug_record_repo.get_recent_completed_drug_records(days, now)
    print(f"[STEP2] Retrieved {len(recent)} recent completed drug records within {days} days.")

    missed = find_missed_doses(scheduled, recent)
    print(f"[STEP3] Found {len(missed)} missed doses to notify.")



    send_notifications(missed, interval, now)


# ----------------------------------------------------
# Step 4 — Notifications
# ----------------------------------------------------

def send_notifications(missed_doses: List[ScheduledDose], interval: int, now: datetime) -> None:
    if not missed_doses:
        return

    interval_seconds = interval
    user_ids = {d.user_id for d in missed_doses}

    users = user_repo.get_users_by_ids(list(user_ids))
    user_email = {u.id: u.email for u in users}
    user_name = {u.id: u.username for u in users}

    configs = user_notification_repo.get_notification_configs_by_user_ids(list(user_ids))

    for dose in missed_doses:
        cfg = configs.get(dose.user_id)
        if not cfg or not cfg.enabled or not cfg.email_enabled:
            continue

        scheduled_time = dose.expected_time or dt_time(9, 0)
        scheduled_dt = datetime.combine(dose.expected_date, scheduled_time)

        should_send = False

        for offset in cfg.notify_minutes:
            target_dt = scheduled_dt + timedelta(minutes=offset)
            diff_seconds = (target_dt - now).total_seconds()

            # Trigger exactly once for each target time window
            if 0 <= diff_seconds < interval_seconds:
                should_send = True
                break

        if not should_send:
            continue

        email = user_email.get(dose.user_id)
        if not email:
            continue

        subject = "DineDose Medication Reminder"
        body = build_email_body(dose, user_name.get(dose.user_id, ""))

        send_email_ses(email, subject, body)


# ----------------------------------------------------
# Email body
# ----------------------------------------------------

def build_email_body(dose: ScheduledDose, user_name: str) -> str:
    scheduled_time = dose.expected_time or dt_time(9, 0)
    scheduled_dt = datetime.combine(dose.expected_date, scheduled_time)
    scheduled_str = scheduled_dt.strftime("%Y-%m-%d %H:%M")

    drug_name = dose.drug_name or "your medication"
    display_name = user_name or "User"

    dosage_part = ""
    if dose.dosage and dose.unit:
        dosage_part = f" (Dosage: {dose.dosage} {dose.unit})"

    return (
        f"Hello {display_name},\n\n"
        f"This is your reminder from DineDose:\n"
        f"- Medication: {drug_name}{dosage_part}\n"
        f"- Scheduled time: {scheduled_str}\n\n"
        f"Please confirm whether you have taken this dose.\n"
        f"If you have already taken it, you may ignore this email.\n\n"
        f"— DineDose Team"
    )