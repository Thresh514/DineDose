from datetime import date, time as dt_time
from flask import jsonify, render_template, Blueprint, request


from pagelogic.repo import food_record_repo


food_record_bp = Blueprint('food_record_bp', __name__)

@food_record_bp.route('/create_food_record', methods=['GET', 'POST'])
def create_food_record_handler():
    """
    创建食物记录
    GET 方法：兼容旧接口，使用 query parameters
    POST 方法：接收 JSON 数据，支持完整参数
    """
    if request.method == 'GET':
        # 兼容旧的 GET 方法
        user_id = int(request.args.get("user_id", 1))
        food_id = int(request.args.get("food_id", 1))

        record_id = food_record_repo.create_food_record(
            user_id=user_id,
            food_id=food_id,
            eaten_date=date.today()
        )

        return jsonify({"created_id": record_id}), 200
    
    elif request.method == 'POST':
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        user_id = data.get("user_id")
        food_id = data.get("food_id")
        
        if not user_id or not food_id:
            return jsonify({"error": "user_id and food_id are required"}), 400
        
        # 解析日期和时间
        eaten_date = date.today()
        if data.get("eaten_date"):
            try:
                eaten_date = date.fromisoformat(data["eaten_date"])
            except ValueError:
                pass
        
        eaten_time = None
        if data.get("eaten_time"):
            try:
                if isinstance(data["eaten_time"], str):
                    time_str = data["eaten_time"]
                    parts = time_str.split(':')
                    hour = int(parts[0])
                    minute = int(parts[1]) if len(parts) > 1 else 0
                    second = int(parts[2]) if len(parts) > 2 else 0
                    eaten_time = dt_time(hour, minute, second)
                else:
                    eaten_time = data["eaten_time"]
            except (ValueError, IndexError, TypeError):
                pass
        
        record_id = food_record_repo.create_food_record(
            user_id=user_id,
            food_id=food_id,
            eaten_date=eaten_date,
            eaten_time=eaten_time,
            amount_numeric=data.get("amount_numeric"),
            unit=data.get("unit"),
            amount_literal=data.get("amount_literal"),
            notes=data.get("notes"),
            source="manual",
            status="TAKEN"
        )
        
        return jsonify({"created_id": record_id, "message": "Meal added successfully"}), 200

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
        status="TAKEN" # e.g., 'TAKEN', 'ON_TIME', 'LATE', 'SKIPPED'
    )

    if not success:
        return jsonify({"error": f"No record with id {record_id} found"}), 404

    return jsonify({"message": "Record updated", "id": record_id}), 200

