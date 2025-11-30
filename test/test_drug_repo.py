import pytest
from pagelogic.repo import drug_repo


# ---------- Fake DB cursor / connection ----------
class FakeCursor:
    def __init__(self, description, rows):
        self.description = description
        self.rows = rows
        self.index = 0

    def execute(self, sql, params=None):
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
        return True


@pytest.fixture
def mock_mydb(monkeypatch):
    """Patch mydb() for drug_repo."""
    def fake_mydb():
        columns = [
            ("id",), ("product_ndc",), ("brand_name",), ("brand_name_base",),
            ("generic_name",), ("labeler_name",), ("dosage_form",), ("route",),
            ("marketing_category",), ("product_type",), ("application_number",),
            ("marketing_start_date",), ("listing_expiration_date",), ("finished",)
        ]

        rows = [
            (1, "0001", "BrandA", "BaseA", "GenA", "A Inc",
             "tablet", "oral", "OTC", "type1", "A1",
             "2020-01-01", "2030-01-01", True)
        ]

        return FakeConn(FakeCursor(columns, rows))

    monkeypatch.setattr(drug_repo, "mydb", fake_mydb)


# ------------------------------------------------------------
#                TEST get_drugs
# ------------------------------------------------------------
def test_get_drugs(mock_mydb):
    drug_repo.drugs = []
    drug_repo.get_drugs()
    assert len(drug_repo.drugs) == 1
    assert drug_repo.drugs[0].generic_name == "GenA"


# ------------------------------------------------------------
#                TEST get_drugs_by_ids
# ------------------------------------------------------------
def test_get_drugs_by_ids(mock_mydb):
    results = drug_repo.get_drugs_by_ids([1])
    assert len(results) == 1
    assert results[0].brand_name == "BrandA"


# ------------------------------------------------------------
#                TEST get_drug_by_id
# ------------------------------------------------------------
def test_get_drug_by_id(mock_mydb):
    result = drug_repo.get_drug_by_id(1)
    assert result.generic_name == "GenA"


# ------------------------------------------------------------
#                TEST local cache functions
# ------------------------------------------------------------
def test_get_drug_by_id_locally():
    drug_repo.drugs = [
        drug_repo.drug(1, "x", "BrandX", "Base", "GenericX",
                       "Labs", "cap", "oral", "OTC", "type",
                       "A", "2020", "2030", True)
    ]
    assert drug_repo.get_drug_by_id_locally(1).generic_name == "GenericX"


def test_get_drugs_by_ids_locally():
    drug_repo.drugs = [
        drug_repo.drug(1, "x", "A", "", "", "", "", "", "", "", "", "", "", True),
        drug_repo.drug(2, "x", "B", "", "", "", "", "", "", "", "", "", "", True),
    ]
    res = drug_repo.get_drugs_by_ids_locally([1, 2])
    assert len(res) == 2
