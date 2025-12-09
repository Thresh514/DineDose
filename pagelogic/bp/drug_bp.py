from flask import jsonify, Blueprint, request

from pagelogic.repo import drug_repo

drug_bp = Blueprint('drug_bp', __name__)

@drug_bp.route('/get_drug', methods=['GET'])
def get_drug_by_id_locally():
    drug_id = request.args.get("id")
    if not drug_id:
        return jsonify({"error": "Missing id"}), 400

    drug_id = int(drug_id)

    food = drug_repo.get_drug_by_id_locally(drug_id)
    if food is None:
        return jsonify({"error": f"No food found with id {drug_id}"}), 404

    return jsonify(food.to_dict()), 200





# Return a sample of drugs (first 100)
@drug_bp.route('/get_sample_drugs', methods=['GET'])
def get_sample_drugs_locally():
    sample_drugs = drug_repo.get_sample_drugs_locally()
    return jsonify([drug.to_dict() for drug in sample_drugs]), 200


# Search drugs by whether the brand_name or generic_name includes name
# name should be at least 2 characters long

#search_drug?name="aspirin amazon"
# if multiple drugs match, return the first 100 drugs
@drug_bp.route('/search_drug', methods=['GET'])
def search_drug_locally():
    name = request.args.get("name", "")
    names = name.split(" ")
    if not names or all(name == "" for name in names):
        return jsonify({"error": "Missing name"}), 400
        
    if len(name) < 2:
        return jsonify({"error": "Name too short, must be at least 2 characters"}), 400

    drugs = drug_repo.search_drugs_by_keywords_locally(names)
    if not drugs:
        return jsonify([]), 404

    return jsonify([drug.to_dict() for drug in drugs]), 200


# Get drug by ndc
# /get_drug_by_ndc?ndc=12345-6789
@drug_bp.route('/get_drug_by_ndc', methods=['GET'])
def get_drug_by_ndc_locally():
    ndc = request.args.get("ndc", "")
    if not ndc:
        return jsonify({"error": "Missing ndc"}), 400

    drug = drug_repo.get_drug_by_ndc_locally(ndc)
    if drug is None:
        return jsonify({"error": f"No drug found with ndc {ndc}"}), 404

    return jsonify(drug.to_dict()), 200