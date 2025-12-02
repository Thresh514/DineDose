from flask import jsonify, Blueprint, request

from pagelogic.repo import food_repo
from utils.bing_api import GoogleImagesAPI
from config import BING_IMAGES_API_KEY

food_bp = Blueprint('food_bp', __name__)


@food_bp.route('/get_foods', methods=['GET'])
def get_food_locally():
    """Get foods by id or name. Must provide exactly one."""
    food_id = int(request.args.get("id", 0))
    food_name = request.args.get("name", "")

    if (food_id != 0 and food_name != "") or (food_id == 0 and food_name == ""):
        return jsonify({"error": "must provide exactly one of id or name"}), 400

    print("food_id:", food_id)
    print("food_name:", food_name)

    if food_id != 0:
        food = food_repo.get_food_by_id_locally(food_id)
        if food is None:
            return jsonify([]), 404
        return jsonify([food.to_dict()]), 200

    foods = food_repo.get_foods_by_name_locally(food_name)
    if not foods:
        return jsonify([]), 404
    return jsonify([food.to_dict() for food in foods]), 200


@food_bp.route('/get_sample_foods', methods=['GET'])
def get_sample_foods_locally():
    """Return first 100 foods."""
    sample_foods = food_repo.get_sample_foods_locally()
    return jsonify([food.to_dict() for food in sample_foods]), 200


@food_bp.route('/search_food', methods=['GET'])
def search_foods_locally():
    """Search foods by name (description includes name). Name must be at least 2 characters."""
    name = request.args.get("name", "")
    names = name.split(" ")

    if not name:
        return jsonify({"error": "Missing name"}), 400
    
    if len(name) < 2:
        return jsonify({"error": "Name too short, must be at least 2 characters"}), 400

    foods = food_repo.search_foods_by_keywords_locally(names)
    if not foods:
        return jsonify([]), 404

    return jsonify([food.to_dict() for food in foods]), 200


@food_bp.route('/get-food-image', methods=['GET'])
def get_food_image():
    """
    Get food image from Bing Images API using SerpApi.
    
    Query Parameters:
        food_name: The name of the food to search for (required)
    
    Returns:
        JSON with image_url, thumbnail, title, and source
    """
    food_name = request.args.get('food_name', '').strip()

    if not food_name:
        return jsonify({"error": "food_name parameter is required"}), 400

    # If API key is not configured, return placeholder
    if not BING_IMAGES_API_KEY:
        print(f"[INFO] No API key configured. Using fallback for: {food_name}")
        return jsonify({
            "image_url": None,
            "source": "placeholder",
            "title": "Using default image - Configure BING_IMAGES_API_KEY for real images"
        }), 200

    google_api = GoogleImagesAPI(BING_IMAGES_API_KEY)
    
    # Try searching with the full food name first
    result = google_api.search_food_image(food_name)
    
    # If no results with full name, try with just the first few meaningful words
    if not result and len(food_name.split()) > 1:
        # Try with first 2-3 words or meaningful keywords
        words = food_name.split()
        search_terms = [
            " ".join(words[:3]),  # First 3 words
            " ".join(words[:2]),  # First 2 words
            words[0]              # First word
        ]
        
        for search_term in search_terms:
            if search_term and len(search_term) >= 2:
                print(f"[INFO] Retrying with simplified search term: '{search_term}'")
                result = google_api.search_food_image(search_term)
                if result:
                    break

    if result:
        return jsonify(result), 200
    else:
        print(f"[WARNING] No image found for food: {food_name}")
        return jsonify({
            "image_url": None,
            "source": "placeholder",
            "title": f"No image found for {food_name}"
        }), 200