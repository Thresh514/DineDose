def get_plan_items_expiring_within(days: int) -> list:
    #get all users' id
    #for each user id:
        #plan_service.get_user_plan(id, now, now + days)
    
    #聚合所有plan_items
    pass


def notify_jobs():
    plan_items =get_plan_items_expiring_within(1)


    []drug_records<-获取plan item对应records情况;
    #要在repo.drug_record_repo.py写一个get_recent_completed_records(days) -> list[drug_record]的函数
    #根据expected time和expected date判断

    []not_found_drug_records <-[]plan_item -[]drug_records
    # 


    send_notifications([]not_found_drug_records)

def send_notifications(missed_plan_items: list):
    #给每个用户发邮件，告诉他有哪些plan items没完成
    pass