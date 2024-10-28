import json
import urllib.parse
from datetime import datetime
from dateutil.relativedelta import relativedelta
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

from utils.tabelog_search_utils import get_tabelog_data
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

def parse_dates_str_from_request(request):
    DATE_FORMAT = '%Y-%m-%d'
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, DATE_FORMAT).date()
        except ValueError:
            return "Invalid startDate format. Expected YYYY-MM-DD.", 400
    else:
        start_date = datetime.today().date()

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, DATE_FORMAT).date()
        except ValueError:
            return "Invalid endDate format. Expected YYYY-MM-DD.", 400
    else:
        end_date = start_date + relativedelta(months=1)

    # Validate dates
    if end_date < start_date:
        return "endDate must be after startDate.", 400

    return start_date.strftime(DATE_FORMAT), end_date.strftime(DATE_FORMAT)


def convert_restaurant_info_for_web(restaurant_info, start_date, end_date):
    # rewrite availability for web
    new_availability = {}
    if AVAILABILITY in restaurant_info.keys():
        if RESERVATION_STATUS in restaurant_info[AVAILABILITY].keys():
            new_availability["reservationStatus"] = restaurant_info[AVAILABILITY][
                RESERVATION_STATUS
            ]
        if LUNCH in restaurant_info[AVAILABILITY].keys():
            new_availability[LUNCH] = restaurant_info[AVAILABILITY][LUNCH]
        if DINNER in restaurant_info[AVAILABILITY].keys():
            new_availability[DINNER] = restaurant_info[AVAILABILITY][DINNER]
        new_availability = trim_availability_by_target_date_range(
            new_availability, start_date, end_date)

    return {
        "name": restaurant_info[RESTAURANT_NAME],
        "coverImageUrl": restaurant_info[COVER_IMAGE_URL],
        "type": type_japanese_to_chinese(restaurant_info[FOOD_TYPE]),
        "rating": restaurant_info[RATING],
        "reservationLink": restaurant_info[RESERVATION_LINK],
        "ikyuId": restaurant_info[IKYU_ID],
        "availability": new_availability,
        "hardToReserve": restaurant_info[AVAILABILITY][HARD_TO_RESERVE],
        "lunchPrice": get_lunch_price_from_availability(restaurant_info[AVAILABILITY]),
        "dinnerPrice": get_dinner_price_from_availability(restaurant_info[AVAILABILITY]),
    }


def stream_restaurant_for_food_types_and_locations(
        food_types,
        locations,
        sort_option,
        start_date: str,
        end_date: str,
        num_people
):
    all_restaurants = search_restaurants_in_tokyo_yield(
        locations, food_types, sort_option, start_date, num_people
    )
    for restaurant in all_restaurants:
        converted_restaurant = convert_restaurant_info_for_web(restaurant, start_date, end_date)
        yield f"data: {json.dumps(converted_restaurant)}\n\n"
    yield f"event: close\ndata: \n\n"


def stream_tabelog_score_and_link_for_restaurants(restaurant_names):
    for restaurant_name in restaurant_names:
        tabelog_data = get_tabelog_data(restaurant_name)
        if tabelog_data is not None:
            score, link = tabelog_data
            yield f"data: {json.dumps({'name': restaurant_name, 'score': score, 'link': link})}\n\n"
        else:
            yield f"data: {json.dumps({'name': restaurant_name, 'score': None, 'link': None})}\n\n"
    yield "event: close\ndata: \n\n"


@app.route("/api/restaurant_search_stream_v2")
def restaurant_search_stream_v2():
    print("🔍 Getting restaurant search stream...")
    locations_and_food_types_string = request.args.get(
        "locationsAndFoodTypes", None)
    locations_and_food_types = json.loads(locations_and_food_types_string)
    sort_option = request.args.get("sortOption", "top-picks")
    start_date, end_date = parse_dates_str_from_request(request)
    num_people = request.args.get("numPeople", 2)

    return Response(
        stream_restaurant_for_food_types_and_locations(
            locations_and_food_types["foodTypes"],
            locations_and_food_types["locations"],
            sort_option,
            start_date,
            end_date,
            num_people
        ),
        content_type="text/event-stream",
    )


@app.route("/api/v1/restaurant_tabelog_score_link", methods=["GET"])
def restaurant_tabelog_score_link_v1():
    print("🔍 Getting tabelog restaurant score and link stream...")
    restaurant_names_string = request.args.get("restaurantNames", None)
    if restaurant_names_string:
        restaurant_names = json.loads(restaurant_names_string)
        return Response(
            stream_tabelog_score_and_link_for_restaurants(restaurant_names),
            content_type="text/event-stream"
        )
    else:
        return Response("No restaurant names provided", status=400)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=6003)
