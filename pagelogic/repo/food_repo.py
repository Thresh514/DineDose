from dataclasses import dataclass, asdict
import time
from typing import List, Optional
from config import mydb
import config

foods = []

@dataclass
class food:
    id: int
    fdc_id: int
    description: str
    fat: float
    carbonhydrate: float
    calories: float
    data_type: str
    food_category_id: str
    publication_date: str
    food_category_num: int

    def to_dict(self) -> dict:
        return asdict(self)

    def __str__(self) -> str:
        return (
            f"Food(id={self.id}, "
            f"name='{self.name}', "
            f"category='{self.category}', "
            f"calories={self.calories}, "
            f"protein={self.protein}, "
            f"fat={self.fat}, "
            f"carbohydrates={self.carbohydrates})"
        )
    
def _row_to_food(cur, row):
    columns = [desc[0] for desc in cur.description]
    rd = dict(zip(columns, row))

    return food(
        id=rd["id"],
        fdc_id=rd["fdc_id"],
        description=rd["description"],
        fat=rd["fat"],
        carbonhydrate=rd["carbonhydrate"],
        calories=rd["calories"],
        data_type=rd["data_type"],
        food_category_id=rd["food_category_id"],
        publication_date=rd["publication_date"],
        food_category_num=rd["food_category_num"],
    )


def get_foods():
    print("star loading foods from DB...", time.time())
    global foods
    conn = mydb()
    cur = conn.cursor()


    try:
        sql_message = "SELECT * FROM foods"
        if config.FLASK_ENV == "dev":
            print("get_foods are running in DEV mode, so only top 100 food will be loaded into local memory:")
            sql_message += " LIMIT 100"

        cur.execute(sql_message)
        
        rows = cur.fetchall()
        foods = [_row_to_food(cur, row) for row in rows]
        print(foods[:10], foods[-10:])
        print("finished loading foods from DB.", time.time())
        return foods
    finally:
        cur.close()
        conn.close()

def get_food_by_id(id: int) -> Optional[food]:
    for f in foods:
        if f.id == id:
            return f
    return None

def get_foods_by_ids(ids: List[int]) -> List[food]:
    return [f for f in foods if f.id in ids]

def get_foods_locally() -> List[food]:
    return foods

def get_food_by_id_locally(id: int) -> Optional[food]:
    for f in foods:
        if f.id == id:
            return f
    return None

def get_foods_by_name_locally(name: str) -> Optional[food]:
    print("get_foods_by_name_locally: name = ", name)
    res = []
    for food in foods:
        if name in food.description:
            res.append(food)
    print(res)
    return res

def get_foods_by_ids_locally(ids: List[int]) -> List[food]:
    return [f for f in foods if f.id in ids]