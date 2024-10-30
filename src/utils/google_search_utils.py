import json
from utils.network import get_response_from_google_place_text_search_api
from utils.redis_client import redis_client
from .cache_utils import get_cache_key_for_google

def get_google_data(ikyu_id, restaurant_search_name):
    cache_key = get_cache_key_for_google(ikyu_id)
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    response_data = get_response_from_google_place_text_search_api(
        f"{restaurant_search_name} in Tokyo, Japan",
    )

    response = response_data.json()
    """
    Example response:
    {
        "places": [
            {
                "rating": 4.5, 
                "displayName": {
                    "text": "Signature",
                    "languageCode": "en"
                }
            }
        ]
    }
    """
    places = response.get("places")
    if places and "rating" in places[0]:
        rating, google_maps_uri = places[0]["rating"], places[0]["googleMapsUri"]
        redis_client.set(cache_key, json.dumps((rating, google_maps_uri)), ex=86400)
        return rating, google_maps_uri
    else:
        print(f"❌ Restaurant not found in Google. "
              f"response: {response}"
              f"restaurant_search_name: {restaurant_search_name}")
        return None
