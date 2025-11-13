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

    def to_dict(self):
        return {
            "id": self.id,
            "plan_item_id": self.plan_item_id,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "repeat_type": self.repeat_type,
            "interval_value": self.interval_value,
            "mon": self.mon,
            "tue": self.tue,
            "wed": self.wed,
            "thu": self.thu,
            "fri": self.fri,
            "sat": self.sat,
            "sun": self.sun,
            "times": self.times
        }
        

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
    plan_obj = plan(
        id=result["id"],
        patient_id=result["patient_id"],
        doctor_id=result["doctor_id"],
        patient_name=result["patient_name"],
        doctor_name=result["doctor_name"],
        name=result["name"],
        plan_items=None   
    )
    return plan_obj

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

    plan_item_list = []
    for row in result:
        item_obj = plan_item(
            id=row["id"],
            plan_id=row["plan_id"],
            drug_id=row["drug_id"],
            drug_name=row["drug_name"],
            dosage=row["dosage"],
            unit=row["unit"],
            amount_literal=row["amount_literal"],
            note=row["note"],
            date=None,     # DB 查询不含 date → 固定为 None
            time=None,     # DB 查询不含 time → 固定为 None
            plan_item_rule=None  
        )
        plan_item_list.append(item_obj)
    return plan_item_list
 
def get_plan_item_rule_by_plan_item_id(plan_item_id): #return an instance of plan_item_rule
    conn = mydb()
    cur = conn.cursor()
    query = "select * from plan_item_rule where plan_item_id = %s"
    cur.execute(query, (plan_item_id,))
    result = cur.fetchall()   
    cur.close()
    conn.close()
    return result

#通过一个plan_id, 获取每个plan_item，以及其对应的plan_item_rule
# 具体来说，获取plan_item_id to plan_item_rule 这样一个dictionary:
#Key: plan_item.id
#Value: 对应的 plan_item_rules
def get_plan_item_rules_by_plan_id(plan_id):
    conn = mydb()
    cur = conn.cursor()   # tuple cursor

    query = """
        SELECT 
            pi.id AS plan_item_id,
            pir.id AS rule_id,
            pir.plan_item_id AS rule_plan_item_id,
            pir.start_date AS rule_start_date,
            pir.end_date AS rule_end_date,
            pir.repeat_type AS rule_repeat_type,
            pir.interval_value AS rule_interval_value,
            pir.mon AS rule_mon,
            pir.tue AS rule_tue,
            pir.wed AS rule_wed,
            pir.thu AS rule_thu,
            pir.fri AS rule_fri,
            pir.sat AS rule_sat,
            pir.sun AS rule_sun,
            pir.times AS rule_times
        FROM plan_item pi
        LEFT JOIN plan_item_rule pir
        ON pi.id = pir.plan_item_id
        WHERE pi.plan_id = %s;
    """

    cur.execute(query, (plan_id,))
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    cur.close()
    conn.close()

    item_id_to_rules = {}

    for row in rows:
        row_dict = dict(zip(columns, row))

        item_id = row_dict["plan_item_id"]

        rule_obj = None
        if row_dict["rule_id"] is not None:  # 有 rule 才构建对象
            rule_obj = plan_item_rule(
                id=row_dict["rule_id"],
                plan_item_id=row_dict["rule_plan_item_id"],
                start_date=row_dict["rule_start_date"],
                end_date=row_dict["rule_end_date"],
                repeat_type=row_dict["rule_repeat_type"],
                interval_value=row_dict["rule_interval_value"],
                mon=row_dict["rule_mon"],
                tue=row_dict["rule_tue"],
                wed=row_dict["rule_wed"],
                thu=row_dict["rule_thu"],
                fri=row_dict["rule_fri"],
                sat=row_dict["rule_sat"],
                sun=row_dict["rule_sun"],
                times=row_dict["rule_times"]
            )

        item_id_to_rules[item_id] = rule_obj

    return item_id_to_rules