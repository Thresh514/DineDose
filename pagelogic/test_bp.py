from datetime import date, time as dt_time
from flask import jsonify, render_template, Blueprint, request
from pagelogic.repo import plan_repo, food_record_repo


test_bp = Blueprint('test_bp', __name__)


@test_bp.route('/get_plan_by_user_id', methods=['GET'])
def get_plan_by_user_id():
    user_id = request.args.get("id")

    plan = plan_repo.get_plan_by_user_id(user_id)
    print(plan.to_dict())
    return jsonify(plan.to_dict()), 200



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

