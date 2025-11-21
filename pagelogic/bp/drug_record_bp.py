import datetime
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
        status=status, # e.g., 'TAKEN', 'ON_TIME', 'LATE', 'SKIPPED'
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
        expected_date=date.today(),
        expected_time=None,
        dosage_numeric=0.0,
        unit="default_unit",
        plan_item_id=None,
        status="LATE", # e.g., 'TAKEN', 'ON_TIME', 'LATE', 'SKIPPED'
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
        expected_date=taken_date,
        expected_time=taken_time,
        dosage_numeric=data.get("dosage_numeric"),
        unit=data.get("unit"),
        plan_item_id=data.get("plan_item_id"),
        status=data.get("status", "TAKEN"),
        notes=data.get("notes")
    )
    
    return jsonify({"message": "Drug record created", "id": new_id}), 200




@drug_record_bp.route('/mark_drug_taken', methods=['POST'])
def mark_drug_taken():
    data = request.get_json() or {}

    user_id = data.get("user_id")
    drug_id = data.get("drug_id")
    plan_item_id = data.get("plan_item_id")
    expected_date_str = data.get("expected_date")
    expected_time_str = data.get("expected_time")  # 可能为 None
    status = data.get("status")       # ON_TIME / EARLY / LATE（业务状态）
    timing_flag = data.get("timing_flag")  # EARLY / LATE / None
    taken_at_str = data.get("taken_at")    # ISO string，用于日志/调试

    # 基本校验
    if not user_id or not drug_id or not plan_item_id or not expected_date_str:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        user_id = int(user_id)
        drug_id = int(drug_id)
        plan_item_id = int(plan_item_id)
    except ValueError:
        return jsonify({"error": "Invalid id"}), 400

    try:
        expected_date = date.fromisoformat(expected_date_str)
    except ValueError:
        return jsonify({"error": "Invalid expected_date"}), 400

    expected_time = None
    if expected_time_str:
        try:
            parts = expected_time_str.split(':')
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            second = int(parts[2]) if len(parts) > 2 else 0
            expected_time = dt_time(hour, minute, second)
        except (ValueError, IndexError):
            return jsonify({"error": "Invalid expected_time"}), 400

    # 业务状态校验：只允许 ON_TIME / EARLY / LATE
    if status not in ("ON_TIME", "EARLY", "LATE"):
        return jsonify({"error": "Invalid status"}), 400

    # ====== 查重：同一个 plan_item + expected_date + expected_time 不允许重复记录 ======
    existing = drug_record_repo.get_drug_record_by_unique(
        user_id=user_id,
        plan_item_id=plan_item_id,
        expected_date=expected_date,
        expected_time=expected_time
    )
    if existing:
        return jsonify({"error": "This dose has already been recorded"}), 400

    # ====== 插入记录 ======
    # 注意：这里写入数据库的 status 统一用 TAKEN（避免 EARLY 不在 enum 里导致报错）
    db_status = "TAKEN"

    new_id = drug_record_repo.create_drug_record(
        user_id=user_id,
        drug_id=drug_id,
        expected_date=expected_date,   # 这里改成 expected_date
        expected_time=expected_time,
        dosage_numeric=None,
        unit=None,
        plan_item_id=plan_item_id,
        status=db_status,              # DB 里存 TAKEN
        notes=None
    )

    return jsonify({
        "message": "Recorded",
        "id": new_id,
        "status": status,
        "timing_flag": timing_flag
    }), 200