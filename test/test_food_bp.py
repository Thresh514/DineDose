import pytest
from flask import Flask
import pagelogic.bp.food_bp as food_bp


# -------------------------------
#   Fake model
# -------------------------------
class DummyFood:
    def __init__(self, id=1, desc="banana"):
        self.id = id
        self.description = desc

    def to_dict(self):
        return {"id": self.id, "description": self.description}


# -------------------------------
#   Flask app
# -------------------------------
@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(food_bp.food_bp)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


# -------------------------------
#   /get_foods
# -------------------------------

def test_get_foods_missing_params(client):
    r = client.get("/get_foods")
    assert r.status_code == 400


def test_get_foods_both_params(client):
    r = client.get("/get_foods?id=1&name=banana")
    assert r.status_code == 400


def test_get_foods_by_id_not_found(client, monkeypatch):
    monkeypatch.setattr(food_bp.food_repo,
                        "get_food_by_id_locally", lambda x: None)

    r = client.get("/get_foods?id=5")
    assert r.status_code == 404
    assert r.get_json() == []


def test_get_foods_by_id_success(client, monkeypatch):
    monkeypatch.setattr(food_bp.food_repo,
                        "get_food_by_id_locally",
                        lambda x: DummyFood(id=x, desc="apple"))

    r = client.get("/get_foods?id=10")
    assert r.status_code == 200
    assert r.get_json()[0]["id"] == 10


def test_get_foods_by_name_not_found(client, monkeypatch):
    monkeypatch.setattr(food_bp.food_repo,
                        "get_foods_by_name_locally", lambda x: [])

    r = client.get("/get_foods?name=banana")
    assert r.status_code == 404
    assert r.get_json() == []


def test_get_foods_by_name_success(client, monkeypatch):
    foods = [DummyFood(id=1, desc="banana"), DummyFood(id=2, desc="banana bread")]
    monkeypatch.setattr(food_bp.food_repo,
                        "get_foods_by_name_locally",
                        lambda x: foods)

    r = client.get("/get_foods?name=banana")
    data = r.get_json()
    assert r.status_code == 200
    assert len(data) == 2
    assert data[0]["description"] == "banana"


# -------------------------------
#   /get_sample_foods
# -------------------------------

def test_get_sample_foods(client, monkeypatch):
    monkeypatch.setattr(
        food_bp.food_repo,
        "get_foods_by_name_locally",
        lambda x: [DummyFood(id=3, desc="sample")]
    )

    r = client.get("/get_sample_foods")
    assert r.status_code == 200
    assert r.get_json()[0]["id"] == 3


# -------------------------------
#   /search_food
# -------------------------------

def test_search_food_missing_name(client):
    r = client.get("/search_food")
    assert r.status_code == 400


def test_search_food_name_too_short(client):
    r = client.get("/search_food?name=a")
    assert r.status_code == 400


def test_search_food_not_found(client, monkeypatch):
    monkeypatch.setattr(
        food_bp.food_repo,
        "get_foods_by_names_locally",
        lambda x: []
    )

    r = client.get("/search_food?name=banana juice")
    assert r.status_code == 404
    assert r.get_json() == []


def test_search_food_success(client, monkeypatch):
    foods = [DummyFood(id=1, desc="banana juice")]
    monkeypatch.setattr(
        food_bp.food_repo,
        "get_foods_by_names_locally",
        lambda x: foods
    )

    r = client.get("/search_food?name=banana juice")
    assert r.status_code == 200
    data = r.get_json()
    assert data[0]["description"] == "banana juice"
