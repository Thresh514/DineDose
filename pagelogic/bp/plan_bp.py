
from datetime import date
from flask import jsonify, render_template, Blueprint, request

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
    print("total number of plan_items: ", len(plan.plan_items))
    return jsonify(plan.to_dict()), 200

