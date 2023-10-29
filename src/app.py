import os
import uuid
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from src.utils.cache_utils import (
    convert_japanese_types_in_japanese_to_code,
    convert_tokyo_sub_regions_in_japanese_to_location_code,
    get_all_restaurant_type_japanese,
    get_cache_location_groups_from_query,
    get_cached_restaurant_info_by_ikyu_id,
    type_japanese_to_chinese,
)
from src.utils.constants import IKYU_ID
from src.utils.file_utils import read_json_from_file
from src.utils.gpt_utils import build_location_groups_for_tokyo, get_gpt_recommendations

from src.utils.ikyu_search_utils import (
    restaurants_from_search_urls,
    search_restaurants_in_tokyo,
)
from src.utils.constants import *
from src.utils.ikyu_url_builders import (
    build_ikyu_query_url,
    build_ikyu_query_urls_from_known_url,
    build_search_url_from_location_group_tokyo,
)
from src.utils.user_session_utils import get_user_session, save_user_session

app = Flask(__name__)
CORS(
    app,
    origins="*",
    methods=["GET", "POST"],
)


@app.route("/api/say_hello", methods=["GET"])
def say_hello():
    return jsonify({"message": "Hello World!"})


def convert_restaurant_info_for_web(restaurant_info):
    newAvailability = {}
    if AVAILABILITY in restaurant_info.keys():
        if RESERVATION_STATUS in restaurant_info[AVAILABILITY].keys():
            newAvailability["reservationStatus"] = restaurant_info[AVAILABILITY][
                RESERVATION_STATUS
            ]
        if LUNCH in restaurant_info[AVAILABILITY].keys():
            newAvailability["lunch"] = restaurant_info[AVAILABILITY][LUNCH]
        if DINNER in restaurant_info[AVAILABILITY].keys():
            newAvailability["dinner"] = restaurant_info[AVAILABILITY][DINNER]

    return {
        "name": restaurant_info[RESTAURANT_NAME],
        "type": type_japanese_to_chinese(restaurant_info[FOOD_TYPE]),
        "lunchPrice": restaurant_info[LUNCH_PRICE],
        "dinnerPrice": restaurant_info[DINNER_PRICE],
        "rating": restaurant_info[RATING],
        "reservationLink": restaurant_info[RESERVATION_LINK],
        "walkingTime": restaurant_info[WALKING_TIME],
        "ikyuId": restaurant_info[IKYU_ID],
        "availability": newAvailability,
    }


@app.route("/api/get_locations_from_query", methods=["POST"])
def get_locations_from_query():
    data = request.get_json()
    isSessionValid = False

    # If doesn't have session id, error out.
    if "sessionId" not in data.keys() or data["sessionId"] == "":
        raise Exception("No session id in query")

    session_id = data["sessionId"]
    print("session_id: ", session_id)
    session = get_user_session(session_id)
    if session == {}:
        raise Exception("No valid session id in query")

    # Do not modify session in this section.
    if "query" in data.keys() and data["query"] != "":
        query = data["query"]
    elif "query" in session.keys():
        query = session["query"]
    else:
        raise Exception("No query found")

    # Get loc_group_json
    if (
        "locationGroups" in session.keys()
        and session["query"] == query
        and session["locationGroups"] != []
    ):
        loc_groups_json = session["locationGroups"]
    else:
        loc_groups_json = build_location_groups_for_tokyo(query)

    for loc_group_json in loc_groups_json:
        subregion_codes = convert_tokyo_sub_regions_in_japanese_to_location_code(
            loc_group_json["locations"]
        )
        loc_group_json["searchUrl"] = build_search_url_from_location_group_tokyo(
            subregion_codes
        )

    # Update session
    session["locationGroups"] = loc_groups_json
    session["query"] = query
    save_user_session(
        session_id,
        session,
    )

    return jsonify({"sessionId": session_id, "locationGroups": loc_groups_json})


@app.route("/api/get_query_for_session", methods=["POST"])
def get_query_for_session():
    data = request.get_json()
    session_id = data["sessionId"]
    print("get_query_for_session: ", session_id)
    session = get_user_session(session_id)
    if session == {}:
        sessionId = str(uuid.uuid4())
        session = {"query": "", "sessionId": sessionId}
        save_user_session(sessionId, session)
        return jsonify(session)
    response = jsonify({"query": session["query"], "sessionId": session_id})
    print("get_query_for_session response: ", response)
    return response


@app.route("/api/get_schedule_from_locations", methods=["POST"])
def get_schedule_from_locations():
    data = request.get_json()
    try:
        session_id = data["sessionId"]
        session = get_user_session(session_id)
        locationGroups = session["locationGroups"]
    except Exception as error:
        raise Exception("Invalid session Id")

    month = "2023-12"
    plansForDay = []
    for i in range(3, 10):
        day = f"{month}-{i:02}"
        for locationGroup in locationGroups:
            plansForDay.append(
                {
                    "date": day,
                    "locationGroup": locationGroup,
                }
            )
    return jsonify(plansForDay)


@app.route("/api/get_other_restaurants", methods=["POST"])
def get_other_restaurants():
    data = request.get_json()
    locationGroup = data["locationGroup"]
    # existing_restaurant_ids = data["existingRestaurantIds"]
    existing_restaurant_ids = []
    # all_types = get_all_restaurant_type_japanese()
    restaurant_types_japanese = "ステーキ／グリル料理,和食,懐石・会席料理,割烹・小料理,京料理,魚介・海鮮料理,鉄板焼,寿司,天ぷら,すき焼き／しゃぶしゃぶ,焼鳥,鍋,うなぎ料理,和食その他,焼肉,ブッフェ,ラウンジ,バー,ワインバー,ビアガーデン・BBQ".split(
        ","
    )
    all_restaurants = search_restaurants_in_tokyo(
        locationGroup["locations"], restaurant_types_japanese, True
    )
    filtered_restaurants = [
        restaurant
        for restaurant in all_restaurants
        if restaurant[IKYU_ID] not in existing_restaurant_ids
    ]
    restaurant_for_web = [
        convert_restaurant_info_for_web(restaurant)
        for restaurant in filtered_restaurants
    ]
    return jsonify(restaurant_for_web)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=6002)
