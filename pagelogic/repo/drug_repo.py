from dataclasses import dataclass, asdict
from typing import List, Optional
from config import mydb


# =============== dataclass model ===============

@dataclass
class drug:
    id: int
    product_ndc: str
    brand_name: str
    brand_name_base: str
    generic_name: str
    labeler_name: str
    dosage_form: str
    route: str
    marketing_category: str
    product_type: str
    application_number: str
    marketing_start_date: str   # DB 里是 varchar(20)
    listing_expiration_date: str
    finished: bool

    def to_dict(self) -> dict:
        # 这里所有字段都是基本类型，直接 asdict 即可
        return asdict(self)

    def __str__(self) -> str:
        return (
            f"Drug(id={self.id}, "
            f"generic_name='{self.generic_name}', "
            f"brand_name='{self.brand_name}', "
            f"dosage_form='{self.dosage_form}', "
            f"route='{self.route}')"
        )


# =============== 内部小工具 ===============

def _row_to_drug(cur, row) -> drug:
    """把一行 tuple 转成 drug dataclass。"""
    columns = [desc[0] for desc in cur.description]
    rd = dict(zip(columns, row))

    return drug(
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
        finished=rd["finished"],
    )


# =============== repo functions ===============

def get_drug_by_id(id: int) -> Optional[drug]:
    """
    按主键 id 拿一条 drug；不存在则返回 None。
    """
    conn = mydb()
    cur = conn.cursor()

    query = """
        SELECT
            id, product_ndc, brand_name, brand_name_base,
            generic_name, labeler_name, dosage_form, route,
            marketing_category, product_type, application_number,
            marketing_start_date, listing_expiration_date, finished
        FROM drugs
        WHERE id = %s
    """

    cur.execute(query, (id,))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return None

    d = _row_to_drug(cur, row)

    cur.close()
    conn.close()
    return d


def get_drugs_by_ids(ids: List[int]) -> List[drug]:
    """
    按一组 id 查询多条 drug，返回 drug dataclass 列表。
    """
    if not ids:
        return []

    conn = mydb()
    cur = conn.cursor()

    print("Querying for drug ids:", ids)

    placeholders = ",".join(["%s"] * len(ids))
    query = f"""
        SELECT
            id, product_ndc, brand_name, brand_name_base,
            generic_name, labeler_name, dosage_form, route,
            marketing_category, product_type, application_number,
            marketing_start_date, listing_expiration_date, finished
        FROM drugs
        WHERE id IN ({placeholders})
    """

    cur.execute(query, tuple(ids))
    rows = cur.fetchall()

    drugs: List[drug] = []
    for row in rows:
        d = _row_to_drug(cur, row)
        drugs.append(d)

    cur.close()
    conn.close()
    return drugs