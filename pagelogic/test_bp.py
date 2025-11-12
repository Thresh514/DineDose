from flask import jsonify, render_template, Blueprint, request

from pagelogic.repo import drug_repo, plan_repo
from pagelogic.service import plan_service

test_bp = Blueprint('test_bp', __name__)


@test_bp.route('/get_user_plan', methods=['GET'])
def get_user_plan():
    user_id = request.args.get("id")
    from_when = request.args.get("from")
    to_when = request.args.get("to")

    plan = plan_service.get_user_plan(user_id, from_when, to_when)
    return jsonify({
        plan
    }), 200

@test_bp.route('/ping', methods=['GET'])
def pingpong():
    return jsonify(
        "pong"
    ), 200

@test_bp.route('/get_drug', methods=['GET'])
def test_get_drugs_by_ids():
    ids = request.args.getlist("ids")   # ['1','2','3']
    print(ids)
    ids = list(map(int, ids))           # [1,2,3]
    print(ids)

    drugs = drug_repo.get_drugs_by_ids(ids)
    print(drugs)
    drug_dicts = [d.to_dict() for d in drugs]

    return jsonify(drug_dicts), 200


@test_bp.route('/get_plan_by_user_id', methods=['GET'])
def test_get_plan_by_user_id():
    user_id = request.args.get("id")

    plan = plan_repo.get_plan_by_user_id(user_id)
    print(plan.to_dict())
    return jsonify(), 200