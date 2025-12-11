import pytest
from flask import Flask
import pagelogic.bp.food_bp as food_bp


# -------------------------------
#   Dummy Model
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
    monkeypatch.setattr(
        food_bp.food_repo,
        "get_food_by_id_locally",
        lambda x: None
    )

    r = client.get("/get_foods?id=5")
    assert r.status_code == 404
    assert r.get_json() == []


def test_get_foods_by_id_success(client, monkeypatch):
    monkeypatch.setattr(
        food_bp.food_repo,
        "get_food_by_id_locally",
        lambda x: DummyFood(id=x, desc="apple")
    )

    r = client.get("/get_foods?id=10")
    assert r.status_code == 200
    assert r.get_json()[0]["id"] == 10
    assert r.get_json()[0]["description"] == "apple"


def test_get_foods_by_name_not_found(client, monkeypatch):
    monkeypatch.setattr(
        food_bp.food_repo,
        "get_foods_by_name_locally",
        lambda x: []
    )

    r = client.get("/get_foods?name=banana")
    assert r.status_code == 404
    assert r.get_json() == []


def test_get_foods_by_name_success(client, monkeypatch):
    foods = [
        DummyFood(id=1, desc="banana"),
        DummyFood(id=2, desc="banana bread")
    ]

    monkeypatch.setattr(
        food_bp.food_repo,
        "get_foods_by_name_locally",
        lambda x: foods
    )

    r = client.get("/get_foods?name=banana")
    assert r.status_code == 200
    data = r.get_json()
    assert len(data) == 2
    assert data[0]["description"] == "banana"


# -------------------------------
#   /get_sample_foods
# -------------------------------

def test_get_sample_foods(client, monkeypatch):
    monkeypatch.setattr(
        food_bp.food_repo,
        "get_sample_foods_locally",
        lambda: [DummyFood(id=3, desc="sample")]
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
        "search_foods_by_keywords_locally",
        lambda names: []
    )

    r = client.get("/search_food?name=banana juice")
    assert r.status_code == 404
    assert r.get_json() == []


def test_search_food_success(client, monkeypatch):
    foods = [DummyFood(id=1, desc="banana juice")]

    monkeypatch.setattr(
        food_bp.food_repo,
        "search_foods_by_keywords_locally",
        lambda names: foods
    )

    r = client.get("/search_food?name=banana juice")
    assert r.status_code == 200
    data = r.get_json()
    assert data[0]["description"] == "banana juice"


    # -------------------------------
#   /get-food-image
# -------------------------------

def test_get_food_image_missing_param(client):
    r = client.get("/get-food-image")
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_get_food_image_no_api_key(client, monkeypatch):
    # Simulate no API key configured
    monkeypatch.setattr(food_bp, "BING_IMAGES_API_KEY", "")

    r = client.get("/get-food-image?food_name=banana")
    data = r.get_json()

    assert r.status_code == 200
    assert data["image_url"] is None
    assert data["source"] == "placeholder"


def test_get_food_image_success_first_try(client, monkeypatch):
    # Fake API key
    monkeypatch.setattr(food_bp, "BING_IMAGES_API_KEY", "FAKE")

    # Mock API class
    class FakeAPI:
        def __init__(self, key):
            self.key = key

        def search_food_image(self, name):
            if name == "banana":
                return {
                    "image_url": "http://img.com/banana.jpg",
                    "title": "Banana",
                    "source": "bing"
                }
            return None

    monkeypatch.setattr(food_bp, "GoogleImagesAPI", FakeAPI)

    r = client.get("/get-food-image?food_name=banana")
    data = r.get_json()

    assert r.status_code == 200
    assert data["image_url"] == "http://img.com/banana.jpg"
    assert data["source"] == "bing"


def test_get_food_image_fallback_search_success(client, monkeypatch):
    monkeypatch.setattr(food_bp, "BING_IMAGES_API_KEY", "FAKE")

    # mock API search behavior:
    # first call returns None → fallback should succeed
    class FakeAPI:
        def __init__(self, key):
            self.key = key
            self.calls = []

        def search_food_image(self, name):
            self.calls.append(name)
            if name in ["banana smoothie", "banana", "banana smoothie"]:
                return {
                    "image_url": "http://img.com/smoothie.jpg",
                    "title": "Banana Smoothie",
                    "source": "bing"
                }
            return None

    monkeypatch.setattr(food_bp, "GoogleImagesAPI", FakeAPI)

    r = client.get("/get-food-image?food_name=banana smoothie")
    data = r.get_json()

    assert r.status_code == 200
    assert data["image_url"] == "http://img.com/smoothie.jpg"
    assert data["title"] == "Banana Smoothie"


def test_get_food_image_no_result_any_search(client, monkeypatch):
    monkeypatch.setattr(food_bp, "BING_IMAGES_API_KEY", "FAKE")

    # All searches fail
    class FakeAPI:
        def __init__(self, key):
            pass

        def search_food_image(self, name):
            return None

    monkeypatch.setattr(food_bp, "GoogleImagesAPI", FakeAPI)

    r = client.get("/get-food-image?food_name=unknown food item")
    data = r.get_json()

    assert r.status_code == 200
    assert data["image_url"] is None
    assert "No image found" in data["title"]