import requests
import logging

logger = logging.getLogger(__name__)


class GoogleImagesAPI:
    """
    Wrapper for Google Images search using SerpApi.
    Uses the 'recipes_results' from Google search for better food image results.
    """

    def __init__(self, api_key):
        """
        Initialize the Google Images API wrapper.
        
        Args:
            api_key: SerpApi API key
        """
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search"

    def search_food_image(self, food_name):
        """
        Search for food images using Google Search via SerpApi.
        Prioritizes recipes_results for food-related content.
        
        Args:
            food_name: Name of the food to search for
            
        Returns:
            Dictionary with image_url, thumbnail, title, source, or None if no results
        """
        if not food_name or not isinstance(food_name, str):
            logger.warning(f"Invalid food_name: {food_name} (type: {type(food_name)})")
            return None

        try:
            # First try: Regular Google search (returns recipes_results for food queries)
            params = {
                "engine": "google",
                "q": food_name,
                "api_key": self.api_key,
            }

            logger.info(f"[GoogleImagesAPI] Searching Google for: '{food_name}'")
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            
            # Try recipes_results first (contains food-related images)
            if "recipes_results" in data and data["recipes_results"]:
                first_recipe = data["recipes_results"][0]
                thumbnail = first_recipe.get("thumbnail")
                if thumbnail:
                    result = {
                        "image_url": thumbnail,
                        "thumbnail": thumbnail,
                        "title": first_recipe.get("title", food_name),
                        "source": "google_recipes"
                    }
                    logger.info(f"[GoogleImagesAPI] Found recipe image for '{food_name}'")
                    return result
            
            # Try knowledge_graph images (encyclopedia-style images)
            if "knowledge_graph" in data:
                kg = data["knowledge_graph"]
                if "header_images" in kg and kg["header_images"]:
                    first_image = kg["header_images"][0]
                    result = {
                        "image_url": first_image.get("image"),
                        "thumbnail": first_image.get("image"),
                        "title": kg.get("title", food_name),
                        "source": "google_knowledge_graph"
                    }
                    logger.info(f"[GoogleImagesAPI] Found knowledge graph image for '{food_name}'")
                    return result
            
            # Second try: Google Images search (tbm=isch returns images_results)
            logger.info(f"[GoogleImagesAPI] Trying Google Images for: '{food_name}'")
            params["tbm"] = "isch"  # Image search
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            
            # Get images from images_results (Google Images results)
            if "images_results" in data and data["images_results"]:
                first_image = data["images_results"][0]
                result = {
                    "image_url": first_image.get("original"),
                    "thumbnail": first_image.get("thumbnail"),
                    "title": food_name,
                    "source": "google_images"
                }
                logger.info(f"[GoogleImagesAPI] Found image from Google Images for '{food_name}'")
                return result
            
            logger.warning(f"[GoogleImagesAPI] No images found for '{food_name}'")
            return None

        except requests.exceptions.Timeout:
            logger.error(f"[GoogleImagesAPI] Request timeout for '{food_name}'")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"[GoogleImagesAPI] Request error for '{food_name}': {e}")
            return None
        except Exception as e:
            logger.error(f"[GoogleImagesAPI] Unexpected error for '{food_name}': {e}")
            return None
