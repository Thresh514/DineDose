from dataclasses import dataclass, asdict
from typing import List, Optional
from config import mydb

foods = []

@dataclass
class food:
    id: int
    name: str
    category: str
    calories: float
    protein: float
    fat: float
    carbohydrates: float

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
    
def _row_to_food(cur, row) -> food:
    """Convert a database row to a food dataclass."""
    columns = [desc[0] for desc in cur.description]
    rd = dict(zip(columns, row))

    return food(
        id=rd["id"],
        name=rd["name"],
        category=rd["category"],
        calories=rd["calories"],
        protein=rd["protein"],
        fat=rd["fat"],
        carbohydrates=rd["carbohydrates"]
    )

def get_foods():
    conn = mydb()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM foods")
        rows = cur.fetchall()
        foods = [_row_to_food(cur, row) for row in rows]
        print(foods[:10], foods[-10:])
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

def get_foods_by_ids_locally(ids: List[int]) -> List[food]:
    return [f for f in foods if f.id in ids]