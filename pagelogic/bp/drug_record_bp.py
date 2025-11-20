from flask import jsonify, Blueprint, request
from datetime import date, time as dt_time
from pagelogic.repo import drug_record_repo

drug_record_bp = Blueprint('drug_record_bp', __name__)

# ----------------------------------------
# GET /get_drug_record_by_id?id=1
# ----------------------------------------
@drug_record_bp.route('/get_drug_record_by_id', methods=['GET'])
def get_drug_record_by_id():
    record_id = request.args.get("id")
    if not record_id:
        return jsonify({"error": "Missing id"}), 400

    record_id = int(record_id)

    record = drug_record_repo.get_drug_record_by_id(record_id)
    if record is None:
        return jsonify({"error": f"No drug record found with id {record_id}"}), 404

    return jsonify(record.to_dict()), 200

# ----------------------------------------
# GET /get_drug_records_by_user_id?user_id=2
# ----------------------------------------
@drug_record_bp.route('/get_drug_records_by_user_id', methods=['GET'])
def get_drug_records_by_user_id():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    user_id = int(user_id)

    records = drug_record_repo.get_drug_records_by_user_id(user_id)
    record_dicts = [rec.to_dict() for rec in records]

    return jsonify(record_dicts), 200

# ----------------------------------------
# GET /delete_drug_record?id=5
# ----------------------------------------
@drug_record_bp.route('/delete_drug_record', methods=['GET'])
def delete_drug_record():
    record_id = request.args.get("id")
    if not record_id:
        return jsonify({"error": "Missing id"}), 400

    record_id = int(record_id)

    success = drug_record_repo.delete_drug_record(record_id)
    if not success:
        return jsonify({"error": f"No record with id {record_id} found"}), 404

    return jsonify({"message": "Record deleted", "id": record_id}), 200

# ----------------------------------------
# GET /update_drug_record?id=5&status=TAKEN&dosage_numeric=100&unit=mg&notes=aaa
# ----------------------------------------
@drug_record_bp.route('/update_drug_record', methods=['GET'])
def update_drug_record():
    record_id = request.args.get("id")
    if not record_id:
        return jsonify({"error": "Missing id"}), 400

    record_id = int(record_id)

    # Optional fields - get from request args or use defaults
    status = request.args.get("status", "TAKEN")  # TAKEN / ON_TIME / LATE / SKIPPED
    dosage_numeric_str = request.args.get("dosage_numeric")
    unit = request.args.get("unit", "")
    notes = request.args.get("notes", "")

    # Convert dosage if exists
    dosage_numeric = None
    if dosage_numeric_str:
        try:
            dosage_numeric = float(dosage_numeric_str)
        except:
            return jsonify({"error": "Invalid dosage_numeric"}), 400

    success = drug_record_repo.update_drug_record(
        record_id=record_id,
        status=status,
        dosage_numeric=dosage_numeric,
        unit=unit,
        notes=notes
    )

    if not success:
        return jsonify({"error": f"Record id {record_id} not updated"}), 404

    return jsonify({"message": "Record updated", "id": record_id}), 200

# ----------------------------------------
# GET TEST: create a simple drug_record
# /create_drug_record_test?user_id=2&drug_id=1001
# ----------------------------------------
@drug_record_bp.route('/create_drug_record_test', methods=['GET'])
def create_drug_record_test():
    user_id = int(request.args.get("user_id", 1))
    drug_id = int(request.args.get("drug_id", 1001))

    new_id = drug_record_repo.create_drug_record(
        user_id=user_id,
        drug_id=drug_id,
        taken_date=date.today(),
        taken_time=None,
        dosage_numeric=0.0,
        unit="default_unit",
        plan_item_id=None,
        status="LATE",
        notes="default test record"
    )

    return jsonify({"message": "Created test drug record", "id": new_id}), 200

# ----------------------------------------
# POST /create_drug_record - create a drug record with full parameters
# ----------------------------------------
@drug_record_bp.route('/create_drug_record', methods=['POST'])
def create_drug_record():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    
    user_id = data.get("user_id")
    drug_id = data.get("drug_id")
    
    if not user_id or not drug_id:
        return jsonify({"error": "user_id and drug_id are required"}), 400
    
    # Parse date
    taken_date = date.today()
    if data.get("taken_date"):
        try:
            taken_date = date.fromisoformat(data["taken_date"])
        except ValueError:
            pass
    
    # Parse time
    taken_time = None
    if data.get("taken_time"):
        try:
            if isinstance(data["taken_time"], str):
                time_str = data["taken_time"]
                parts = time_str.split(':')
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
                second = int(parts[2]) if len(parts) > 2 else 0
                taken_time = dt_time(hour, minute, second)
            else:
                taken_time = data["taken_time"]
        except (ValueError, IndexError, TypeError):
            pass
    
    new_id = drug_record_repo.create_drug_record(
        user_id=user_id,
        drug_id=drug_id,
        taken_date=taken_date,
        taken_time=taken_time,
        dosage_numeric=data.get("dosage_numeric"),
        unit=data.get("unit"),
        plan_item_id=data.get("plan_item_id"),
        status=data.get("status", "TAKEN"),
        notes=data.get("notes")
    )
    
    return jsonify({"message": "Drug record created", "id": new_id}), 200