from flask import jsonify, render_template, Blueprint, request

from pagelogic.repo import drug_repo, food_repo

food_bp = Blueprint('food_bp', __name__)

@food_bp.route('/get_food', methods=['GET'])
def get_food_by_id_locally():
    food_id = request.args.get("id")
    if not food_id:
        return jsonify({"error": "Missing id"}), 400

    food_id = int(food_id)

    food = food_repo.get_food_by_id_locally(food_id)
    if food is None:
        return jsonify({"error": f"No food found with id {food_id}"}), 404

    return jsonify(food.to_dict()), 200