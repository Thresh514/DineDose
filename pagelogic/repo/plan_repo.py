from config import mydb



class plan:
    def __init__(self, 
               id, 
               patient_id, 
               doctor_id, 
               patient_name, 
               doctor_name, 
               name, 
               plan_items, #如果从数据库返回，此项为NULL
                ):
        self.id = id
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.patient_name = patient_name
        self.doctor_name = doctor_name
        self.name = name
        self.plan_items = plan_items


#返回给前端的struct
class plan_item:
    def __init__(
                self, 
                id, 
                plan_id, 
                drug_id, 
                drug_name, #如果从数据库返回，此项为NULL
                dosage, 
                unit, 
                amount_literal, 
                note,
                date, #如果从数据库返回，此项为NULL
                time, #如果从数据库返回，此项为NULL
                plan_item_rule #如果从数据库返回，此项为NULL
                ):
        self.id = id
        self.plan_id = plan_id
        self.drug_id = drug_id
        self.drug_name = drug_name
        self.dosage = dosage
        self.unit = unit
        self.amount_literal = amount_literal
        self.note = note
        self.date = date
        self.time = time
        self.plan_item_rule = plan_item_rule

class plan_item_rule:
    def __init__(self, 
                 id, 
                 plan_item_id, 
                 start_date, 
                 end_date, 
                 repeat_type,  
                 #'ONCE', 'DAILY', 'WEEKLY', 'PRN'
                 #ONCE means only need to type in start_date and times
                 #DAILY means repeat daily, fill in interval value and times
                 #WEEKLY means repeat according to specified mon tue...sun flags; also need to fill in times
                 #PRN means repeat according only
                 interval_value, #间隔多少 如 repeat_type = DAILY 时, 1表示每天一次
                 mon, 
                 tue, 
                 wed, 
                 thu, 
                 fri, 
                 sat, 
                 sun, 
                 times):
        self.id = id
        self.plan_item_id = plan_item_id
        self.start_date = start_date
        self.end_date = end_date
        self.repeat_type = repeat_type
        self.interval_value =  interval_value
        self.mon = mon
        self.tue = tue 
        self.wed = wed
        self.thu = thu
        self.fri = fri 
        self.sat = sat
        self.sun = sun
        self.times = times
        

def get_plan_by_id(plan_id): #return an instance of plan by plan_id

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
    conn = mydb()
    cur = conn.cursor()      # ✅ 返回字典格式
    print("Querying for:", plan_id)
    query = "select * from plan_item where plan_id = %s" 
    cur.execute(query, (plan_id,))
    result = cur.fetchall()                 #获取这个query的结果
    print(result)
    cur.close()
    conn.close()
    return result
 
def get_plan_item_rule_by_plan_item_id(plan_item_id): #return an instance of plan_item_rule
    pass

#通过一个plan_id, 获取每个plan_item，以及其对应的plan_item_rule
# 具体来说，获取plan_item_id to plan_item_rule 这样一个dictionary:
#Key: plan_item.id
#Value: 对应的 plan_item_rules
def get_plan_item_rules_by_plan_id(plan_id):
    #plan_id -> 所有对应的plan_items
    #plan_items ->各自对应的plan_item_rule
    
    item_id_to_rules = dict()

    return item_id_to_rules
