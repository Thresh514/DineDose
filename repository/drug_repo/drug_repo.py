from repository.db import db
from domains.drug import Drug

class DrugRepository:

    @staticmethod
    def get_by_id(drug_id):
        """根据ID查找药品"""
        return Drug.query.get(drug_id)

    @staticmethod
    def get_by_name(brand_name):
        """根据brand_name查找药品"""
        return Drug.query.filter(Drug.brand_name.ilike(f"%{brand_name}%")).all()

    @staticmethod
    def get_all(limit=100):
        """可选：获取部分药品（默认100条）"""
        return Drug.query.limit(limit).all()