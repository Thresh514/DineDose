from flask import jsonify, Blueprint, request

from pagelogic.repo import food_repo

food_bp = Blueprint('food_bp', __name__)


#返回一个 food[]
#传入id或者name；不能两者同时传入
#如果是id，返回一个长度为1的list of food
#如果是name，返回一个description内包含name 的list of food
@food_bp.route('/get_foods', methods=['GET'])
def get_food_locally():
    food_id = int(request.args.get("id", 0))
    food_name = request.args.get("name", "")

    # 不能同时传 / 同时不传
    if (food_id != 0 and food_name != "") or (food_id == 0 and food_name == ""):
        return jsonify({"error": "must provide exactly one of id or name"}), 400

    print("food_id:", food_id)
    print("food_name:", food_name)

    # 通过 id 查
    if food_id != 0:
        food = food_repo.get_food_by_id_locally(food_id)
        if food is None:
            return jsonify([]), 404  # 没找到返回空 list
        return jsonify([food.to_dict()]), 200

    # 通过 name 查（description 内包含 name 的逻辑在 repo 里实现）
    foods = food_repo.get_foods_by_name_locally(food_name)
    if not foods:
        return jsonify([]), 404
    return jsonify([food.to_dict() for food in foods]), 200