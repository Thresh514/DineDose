
from datetime import date, time
from flask import jsonify, render_template, Blueprint, request
from pagelogic.repo import plan_repo
from pagelogic.service import plan_service


plan_bp = Blueprint('plan_bp', __name__)
#sample call: 
# GET /get_use_plan?user_id=2&from=2025-11-01&to=2025-12-31
#可以传入date
# GET /get_user_plan?user_id=2&from=2025-11-01T10:00:00&to=2025-12-15T22:00:00
#datetime也ok
@plan_bp.route("/get_user_plan", methods=["GET"])
def get_user_plan_handler():
    user_id = int(request.args.get("id"))
    from_str = request.args.get("from")   # 可能是 None
    to_str = request.args.get("to")

    from_when = date.fromisoformat(from_str) if from_str else None
    to_when = date.fromisoformat(to_str) if to_str else None

    plan = plan_service.get_user_plan(user_id, from_when, to_when)
    return jsonify(plan.to_dict()), 200

@plan_bp.route("/get_raw_plan", methods=["GET"])
def get_raw_plan_handler():
    """
    GET /get_raw_plan?id=5

    返回某个 user 的原始 plan（未展开的 plan_item + plan_item_rule），
    专门给医生编辑页面用。
    """
    user_id_str = request.args.get("id")
    if not user_id_str:
        return jsonify({"error": "id is required"}), 400

    try:
        user_id = int(user_id_str)
    except ValueError:
        return jsonify({"error": "id must be int"}), 400

    plan = plan_service.get_raw_plan(user_id)
    if not plan:
        return jsonify({"error": f"No plan found for user {user_id}"}), 404

    # 这里直接用你原来的 to_dict
    return jsonify(plan.to_dict()), 200




@plan_bp.route("/plan_item", methods=["POST"])
def create_plan_item():
    """
    Body JSON 示例：
    {
      "plan_id": 1,
      "drug_id": 1001,
      "dosage": 2000,
      "unit": "mg",
      "amount_literal": "2 tablets",
      "note": "after meal",
      "rules": [
        {
          "start_date": "2025-11-21",
          "end_date": "2025-11-30",
          "repeat_type": "DAILY",
          "interval_value": 1,
          "mon": true, "tue": true, "wed": true, "thu": true, "fri": true,
          "sat": false, "sun": false,
          "times": ["12:00:00", "18:00:00"]
        }
      ]
    }
    """
    data = request.get_json() or {}
    plan_id = data.get("plan_id")
    patient_id = data.get("patient_id")

    if not plan_id:
        if not patient_id:
            return jsonify({"error": "plan_id or patient_id required"}), 400

        # 自动查 plan
        plan = plan_repo.get_plan_by_user_id(int(patient_id))
        if not plan:
            return jsonify({"error": f"No plan found for patient {patient_id}"}), 404
        plan_id = plan.id

    drug_id = data.get("drug_id")
    dosage  = data.get("dosage")
    unit    = data.get("unit")

    if not all([plan_id, drug_id, dosage, unit]):
        return jsonify({"error": "plan_id, drug_id, dosage, unit are required"}), 400

    try:
        plan_id = int(plan_id)
        drug_id = int(drug_id)
        dosage  = int(dosage)
    except ValueError:
        return jsonify({"error": "plan_id, drug_id, dosage must be int"}), 400

    amount_literal = data.get("amount_literal")
    note           = data.get("note")
    rules_raw      = data.get("rules", [])

    # 解析 rules
    parsed_rules = []
    for r in rules_raw:
        try:
            start_date = date.fromisoformat(r["start_date"])
        except Exception:
            return jsonify({"error": "Invalid start_date in rules"}), 400

        end_date_str = r.get("end_date")
        end_date = None
        if end_date_str:
            try:
                end_date = date.fromisoformat(end_date_str)
            except Exception:
                return jsonify({"error": "Invalid end_date in rules"}), 400

        repeat_type    = r.get("repeat_type", "ONCE")
        interval_value = r.get("interval_value")

        # weekday flags
        mon = bool(r.get("mon", False))
        tue = bool(r.get("tue", False))
        wed = bool(r.get("wed", False))
        thu = bool(r.get("thu", False))
        fri = bool(r.get("fri", False))
        sat = bool(r.get("sat", False))
        sun = bool(r.get("sun", False))

        # times: ["12:00:00", "18:00:00"] -> [dt_time, dt_time]
        times_list = []
        for t in r.get("times", []):
            if not t:
                continue
            try:
                parts = str(t).split(":")
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
                second = int(parts[2]) if len(parts) > 2 else 0
                times_list.append(time(hour, minute, second))
            except Exception:
                return jsonify({"error": f"Invalid time in rules: {t}"}), 400

        parsed_rules.append({
            "start_date": start_date,
            "end_date": end_date,
            "repeat_type": repeat_type,
            "interval_value": interval_value,
            "mon": mon,
            "tue": tue,
            "wed": wed,
            "thu": thu,
            "fri": fri,
            "sat": sat,
            "sun": sun,
            "times": times_list,
        })

    try:
        new_item_id = plan_repo.create_plan_item_with_rules(
            plan_id=plan_id,
            drug_id=drug_id,
            dosage=dosage,
            unit=unit,
            amount_literal=amount_literal,
            note=note,
            rules=parsed_rules,
        )
    except Exception as e:
        return jsonify({"error": "create_plan_item failed", "detail": str(e)}), 500

    return jsonify({"message": "plan_item created", "plan_item_id": new_item_id}), 201


