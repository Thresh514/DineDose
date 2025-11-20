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
# GET /update_drug_record?id=5&status=ON_TIME&notes=aaa
# ----------------------------------------
@drug_record_bp.route('/update_drug_record', methods=['GET'])
def update_drug_record():
    record_id = request.args.get("id")
    if not record_id:
        return jsonify({"error": "Missing id"}), 400

    record_id = int(record_id)

    # Optional fields
    dosage_numeric = request.args.get("dosage_numeric")
    unit = request.args.get("unit")
    amount_literal = request.args.get("amount_literal")
    status = request.args.get("status")          # TAKEN / ON_TIME / LATE / SKIPPED
    notes = request.args.get("notes")

    # Convert dosage if exists
    if dosage_numeric is not None:
        try:
            dosage_numeric = float(dosage_numeric)
        except:
            return jsonify({"error": "Invalid dosage_numeric"}), 400

    success = drug_record_repo.update_drug_record(
        record_id=record_id,
        dosage_numeric=dosage_numeric,
        unit=unit,
        amount_literal=amount_literal,
        status=status,
        notes=notes
    )

    if not success:
        return jsonify({"error": f"Record id {record_id} not updated"}), 404

    return jsonify({"message": "Record updated", "id": record_id}), 200

# ----------------------------------------
# GET TEST: create a simple drug_record
# /create_drug_record_test?user_id=2&drug_id=1002
# ----------------------------------------
@drug_record_bp.route('/create_drug_record_test', methods=['GET'])
def create_drug_record_test():
    user_id = int(request.args.get("user_id", 1))
    drug_id = int(request.args.get("drug_id", 1002))

    new_id = drug_record_repo.create_drug_record(
        user_id=user_id,
        drug_id=drug_id,
        taken_date=date.today(),
        taken_time=None,
        dosage_numeric=100,
        unit="mg",
        plan_item_id=None,
        status="TAKEN",
        notes="this is test record"
    )

    return jsonify({"message": "Created test drug record", "id": new_id}), 200