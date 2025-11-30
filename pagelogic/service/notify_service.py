import logging
from dataclasses import dataclass
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
NOW = datetime.now()
#datetime.now(timezone.utc) 才是utc+0时间

def get_scheduled_doses_within(days: int) -> List[ScheduledDose]:
    print("\n==================== STEP 1: Collect scheduled doses ====================")
    NOW = datetime.now()
    
    window_start = NOW
    window_end = NOW + timedelta(days=days)


    # 1) Fetch all users
    users = user_repo.get_all_users()
    user_ids = [user.id for user in users]

    # 2) Get plans for users
    plans = plan_repo.get_plans_by_user_ids(user_ids)

    # Filter users with a plan
    users_with_plans = [u for u in users if u.id in plans]

    scheduled: List[ScheduledDose] = []

    # 3) Expand plan items into concrete doses
    for user in users_with_plans:

        plan = plan_service.get_user_plan(
            id=user.id,
            from_when=window_start,
            to_when=window_end,
        )

        if not plan:
            continue
        if not plan.plan_items:
            continue

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
            scheduled.append(sd)

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

def notify_jobs(days: int = 1, interval: int = 5*60) -> None:
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
#interval: seconds between checks
def send_notifications(missed_doses: List[ScheduledDose], interval: int) -> None:
    if not missed_doses:
        return

    user_ids = {dose.user_id for dose in missed_doses}

    users = user_repo.get_users_by_ids(list(user_ids))
    user_id_to_email = {u.id: u.email for u in users}
    user_id_to_name = {u.id: u.username for u in users}

    user_id_to_config = user_notification_repo.get_notification_configs_by_user_ids(
        list(user_ids)
    )
    now_utc = NOW


    for dose in missed_doses:
        cfg = user_id_to_config.get(dose.user_id)
        if not cfg:
            continue
        if not cfg.enabled or not cfg.email_enabled:
            continue

        # Construct datetime
        scheduled_time = dose.expected_time or dt_time(9, 0)
        scheduled_dt = datetime.combine(dose.expected_date, scheduled_time)

        if scheduled_dt.tzinfo is None:
            diff_minutes = round(
                (scheduled_dt - now_utc.replace(tzinfo=None)).total_seconds() / interval
            )
        else:
            diff_minutes = round((scheduled_dt - now_utc).total_seconds() / interval)

        if diff_minutes not in cfg.notify_minutes:
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