@plan_bp.route("/plan_item/<int:item_id>", methods=["PUT"])
def update_plan_item(item_id):
    """
    Body JSON 和 create 基本一样，只是 plan_item 已存在：
    {
      "plan_id": 1,
      "drug_id": 1001,
      "dosage": 1500,
      "unit": "mg",
      "amount_literal": "1.5 tablets",
      "note": "after meal",
      "rules": [ ... 同上 ... ]
    }
    """
    data = request.get_json() or {}
    plan_id = data.get("plan_id")
    patient_id = data.get("patient_id")

    if not plan_id:
        if not patient_id:
            return jsonify({"error": "plan_id or patient_id required"}), 400

        # 自动查 plan
        plan = plan_repo.get_plan_by_user_id(int(patient_id))
        if not plan:
            return jsonify({"error": f"No plan found for patient {patient_id}"}), 404
        plan_id = plan.id
    drug_id = data.get("drug_id")
    dosage  = data.get("dosage")
    unit    = data.get("unit")

    if not all([plan_id, drug_id, dosage, unit]):
        return jsonify({"error": "plan_id, drug_id, dosage, unit are required"}), 400

    try:
        plan_id = int(plan_id)
        drug_id = int(drug_id)
        dosage  = int(dosage)
    except ValueError:
        return jsonify({"error": "plan_id, drug_id, dosage must be int"}), 400

    amount_literal = data.get("amount_literal")
    note           = data.get("note")
    rules_raw      = data.get("rules", [])

    # 解析 rules（和 create 一样）
    parsed_rules = []
    for r in rules_raw:
        try:
            start_date = date.fromisoformat(r["start_date"])
        except Exception:
            return jsonify({"error": "Invalid start_date in rules"}), 400

        end_date_str = r.get("end_date")
        end_date = None
        if end_date_str:
            try:
                end_date = date.fromisoformat(end_date_str)
            except Exception:
                return jsonify({"error": "Invalid end_date in rules"}), 400

        repeat_type    = r.get("repeat_type", "ONCE")
        interval_value = r.get("interval_value")

        mon = bool(r.get("mon", False))
        tue = bool(r.get("tue", False))
        wed = bool(r.get("wed", False))
        thu = bool(r.get("thu", False))
        fri = bool(r.get("fri", False))
        sat = bool(r.get("sat", False))
        sun = bool(r.get("sun", False))

        times_list = []
        for t in r.get("times", []):
            if not t:
                continue
            try:
                parts = str(t).split(":")
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
                second = int(parts[2]) if len(parts) > 2 else 0
                times_list.append(time(hour, minute, second))
            except Exception:
                return jsonify({"error": f"Invalid time in rules: {t}"}), 400

        parsed_rules.append({
            "start_date": start_date,
            "end_date": end_date,
            "repeat_type": repeat_type,
            "interval_value": interval_value,
            "mon": mon,
            "tue": tue,
            "wed": wed,
            "thu": thu,
            "fri": fri,
            "sat": sat,
            "sun": sun,
            "times": times_list,
        })

    try:
        ok = plan_repo.update_plan_item_with_rules(
            item_id=item_id,
            plan_id=plan_id,
            drug_id=drug_id,
            dosage=dosage,
            unit=unit,
            amount_literal=amount_literal,
            note=note,
            rules=parsed_rules,
        )
    except Exception as e:
        return jsonify({"error": "update_plan_item failed", "detail": str(e)}), 500

    if not ok:
        return jsonify({"error": f"plan_item {item_id} not found"}), 404

    return jsonify({"message": "plan_item updated", "plan_item_id": item_id}), 200

@plan_bp.route("/plan_item/<int:item_id>", methods=["DELETE"])
def delete_plan_item(item_id):
    """
    删除 plan_item 以及它对应的所有 plan_item_rule
    """
    try:
        ok = plan_repo.delete_plan_item_and_rules(item_id)
    except Exception as e:
        return jsonify({"error": "delete_plan_item failed", "detail": str(e)}), 500

    if not ok:
        return jsonify({"error": f"plan_item {item_id} not found"}), 404

    return jsonify({"message": "plan_item deleted", "plan_item_id": item_id}), 200