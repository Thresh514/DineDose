from flask import jsonify, render_template, Blueprint, request

from pagelogic.repo import food_record_repo

past_foods_bp = Blueprint('past_foods_bp', __name__)

@past_foods_bp.route('/past_foods', methods=['GET'])
def past_foods_view():
    user_id = int(request.args.get("user_id", 1))

    records = food_record_repo.get_food_records_by_user_id(user_id)

    records_dicts = [record.to_dict() for record in records]

    return render_template("past_foods_view.html", records=records_dicts)

