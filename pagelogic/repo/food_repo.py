from dataclasses import dataclass, asdict
import time
from typing import List, Optional
from unicodedata import name
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
#     agricultural_acquisi
# branded_food        
# experimental_food   
# foundation_food     
# market_acquistion   
# sample_food         
# sr_legacy_food      
# sub_sample_food     
# survey_fndds_food   
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
            f"carbohydrates={self.carbonhydrate})"
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
    global foods
    conn = mydb()
    cur = conn.cursor()


    try:
        sql_message = "SELECT * FROM foods"
        if config.FLASK_ENV == "dev":
            sql_message += " LIMIT 100"

        cur.execute(sql_message)
        
        rows = cur.fetchall()
        foods = [_row_to_food(cur, row) for row in rows]
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
    res = []
    for food in foods:
        if name in food.description:
            res.append(food)
    return res


def get_sample_foods_locally() -> List[food]:
    return foods[:100]

# Retrieve foods whose descriptions contain all the provided names (case-insensitive)
def search_foods_by_keywords_locally(names: List[str]) -> List[food]:
    if not names or all(name == "" for name in names):
        return foods[:100]  # Return first 100 foods as default if name is empty
    
    names = [name.lower() for name in names]
    res = []
    for food in foods:
        if all(name in food.description.lower() for name in names):
            res.append(food)

    #decrease priority for foods with data_type of "branded_food"
    return sorted(res, key=lambda x: (x.data_type == "branded_food", len(x.description)))[:100]

def get_foods_by_ids_locally(ids: List[int]) -> List[food]:
    return [f for f in foods if f.id in ids]