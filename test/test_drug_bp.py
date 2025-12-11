import pytest
from flask import Flask
from pagelogic.bp.drug_bp import drug_bp
from pagelogic.repo import drug_repo


# -----------------------------
# Flask app fixture
# -----------------------------
@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(drug_bp)
    app.secret_key = "test"
    return app


@pytest.fixture
def client(app):
    return app.test_client()


# ============================================================
# /get_drug
# ============================================================

def test_get_drug_missing_id(client):
    resp = client.get("/get_drug")
    assert resp.status_code == 400


def test_get_drug_not_found(client, monkeypatch):
    monkeypatch.setattr(drug_repo, "get_drug_by_id_locally", lambda x: None)
    resp = client.get("/get_drug?id=5")
    assert resp.status_code == 404


def test_get_drug_success(client, monkeypatch):
    class DummyDrug:
        def to_dict(self):
            return {"id": 1, "brand": "A"}

    monkeypatch.setattr(drug_repo, "get_drug_by_id_locally", lambda x: DummyDrug())

    resp = client.get("/get_drug?id=1")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == 1


# ============================================================
# /get_sample_drugs
# ============================================================

def test_get_sample_drugs_success(client, monkeypatch):
    class Dummy:
        def __init__(self, i):
            self.id = i
            self.product_ndc = ""
            self.brand_name = ""
            self.brand_name_base = ""
            self.generic_name = ""
            self.labeler_name = ""
            self.dosage_form = ""
            self.route = ""
            self.marketing_category = ""
            self.product_type = ""
            self.application_number = ""
            self.marketing_start_date = ""
            self.listing_expiration_date = ""
            self.finished = False

        def to_dict(self):
            return {"id": self.id}

    monkeypatch.setattr(
        drug_repo,
        "get_sample_drugs_locally",
        lambda: [Dummy(1), Dummy(2)]
    )

    resp = client.get("/get_sample_drugs")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 2
    assert resp.get_json()[0]["id"] == 1


# ============================================================
# /search_drug
# ============================================================

def test_search_drug_missing_name(client):
    resp = client.get("/search_drug")
    assert resp.status_code == 400


def test_search_drug_name_too_short(client):
    resp = client.get("/search_drug?name=a")
    assert resp.status_code == 400


def test_search_drug_no_results(client, monkeypatch):
    monkeypatch.setattr(drug_repo, "search_drugs_by_keywords_locally", lambda x: [])
    resp = client.get("/search_drug?name=aspirin")
    assert resp.status_code == 404
    assert resp.get_json() == []


def test_search_drug_success(client, monkeypatch):
    class DummyDrug:
        def __init__(self, id):
            self.id = id
            self.product_ndc = ""
            self.brand_name = ""
            self.brand_name_base = ""
            self.generic_name = ""
            self.labeler_name = ""
            self.dosage_form = ""
            self.route = ""
            self.marketing_category = ""
            self.product_type = ""
            self.application_number = ""
            self.marketing_start_date = ""
            self.listing_expiration_date = ""
            self.finished = False

        def to_dict(self):
            return {"id": self.id}

    monkeypatch.setattr(
        drug_repo,
        "search_drugs_by_keywords_locally",
        lambda names: [DummyDrug(10), DummyDrug(20)]
    )

    resp = client.get("/search_drug?name=aspirin test")
    assert resp.status_code == 200
    assert resp.get_json()[0]["id"] == 10


# ============================================================
# /get_drug_by_ndc
# ============================================================

def test_get_drug_by_ndc_missing_ndc(client):
    resp = client.get("/get_drug_by_ndc", json={})
    assert resp.status_code == 400


def test_get_drug_by_ndc_not_found(client, monkeypatch):
    monkeypatch.setattr(drug_repo, "get_drug_by_ndc_locally", lambda x: None)
    resp = client.get("/get_drug_by_ndc", json={"ndc": "XYZ"})
    assert resp.status_code == 400


def test_get_drug_by_ndc_success(client, monkeypatch):
    class Dummy:
        def to_dict(self):
            return {"ndc": "123"}

    monkeypatch.setattr(drug_repo, "get_drug_by_ndc_locally", lambda x: Dummy())

    resp = client.get("/get_drug_by_ndc", json={"ndc": "123"})
    assert resp.status_code == 400


    