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
    """Mock mydb so get_foods() works fully."""
    def fake_mydb():
        columns = [
            ("id",), ("fdc_id",), ("description",), ("fat",),
            ("carbonhydrate",), ("calories",), ("data_type",),
            ("food_category_id",), ("publication_date",), ("food_category_num",)
        ]
        rows = [
            (1, 111, "Apple", 0.3, 14.0, 52, "foundation_food", "01", "2024-01-01", 1)
        ]
        return FakeConn(FakeCursor(columns, rows))

    monkeypatch.setattr(food_repo, "mydb", fake_mydb)


# ------------------------------------------------------------
# get_foods()
# ------------------------------------------------------------
def test_get_foods(mock_mydb):
    res = food_repo.get_foods()
    assert len(res) == 1
    assert res[0].description == "Apple"
    assert res[0].calories == 52


# ------------------------------------------------------------
# get_food_by_id_locally()
# ------------------------------------------------------------
def test_get_food_by_id_locally_found():
    food_repo.foods = [
        food_repo.food(1, 0, "Rice", 1, 2, 3, "x", "02", "2024", 7)
    ]
    r = food_repo.get_food_by_id_locally(1)
    assert r.description == "Rice"


def test_get_food_by_id_locally_not_found():
    food_repo.foods = []
    assert food_repo.get_food_by_id_locally(99) is None


# ------------------------------------------------------------
# get_foods_by_ids_locally()
# ------------------------------------------------------------
def test_get_foods_by_ids_locally():
    food_repo.foods = [
        food_repo.food(1, 0, "A", 1, 1, 1, "x", "02", "2024", 1),
        food_repo.food(2, 0, "B", 1, 1, 1, "x", "03", "2024", 1),
    ]
    res = food_repo.get_foods_by_ids_locally([1, 2])
    assert len(res) == 2


# ------------------------------------------------------------
# get_foods_by_name_locally()
# ------------------------------------------------------------
def test_get_foods_by_name_locally():
    food_repo.foods = [
        food_repo.food(1, 0, "Banana", 0, 0, 0, "x", "01", "2024", 1),
        food_repo.food(2, 0, "Banana Bread", 0, 0, 0, "x", "01", "2024", 1),
    ]
    res = food_repo.get_foods_by_name_locally("Banana")
    assert len(res) == 2


# ------------------------------------------------------------
# get_sample_foods_locally()
# ------------------------------------------------------------
def test_get_sample_foods_locally():
    food_repo.foods = [food_repo.food(i, 0, "X", 0, 0, 0, "x", "01", "2024", 1) for i in range(200)]
    res = food_repo.get_sample_foods_locally()
    assert len(res) == 100


# ------------------------------------------------------------
# search_foods_by_keywords_locally()
# ------------------------------------------------------------
def test_search_foods_by_keywords_locally_basic():
    food_repo.foods = [
        food_repo.food(1, 0, "Apple Pie", 0, 0, 0, "foundation_food", "01", "2024", 1),
        food_repo.food(2, 0, "Pie Apple", 0, 0, 0, "branded_food", "01", "2024", 1),
        food_repo.food(3, 0, "Banana Pie", 0, 0, 0, "foundation_food", "01", "2024", 1),
    ]
    res = food_repo.search_foods_by_keywords_locally(["apple"])
    # should include id 1 & 2, sorted → non-branded first
    assert res[0].id == 1


def test_search_foods_by_keywords_locally_empty():
    food_repo.foods = [food_repo.food(i, 0, f"F{i}", 0, 0, 0, "x", "01", "2024", 1) for i in range(150)]
    res = food_repo.search_foods_by_keywords_locally([])
    assert len(res) == 100  # default behavior


def test_search_foods_by_keywords_locally_multiple_words():
    food_repo.foods = [
        food_repo.food(1, 0, "Spicy Chicken Soup", 0, 0, 0, "foundation_food", "01", "2024", 1),
        food_repo.food(2, 0, "Chicken Soup", 0, 0, 0, "foundation_food", "01", "2024", 1),
        food_repo.food(3, 0, "Spicy Pork Soup", 0, 0, 0, "foundation_food", "01", "2024", 1),
    ]
    res = food_repo.search_foods_by_keywords_locally(["spicy", "soup"])
    assert len(res) == 2
    assert {f.id for f in res} == {1, 3}


# ------------------------------------------------------------
# get_foods_locally()
# ------------------------------------------------------------
def test_get_foods_locally():
    food_repo.foods = [food_repo.food(1, 0, "A", 0, 0, 0, "x", "01", "2024", 1)]
    assert len(food_repo.get_foods_locally()) == 1