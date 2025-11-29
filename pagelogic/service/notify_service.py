import logging
from datetime import date, timedelta
from pagelogic.service import plan_service
from pagelogic.repo import drug_record_repo
import pagelogic.repo.plan_repo as plan_repo
import pagelogic.repo.user_repo as user_repo

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

def send_notifications(missed_plan_items: list):
    #给每个用户发邮件，告诉他有哪些plan items没完成
    pass