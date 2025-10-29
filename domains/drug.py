from repository.db import db

class Drug(db.Model):
    __tablename__ = 'drugs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_ndc = db.Column(db.String(50))
    brand_name = db.Column(db.String(255))
    brand_name_base = db.Column(db.String(255))
    generic_name = db.Column(db.Text)
    labeler_name = db.Column(db.String(255))
    dosage_form = db.Column(db.String(255))
    route = db.Column(db.String(255))
    marketing_category = db.Column(db.String(255))
    product_type = db.Column(db.String(255))
    application_number = db.Column(db.String(255))
    marketing_start_date = db.Column(db.String(20))
    listing_expiration_date = db.Column(db.String(20))
    finished = db.Column(db.Boolean)

    def __repr__(self):
        return f"<Drug {self.brand_name} ({self.id})>"