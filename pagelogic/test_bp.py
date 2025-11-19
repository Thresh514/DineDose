from datetime import date
from pagelogic.repo import plan_repo
from flask import jsonify, render_template, Blueprint, request
from datetime import time as dt_time

from pagelogic.repo import drug_repo, plan_repo, food_repo
from pagelogic.service import plan_service
from pagelogic.repo import food_record_repo


test_bp = Blueprint('test_bp', __name__)


#sample call: 
# GET /get_use_plan?user_id=2&from=2025-11-01&to=2025-12-31
#可以传入date
# GET /get_user_plan?user_id=2&from=2025-11-01T10:00:00&to=2025-12-15T22:00:00
#datetime也ok
@test_bp.route("/get_user_plan", methods=["GET"])
def get_user_plan_handler():
    user_id = int(request.args.get("id"))
    from_str = request.args.get("from")   # 可能是 None
    to_str = request.args.get("to")

    from_when = date.fromisoformat(from_str) if from_str else None
    to_when = date.fromisoformat(to_str) if to_str else None

    plan = plan_service.get_user_plan(user_id, from_when, to_when)
    print("total number of plan_items: ", len(plan.plan_items))
    return jsonify(plan.to_dict()), 200

@test_bp.route('/ping', methods=['GET'])
def pingpong():
    return jsonify(
        "pong"
    ), 200

@test_bp.route('/get_drug', methods=['GET'])
def get_drugs_by_ids():
    ids = request.args.getlist("ids")   # ['1','2','3']
    print(ids)
    ids = list(map(int, ids))           # [1,2,3]
    print(ids)

    drugs = drug_repo.get_drugs_by_ids(ids)
    print(drugs)
    drug_dicts = [d.to_dict() for d in drugs]

    return jsonify(drug_dicts), 200


@test_bp.route('/get_plan_by_user_id', methods=['GET'])
def get_plan_by_user_id():
    user_id = request.args.get("id")

    plan = plan_repo.get_plan_by_user_id(user_id)
    print(plan.to_dict())
    return jsonify(plan.to_dict()), 200

@test_bp.route('/get_food_by_id_locally', methods=['GET'])
def get_food_by_id_locally():
    food_id = request.args.get("id")
    if not food_id:
        return jsonify({"error": "Missing id"}), 400

    food_id = int(food_id)

    food = food_repo.get_food_by_id_locally(food_id)
    if food is None:
        return jsonify({"error": f"No food found with id {food_id}"}), 404

    return jsonify(food.to_dict()), 200


@test_bp.route('/get_drug_by_id_locally', methods=['GET'])
def get_drug_by_id_locally():
    drug_id = request.args.get("id")
    if not drug_id:
        return jsonify({"error": "Missing id"}), 400

    drug_id = int(drug_id)

    food = drug_repo.get_drug_by_id_locally(drug_id)
    if food is None:
        return jsonify({"error": f"No food found with id {drug_id}"}), 404

    return jsonify(food.to_dict()), 200

@test_bp.route('/doctor_calendar', methods=['GET', 'POST'])
def calendar_view():
    return render_template("doctor_calendar_view.html")

@test_bp.route('/create_food_record_test', methods=['GET'])
def create_food_record_test_handler():
    user_id = int(request.args.get("user_id", 1))
    food_id = int(request.args.get("food_id", 1))

    record_id = food_record_repo.create_food_record(
        user_id=user_id,
        food_id=food_id,
        eaten_date=date.today()
    )

    return jsonify({"created_id": record_id}), 200

    
@test_bp.route('/get_food_record_test', methods=['GET'])
def get_food_record_test():
    """
    Quick browser-test endpoint:
    Reads a food record by id.
    """
    record_id = int(request.args.get("id", 1))

    record = food_record_repo.get_food_record_by_id(record_id)
    if not record:
        return jsonify({"error": f"No record found with id {record_id}"}), 404

    return jsonify(record.to_dict()), 200
