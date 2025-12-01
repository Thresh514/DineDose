from flask import jsonify, Blueprint, request

from pagelogic.repo import food_repo

food_bp = Blueprint('food_bp', __name__)


#返回一个 food[]
#传入id或者name；不能两者同时传入
# /gets_foods?name=Banana&id=1 是违法的
#如果是id，返回一个长度为1的list of food
#如果是name，返回一个description内包含name 的list of food
#sample call:
# /gets_foods?name=Banana
# /gets_foods?id=1
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


# Return a sample of foods (first 100)
@food_bp.route('/get_sample_foods', methods=['GET'])
def get_sample_foods_locally():
    sample_foods = food_repo.get_foods_by_names_locally("")
    #will return first 100 foods
    return jsonify([food.to_dict() for food in sample_foods]), 200


# search food，by whether the  description includes name 
# /search_food?name="Banana Juice"
# name should be at least 2 characters long
#if multiple foods match, return the first 100 foods
@food_bp.route('/search_food', methods=['GET'])
def search_foods_locally():
    name = request.args.get("name", "")
    names = name.split(" ")

    if not name:
        return jsonify({"error": "Missing name"}), 400
    
    if len(name) < 2:
        return jsonify({"error": "Name too short, must be at least 2 characters"}), 400

    foods = food_repo.get_foods_by_names_locally(names)
    if not foods:
        return jsonify([]), 404

    return jsonify([food.to_dict() for food in foods]), 200