from utils.network import get_response_from_google_place_text_search_api


def get_google_data(restaurant_search_name):
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
        return places[0]["rating"], places[0]["googleMapsUri"]
    else:
        print(f"❌ Restaurant not found in Google. "
              f"response: {response}"
              f"restaurant_search_name: {restaurant_search_name}")
        return None
