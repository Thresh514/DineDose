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

    def to_dict(self):
        return {
            "id": self.id,
            "product_ndc": self.product_ndc,
            "brand_name": self.brand_name,
            "brand_name_base": self.brand_name_base,
            "generic_name": self.generic_name,
            "labeler_name": self.labeler_name,
            "dosage_form": self.dosage_form,
            "route": self.route,
            "marketing_category": self.marketing_category,
            "product_type": self.product_type,
            "application_number": self.application_number,
            "marketing_start_date": self.marketing_start_date,
            "listing_expiration_date": self.listing_expiration_date,
            "finished": self.finished
        }

def get_drug_by_id(id):
    pass

def get_drugs_by_ids(ids):
    if not ids:
        return []

    conn = mydb()
    cur = conn.cursor()  # 普通 cursor，没有 dict 功能

    print("Querying for drug ids:", ids)

    placeholders = ",".join(["%s"] * len(ids))
    query = f"SELECT * FROM drugs WHERE id IN ({placeholders})"

    cur.execute(query, tuple(ids))
    rows = cur.fetchall()

    # ⭐ 获取列名
    columns = [desc[0] for desc in cur.description]

    cur.close()
    conn.close()

    drugs = []
    for r in rows:
        # ⭐ 手动把 tuple → dict
        rd = dict(zip(columns, r))

        d = drug(
            id=rd["id"],
            product_ndc=rd["product_ndc"],
            brand_name=rd["brand_name"],
            brand_name_base=rd["brand_name_base"],
            generic_name=rd["generic_name"],
            labeler_name=rd["labeler_name"],
            dosage_form=rd["dosage_form"],
            route=rd["route"],
            marketing_category=rd["marketing_category"],
            product_type=rd["product_type"],
            application_number=rd["application_number"],
            marketing_start_date=rd["marketing_start_date"],
            listing_expiration_date=rd["listing_expiration_date"],
            finished=rd["finished"]
        )
        drugs.append(d)

    return drugs



