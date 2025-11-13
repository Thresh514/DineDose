from pagelogic.repo import plan_repo
from flask import jsonify, render_template, Blueprint, request

from pagelogic.service import plan_service

test_bp = Blueprint('test_bp', __name__)


@test_bp.route('/get_user_plan', methods=['GET'])
def get_user_plan():
    user_id = request.args.get("id")
    from_when = request.args.get("from")
    to_when = request.args.get("to")
    request

    plan = plan_service.get_user_plan(user_id, from_when, to_when)
    return jsonify({
        plan
    }), 200

@test_bp.route('/ping', methods=['GET'])
def pingpong():
    return jsonify(
        "pong"
    ), 200


@test_bp.route('/get_plan_item_rules_by_plan_id', methods=['GET'])
def test_get_plan_item_rules_by_plan_id():
    plan_id = request.args.get("id")

    result = plan_repo.get_plan_item_rules_by_plan_id(plan_id)

    for k, v in result.items():
        print("key", k, "value", v)

    return jsonify(), 200