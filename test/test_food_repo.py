import pytest
from pagelogic.repo import food_repo


# ---------- Fake DB cursor / connection ----------
class FakeCursor:
    def __init__(self, description, rows):
        self.description = description
        self.rows = rows
        self.index = 0

    def execute(self, sql):
        return True

    def fetchall(self):
        return self.rows

    def fetchone(self):
        if self.index >= len(self.rows):
            return None
        row = self.rows[self.index]
        self.index += 1
        return row

    def close(self):
        return True


class FakeConn:
    def __init__(self, cursor):
        self.cursor_obj = cursor

    def cursor(self):
        return self.cursor_obj

    def close(self):
        pass


@pytest.fixture
def mock_mydb(monkeypatch):
    """Patch mydb() to return fake DB connection."""
    def fake_mydb():
        columns = [
            ("id",), ("fdc_id",), ("description",), ("fat",),
            ("carbonhydrate",), ("calories",), ("data_type",),
            ("food_category_id",), ("publication_date",), ("food_category_num",)
        ]
        rows = [(1, 111, "Apple", 0.3, 14.0, 52, "Branded", "01", "2024-01-01", 1)]
        return FakeConn(FakeCursor(columns, rows))

    monkeypatch.setattr(food_repo, "mydb", fake_mydb)


# ------------------------------------------------------------
#                TEST get_foods
# ------------------------------------------------------------
def test_get_foods(mock_mydb):
    foods = food_repo.get_foods()
    assert len(foods) == 1
    assert foods[0].description == "Apple"
    assert foods[0].calories == 52


# ------------------------------------------------------------
#                TEST get_food_by_id_locally
# ------------------------------------------------------------
def test_get_food_by_id_locally():
    food_repo.foods = [
        food_repo.food(1, 0, "Rice", 1, 30, 130, "X", "02", "2024-01-02", 2)
    ]
    result = food_repo.get_food_by_id_locally(1)
    assert result.description == "Rice"


# ------------------------------------------------------------
#                TEST get_foods_by_ids_locally
# ------------------------------------------------------------
def test_get_foods_by_ids_locally():
    food_repo.foods = [
        food_repo.food(1, 0, "A", 0, 0, 0, "", "", "", 1),
        food_repo.food(2, 0, "B", 0, 0, 0, "", "", "", 1),
    ]
    res = food_repo.get_foods_by_ids_locally([1, 2])
    assert len(res) == 2


# ------------------------------------------------------------
#                TEST get_foods_by_name_locally
# ------------------------------------------------------------
def test_get_foods_by_name_locally():
    food_repo.foods = [
        food_repo.food(1, 0, "Banana", 0, 0, 0, "", "", "", 1),
        food_repo.food(2, 0, "Banana Bread", 0, 0, 0, "", "", "", 1),
    ]
    res = food_repo.get_foods_by_name_locally("Banana")
    assert len(res) == 2

def test_get_food_by_id_locally_not_found():
    food_repo.foods = []
    result = food_repo.get_food_by_id_locally(999)
    assert result is None


def test_get_foods_by_ids_locally_empty():
    food_repo.foods = []
    res = food_repo.get_foods_by_ids_locally([1])
    assert res == []


def test_get_foods_by_name_locally_not_found():
    food_repo.foods = [
        food_repo.food(1, 0, "Banana", 0, 0, 0, "", "", "", 1)
    ]
    res = food_repo.get_foods_by_name_locally("xxx")
    assert res == []


def test_get_foods_by_names_locally():
    food_repo.foods = [
        food_repo.food(1, 0, "Apple Pie", 0, 0, 0, "foundation_food", "", "", 1),
        food_repo.food(2, 0, "Apple Branded", 0, 0, 0, "branded_food", "", "", 1),
    ]
    res = food_repo.get_foods_by_names_locally(["apple"])
    assert len(res) == 2
    assert res[0].data_type == "foundation_food"


def test_get_foods_by_names_locally_empty_names():
    food_repo.foods = [food_repo.food(i, 0, f"Food {i}", 0, 0, 0, "", "", "", 1) for i in range(200)]
    res = food_repo.get_foods_by_names_locally([""])
    assert len(res) == 100


def test_get_foods_by_names_locally_no_match():
    food_repo.foods = [
        food_repo.food(1, 0, "Banana", 0, 0, 0, "", "", "", 1)
    ]
    res = food_repo.get_foods_by_names_locally(["xxx"])
    assert res == []


def test_get_foods_by_ids():
    food_repo.foods = [
        food_repo.food(1, 0, "AAA", 0, 0, 0, "", "", "", 1),
        food_repo.food(2, 0, "BBB", 0, 0, 0, "", "", "", 1)
    ]
    res = food_repo.get_foods_by_ids([1])
    assert len(res) == 1
    assert res[0].description == "AAA"


def test_get_foods_locally():
    food_repo.foods = [
        food_repo.food(1, 0, "A", 0, 0, 0, "", "", "", 1)
    ]
    res = food_repo.get_foods_locally()
    assert len(res) == 1
    assert res[0].id == 1





def test_get_food_by_id():
    food_repo.foods = [
        food_repo.food(1, 0, "Apple", 0, 0, 0, "", "", "", 1)
    ]
    result = food_repo.get_food_by_id(1)
    assert result.description == "Apple"

def test_row_to_food():
    columns = [
        ("id",), ("fdc_id",), ("description",), ("fat",),
        ("carbonhydrate",), ("calories",), ("data_type",),
        ("food_category_id",), ("publication_date",), ("food_category_num",)
    ]
    fake_cursor = type("C", (), {"description": columns})
    row = (1, 2, "Test", 1.1, 2.2, 3.3, "test_type", "01", "2024", 9)

    food_obj = food_repo._row_to_food(fake_cursor, row)
    assert food_obj.description == "Test"
    assert food_obj.food_category_num == 9

def test_get_foods_dev_env(monkeypatch, mock_mydb):
    monkeypatch.setattr(food_repo.config, "FLASK_ENV", "dev")
    foods = food_repo.get_foods()
    assert len(foods) == 1
