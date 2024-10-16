import json
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from utils.ikyu_parse_utils import trim_availability_by_target_date_range
from utils.ikyu_search_utils import get_lunch_price_from_availability, get_dinner_price_from_availability
from utils.cache_utils import (
    type_japanese_to_chinese,
)

from utils.ikyu_search_utils import (
    search_restaurants_in_tokyo_yield,
)
from utils.constants import *

app = Flask(__name__)

CORS(
    app,
    origins="*",
    methods=["GET", "POST"],
)


@app.route("/api/say_hello", methods=["GET"])
def say_hello():
    # For testing
    return jsonify({"message": "Hello World!"})


def convert_restaurant_info_for_web(restaurant_info):
    # rewrite availability for web
    newAvailability = {}
    if AVAILABILITY in restaurant_info.keys():
        if RESERVATION_STATUS in restaurant_info[AVAILABILITY].keys():
            newAvailability["reservationStatus"] = restaurant_info[AVAILABILITY][
                RESERVATION_STATUS
            ]
        if LUNCH in restaurant_info[AVAILABILITY].keys():
            newAvailability[LUNCH] = restaurant_info[AVAILABILITY][LUNCH]
        if DINNER in restaurant_info[AVAILABILITY].keys():
            newAvailability[DINNER] = restaurant_info[AVAILABILITY][DINNER]
        newAvailability = trim_availability_by_target_date_range(
            newAvailability)

    return {
        "name": restaurant_info[RESTAURANT_NAME],
        "coverImageUrl": restaurant_info[COVER_IMAGE_URL],
        "type": type_japanese_to_chinese(restaurant_info[FOOD_TYPE]),
        "rating": restaurant_info[RATING],
        "reservationLink": restaurant_info[RESERVATION_LINK],
        "ikyuId": restaurant_info[IKYU_ID],
        "availability": newAvailability,
        "hardToReserve": restaurant_info[AVAILABILITY][HARD_TO_RESERVE],
        "lunchPrice": get_lunch_price_from_availability(restaurant_info[AVAILABILITY]),
        "dinnerPrice": get_dinner_price_from_availability(restaurant_info[AVAILABILITY]),
    }


def stream_restaurant_for_food_types_and_locations(foodTypes, locations):
    all_restaurants = search_restaurants_in_tokyo_yield(
        locations, foodTypes
    )
    for restaurant in all_restaurants:
        converted_restaurant = convert_restaurant_info_for_web(restaurant)
        yield f"data: {json.dumps(converted_restaurant)}\n\n"
    yield f"event: close\ndata: \n\n"


@app.route("/api/restaurant_search_stream_v2")
def restaurant_search_stream_v2():
    print("🔍 Getting restaurant search stream...")
    locationsAndFoodTypesString = request.args.get(
        "locationsAndFoodTypes", None)
    locationsAndFoodTypes = json.loads(locationsAndFoodTypesString)

    return Response(
        stream_restaurant_for_food_types_and_locations(
            locationsAndFoodTypes["foodTypes"], locationsAndFoodTypes["locations"]),
        content_type="text/event-stream",
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=6003)
