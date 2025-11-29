from datetime import datetime, timezone, timezone
from pagelogic.repo import user_notification_repo, user_repo
from pagelogic.repo.drug_record_repo import drug_record
from pagelogic.repo.user_repo import User
from utils.emailsender import send_email_ses

def get_plan_items_expiring_within(days: int) -> list:

    #get all users' id
    #for each user id:
        #plan_service.get_user_plan(id, now, now + days)
    
    #聚合所有plan_items

    plan_items = []
    start_date = date.today()
    end_date = start_date + timedelta(days=days)
    user_ids = user_repo.get_all_users_ids()
    for user_id in user_ids:
        user_plan_items = plan_service.get_user_plan_items_by_date_range(
            user_id=user_id,
            start=start_date,
            end=end_date
        )
        plan_items.extend(user_plan_items)

    return plan_items

    


def notify_jobs():
    plan_items = get_plan_items_expiring_within(1)
    logging.info(f"Found {len(plan_items)} plan items expiring within 1 day.")
    #[]drug_records<-获取plan item对应records情况;
    #要在repo.drug_record_repo.py写一个get_recent_completed_records(days) -> list[drug_record]的函数
    #根据expected time和expected date判断


    not_found_drug_records = []
    recent_drug_records = drug_record_repo.get_recent_completed_drug_records(7)
    for plan_item in plan_items:
        #check if there's a drug_record matching this plan_item in recent_drug_records
        found = False
        for record in recent_drug_records:
            if (record.plan_item_id == plan_item.id and
                record.expected_date == plan_item.expected_date and
                record.expected_time == plan_item.expected_time):
                found = True
                break
        if not found:
            not_found_drug_records.append(plan_item)
    logging.info(f"Found {len(not_found_drug_records)} missed plan items needing notification.")
    send_notifications(not_found_drug_records)


def send_notifications(missed_plan_items: List[drug_record]) -> None:
    """
    Iterate through all missed drug plan items and send email notifications
    based on each user's notification settings.
    """
    if not missed_plan_items:
        return

    # 1. Collect user IDs involved in these missed items
    user_ids = {item.user_id for item in missed_plan_items}

    # 2. Fetch user profiles (email / name)
    users = user_repo.get_users_by_ids(list(user_ids))
    user_id_to_email = {user.id: user.email for user in users}

    # Prefer 'name', fallback to 'username', fallback to ""
    user_id_to_name = {
        user.id: user.username
        for user in users
    }

    # 3. Fetch notification settings for all users
    # Expected format: { user_id: NotificationConfig }
    user_id_to_config = user_notification_repo.get_notification_configs_by_user_ids(
        list(user_ids)
    )

    # Current timestamp for calculating time offset
    now_utc = datetime.now(timezone.utc)

    # 4. Evaluate each missed item
    for missed_item in missed_plan_items:
        cfg = user_id_to_config.get(missed_item.user_id)
        if cfg is None:
            continue

        # Skip if notifications or email notifications are disabled
        if not cfg.enabled or not cfg.email_enabled:
            continue

        # Determine the time difference (in minutes)
        plan_time = missed_item.plan_time  # should be datetime

        if plan_time.tzinfo is None:
            # naive datetime -> compare using naive current time
            diff_minutes = round(
                (plan_time - now_utc.replace(tzinfo=None)).total_seconds() / 60
            )
        else:
            diff_minutes = round(
                (plan_time - now_utc).total_seconds() / 60
            )

        # Trigger notification if the offset matches user settings
        if diff_minutes not in cfg.notify_minutes:
            continue

        # Send the e-mail
        email = user_id_to_email.get(missed_item.user_id)
        if not email:
            continue

        user_name = user_id_to_name.get(missed_item.user_id, "")
        subject = "DineDose Medication Reminder"

        body = build_email_body(missed_item, user_name)
        send_email_ses(email, subject, body)

    return


def build_email_body(missed_item: drug_record, user_name: str) -> str:
    """
    Build the email content for the medication reminder.
    """

    # Format time nicely
    if missed_item.plan_time.tzinfo:
        plan_time_str = missed_item.plan_time.astimezone().strftime("%Y-%m-%d %H:%M")
    else:
        plan_time_str = missed_item.plan_time.strftime("%Y-%m-%d %H:%M")

    # Handle dosage field (if exists)
    dosage = getattr(missed_item, "dosage", None)
    dosage_part = f" (Dosage: {dosage})" if dosage else ""

    # Determine drug name field (adapt based on your actual drug_record model)
    drug_name = getattr(missed_item, "drug_name", None)
    if drug_name is None:
        drug_name = getattr(missed_item, "generic_name", "Unknown medication")

    display_name = user_name or "User"

    body = (
        f"Hello {display_name},\n\n"
        f"This is a medication reminder from DineDose:\n"
        f"- Medication: {drug_name}{dosage_part}\n"
        f"- Scheduled time: {plan_time_str}\n\n"
        f"Please confirm whether you have taken this medication as instructed.\n"
        f"If you have already taken it, you can safely ignore this email.\n\n"
        f"To adjust or disable medication reminders, please visit your "
        f"DineDose Notification Settings.\n\n"
        f"— DineDose Team"
    )

    return body