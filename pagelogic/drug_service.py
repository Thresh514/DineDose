from repository.drug_repo.drug_repo import DrugRepository

class DrugService:

    @staticmethod
    def get_drug_by_id(drug_id):
        drug = DrugRepository.get_by_id(drug_id)
        if not drug:
            return None
        return {
            "id": drug.id,
            "brand_name": drug.brand_name,
            "generic_name": drug.generic_name,
            "labeler_name": drug.labeler_name,
            "route": drug.route
        }

    @staticmethod
    def search_drug_by_name(name):
        drugs = DrugRepository.get_by_name(name)
        return [
            {
                "id": d.id,
                "brand_name": d.brand_name,
                "generic_name": d.generic_name,
                "route": d.route
            } for d in drugs
        ]