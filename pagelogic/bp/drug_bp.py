from flask import jsonify, render_template, Blueprint, request

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