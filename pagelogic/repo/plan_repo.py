from config import mydb


# class plan:
#     def __init__(self, plan_id, patient_id, doctor_id, name, description):
#         self.plan_id = plan_id
#         self.patient_id = patient_id
#         self.doctor_id = doctor_id
#         self.name = name
#         self.description = description


def main():
    get_plan_by_id(1)

def get_plan_by_id(plan_id): #return an instance of plan

    conn = mydb()
    cur = conn.cursor()      # ✅ 返回字典格式
    print("Querying for:", plan_id)
    query = "select * from plan where id = %s" 
    cur.execute(query, (plan_id,))
    result = cur.fetchone()                 #获取这个query的结果
    print(result)
    cur.close()
    conn.close()
    return result

def get_all_plan_items_by_plan_id(plan_id): #return a list of plan_item
    pass
 
def get_plan_item_rule_by_plan_item_id(plan_item_id): #return an instance of plan_item_rule
    pass