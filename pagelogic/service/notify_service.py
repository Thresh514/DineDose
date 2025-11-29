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

    print(f"[STEP1] Time window: {window_start}  →  {window_end}")

    # 1) Fetch all users
    users = user_repo.get_all_users()
    user_ids = [user.id for user in users]

    print(f"[STEP1] Total users found: {len(users)}")
    print(f"[STEP1] User IDs: {user_ids}")

    # 2) Get plans for users
    plans = plan_repo.get_plans_by_user_ids(user_ids)

    print(f"[STEP1] Total plans found: {len(plans)}")
    print(f"[STEP1] Plans belong to users: {list(plans.keys())}")

    # Filter users with a plan
    users_with_plans = [u for u in users if u.id in plans]
    print(f"[STEP1] Users with a plan: {[u.id for u in users_with_plans]}")

    scheduled: List[ScheduledDose] = []

    # 3) Expand plan items into concrete doses
    for user in users_with_plans:
        print(f"\n[STEP1] Expanding plan for user_id={user.id}")

        plan = plan_service.get_user_plan(
            id=user.id,
            from_when=window_start,
            to_when=window_end,
        )

        if not plan:
            print(f"[STEP1]   No plan returned for user {user.id}")
            continue
        if not plan.plan_items:
            print(f"[STEP1]   Plan has no items for user {user.id}")
            continue

        print(f"[STEP1]   Expanded plan_items count={len(plan.plan_items)}")

        for item in plan.plan_items:
            if item.date is None:
                print(f"[STEP1]   Skipping PRN/no-date item: plan_item_id={item.id}")
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
            scheduled.append(sd)

    print(f"\n[STEP1] TOTAL scheduled doses collected: {len(scheduled)}")
    return scheduled


# =========================
# Step 2: diff scheduled vs completed
# =========================

def find_missed_doses(
    scheduled: List[ScheduledDose],
    recent_records: List[drug_record_repo.drug_record],
) -> List[ScheduledDose]:

    print("\n==================== STEP 2: Compare scheduled vs completed ====================")
    print(f"[STEP2] Scheduled count: {len(scheduled)}")
    print(f"[STEP2] Completed records count: {len(recent_records)}")

    completed_keys = set()

    for record in recent_records:
        key = (
            record.user_id,
            record.plan_item_id,
            record.expected_date,
            record.expected_time,
        )
        completed_keys.add(key)
        print(f"[STEP2] Completed record: {key}")

    missed = []

    for dose in scheduled:
        key = (
            dose.user_id,
            dose.plan_item_id,
            dose.expected_date,
            dose.expected_time,
        )
        if key not in completed_keys:
            print(f"[STEP2] MISSED dose: {key}")
            missed.append(dose)
        else:
            print(f"[STEP2] OK dose (taken): {key}")

    print(f"\n[STEP2] TOTAL missed doses: {len(missed)}")
    return missed


# =========================
# Step 3: main entry
# =========================

def notify_jobs(days: int = 1, interval: int = 5*60) -> None:
    print("\n==================== NOTIFY JOB START ====================")
    print(f"[MAIN] Running notify_jobs(days={days})")

    # Step 1
    scheduled_doses = get_scheduled_doses_within(days)
    print(f"[MAIN] Scheduled doses count: {len(scheduled_doses)}")

    # Step 2
    recent_records = drug_record_repo.get_recent_completed_drug_records(days)
    print(f"[MAIN] Completed drug records count: {len(recent_records)}")

    # Step 3
    missed_doses = find_missed_doses(scheduled_doses, recent_records)
    print(f"[MAIN] Missed doses count: {len(missed_doses)}")

    # Step 4
    print(f"[MAIN] Sending notifications ...")
    send_notifications(missed_doses, interval)

    print("==================== NOTIFY JOB END ====================\n")


# =========================
# Step 4: send notifications
# =========================
#interval: seconds between checks
def send_notifications(missed_doses: List[ScheduledDose], interval: int) -> None:
    print("\n==================== STEP 4: Sending notifications ====================")

    if not missed_doses:
        print("[STEP4] No missed doses, skipping email.")
        return

    user_ids = {dose.user_id for dose in missed_doses}
    print(f"[STEP4] Users with missed doses: {user_ids}")

    users = user_repo.get_users_by_ids(list(user_ids))
    user_id_to_email = {u.id: u.email for u in users}
    user_id_to_name = {u.id: u.username for u in users}

    print("[STEP4] Loaded user profiles:")
    for uid in user_id_to_email:
        print(f"  user_id={uid}, email={user_id_to_email[uid]}")

    user_id_to_config = user_notification_repo.get_notification_configs_by_user_ids(
        list(user_ids)
    )
    print("[STEP4] Loaded notification configs:")
    for uid, cfg in user_id_to_config.items():
        print(f"  user_id={uid}, notify_minutes={cfg.notify_minutes}, enabled={cfg.enabled}")

    now_utc = NOW


    for dose in missed_doses:
        print(f"\n[STEP4] Evaluating dose → {dose}")

        cfg = user_id_to_config.get(dose.user_id)
        if not cfg:
            print("[STEP4]   No notification config, skipping")
            continue
        if not cfg.enabled or not cfg.email_enabled:
            print("[STEP4]   Notification disabled, skipping")
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

        print(f"[STEP4]   Time diff (minutes): {diff_minutes}, now_utc={now_utc}")

        if diff_minutes not in cfg.notify_minutes:
            print("[STEP4]   Time does not match notify_minutes, skipping")
            continue

        email = user_id_to_email.get(dose.user_id)
        if not email:
            print("[STEP4]   Cannot send email (email missing)")
            continue

        user_name = user_id_to_name.get(dose.user_id, "")
        subject = "DineDose Medication Reminder"
        body = build_email_body(dose, user_name)

        print(f"[STEP4]   Sending email to {email}")
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