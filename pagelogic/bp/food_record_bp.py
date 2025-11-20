from datetime import date
from flask import jsonify, render_template, Blueprint, request


from pagelogic.repo import food_record_repo


food_record_bp = Blueprint('food_record_bp', __name__)

@food_record_bp.route('/create_food_record', methods=['GET'])
def create_food_record_handler():
    user_id = int(request.args.get("user_id", 1))
    food_id = int(request.args.get("food_id", 1))

    record_id = food_record_repo.create_food_record(
        user_id=user_id,
        food_id=food_id,
        eaten_date=date.today()
    )

    return jsonify({"created_id": record_id}), 200

@food_record_bp.route('/get_food_record', methods=['GET'])
def get_food_record_handler():
    """
    Quick browser-test endpoint:
    Reads a food record by id.
    """
    record_id = int(request.args.get("id", 1))

    record = food_record_repo.get_food_record_by_id(record_id)
    if not record:
        return jsonify({"error": f"No record found with id {record_id}"}), 404

    return jsonify(record.to_dict()), 200

@food_record_bp.route('/get_food_records_by_user_id', methods=['GET'])
def get_food_records_by_user_id_handler():
    user_id = int(request.args.get("user_id", 1))

    records = food_record_repo.get_food_records_by_user_id(user_id)
    record_dicts = [record.to_dict() for record in records]

    return jsonify(record_dicts), 200

@food_record_bp.route('/delete_food_record', methods=['GET'])
def delete_food_record_handler():
    record_id = int(request.args.get("id", 1))

    success = food_record_repo.delete_food_record(record_id)
    if not success:
        return jsonify({"error": f"No record with id {record_id} found"}), 404

    return jsonify({"message": "Record deleted", "id": record_id}), 200


@food_record_bp.route('/update_food_record', methods=['GET'])
def update_food_record_handler():
    record_id = int(request.args.get("id", 4))
    notes = request.args.get("notes", "")

    success = food_record_repo.update_food_record(
        record_id=record_id,
        amount_numeric=0.0,
        unit="default_unit",
        amount_literal="default_literal",
        notes=notes,
        status="TAKEN"
    )

    if not success:
        return jsonify({"error": f"No record with id {record_id} found"}), 404

    return jsonify({"message": "Record updated", "id": record_id}), 200

