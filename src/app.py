import json
import uuid
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from utils.ikyu_parse_utils import trim_availability_by_target_date_range
from utils.ikyu_search_utils import get_lunch_price_from_availability, get_dinner_price_from_availability
from utils.constants import get_all_dates_in_range
from utils.cache_utils import (
    convert_food_types_in_japanese_to_chinese,
    convert_food_types_in_japanese_to_code,
    convert_tokyo_sub_regions_in_japanese_to_location_code,
    type_japanese_to_chinese,
)
from utils.constants import IKYU_ID
from utils.gpt_utils import (
    build_location_groups_for_tokyo,
    get_suggested_restaurant_type_codes,
)

from utils.ikyu_search_utils import (
    search_restaurants_in_tokyo_yield,
)
from utils.constants import *
from utils.ikyu_url_builders import (
    build_search_url_from_location_group_tokyo,
)
from utils.user_session_utils import get_user_session, save_user_session

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
        newAvailability = trim_availability_by_target_date_range(newAvailability)

    return {
        "name": restaurant_info[RESTAURANT_NAME],
        "type": type_japanese_to_chinese(restaurant_info[FOOD_TYPE]),
        "rating": restaurant_info[RATING],
        "reservationLink": restaurant_info[RESERVATION_LINK],
        "ikyuId": restaurant_info[IKYU_ID],
        "availability": newAvailability,
        "hardToReserve": restaurant_info[AVAILABILITY][HARD_TO_RESERVE],
        "lunchPrice": get_lunch_price_from_availability(restaurant_info[AVAILABILITY]),
        "dinnerPrice": get_dinner_price_from_availability(restaurant_info[AVAILABILITY]),
    }


@app.route("/api/get_locations_from_query", methods=["POST"])
def get_locations_from_query():
    data = request.get_json()

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

    # Get food types from query
    if (
        "foodTypes" in session.keys()
        and session["query"] == query
        and session["foodTypes"] != []
    ):  # if session is valid
        food_types = session["foodTypes"]
    else:
        food_types = get_suggested_restaurant_type_codes(query)

    # Update session
    session["locationGroups"] = loc_groups_json
    session["query"] = query
    session["foodTypes"] = food_types
    save_user_session(
        session_id,
        session,
    )

    # Build search url
    food_types_codes = convert_food_types_in_japanese_to_code(food_types)
    for loc_group_json in loc_groups_json:
        subregion_codes = convert_tokyo_sub_regions_in_japanese_to_location_code(
            loc_group_json["locations"],
        )
        loc_group_json["searchUrl"] = build_search_url_from_location_group_tokyo(
            subregion_codes, food_types_codes
        )

    return jsonify(
        {
            "sessionId": session_id,
            "locationGroups": loc_groups_json,
            "foodTypes": convert_food_types_in_japanese_to_chinese(food_types),
        }
    )


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

    plansForDay = []
    for day in get_all_dates_in_range():
        for locationGroup in locationGroups:
            plansForDay.append(
                {
                    "date": day,
                    "locationGroup": locationGroup,
                }
            )
    return jsonify(plansForDay)


def stream_restaurant_for_food_types_and_locations(foodTypes, locationGroup):
    all_restaurants = search_restaurants_in_tokyo_yield(
        locationGroup["locations"], foodTypes
    )
    for restaurant in all_restaurants:
        converted_restaurant = convert_restaurant_info_for_web(restaurant)
        yield f"data: {json.dumps(converted_restaurant)}\n\n"
    yield f"event: close\ndata: \n\n"


@app.route("/api/details_stream")
def sse():
    print("🔍 Getting details stream...")
    sessionId = request.args.get("sessionId", None)
    session = get_user_session(sessionId)
    if session == {}:
        raise Exception("Invalid session Id")
    if "foodTypes" not in session.keys():
        raise Exception("No food types found in session")
    foodTypes = session["foodTypes"]
    if foodTypes == []:
        raise Exception("No food types found in session")

    locationGroupString = request.args.get("locationGroup", None)
    print("locationGroupString: ", locationGroupString)
    locationGroup = json.loads(locationGroupString)
    return Response(
        stream_restaurant_for_food_types_and_locations(foodTypes, locationGroup),
        content_type="text/event-stream",
    )
    
@app.route("/api/restaurant_search_stream_v2")
def restaurant_search_stream_v2():
    print("🔍 Getting restaurant search stream...")
    locationGroup = {
        "locations": [
            # "押上",
            # "スカイツリー周辺"
        ],
        "reason": "您提到将去晴空塔，这对应于押上和スカイツリー周辺地区"
    }
    return Response(
        stream_restaurant_for_food_types_and_locations(ALL_FOOD_TYPES_EXCEPT_CHINESE, locationGroup),
        content_type="text/event-stream",
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=6002)
