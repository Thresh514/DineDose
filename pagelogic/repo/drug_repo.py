from config import mydb

class drug:
    def __init__(self,
                 id, 
                 product_ndc,
                 brand_name,
                 brand_name_base,  
                generic_name,
                labeler_name,
                dosage_form,
                route,
                marketing_category,
                product_type,
                application_number, 
                marketing_start_date,
                listing_expiration_date,
                finished):
            self.id = id
            self.product_ndc = product_ndc
            self.brand_name = brand_name
            self.brand_name_base = brand_name_base
            self.generic_name = generic_name
            self.labeler_name = labeler_name
            self.dosage_form = dosage_form
            self.route = route
            self.marketing_category = marketing_category
            self.product_type = product_type
            self.application_number = application_number
            self.marketing_start_date = marketing_start_date
            self.listing_expiration_date = listing_expiration_date
            self.finished = finished


def get_drug_by_id(id):
    pass

def get_drugs_by_ids(ids):
    conn = mydb()
    cur = conn.cursor()      # ✅ 返回字典格式
    print("Querying for:", ids)
    query = "select * from drugs where id = %s" 
    cur.execute(query, (ids,))
    result = cur.fetchone()                 #获取这个query的结果
    print(result)
    cur.close()
    conn.close()
    return result






