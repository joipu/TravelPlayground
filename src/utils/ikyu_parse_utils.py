from datetime import datetime, timedelta

from utils.network import get_response_json_from_url_with_headers
from utils.constants import *
from utils.ikyu_availability_utils import filter_availability, has_available_dates_after


def clean_string(input_string):
    cleaned_string = " ".join(input_string.split()).strip()
    return cleaned_string


def get_availability_json_for_ikyu_id(ikuy_id):
    url = f"https://restaurant.ikyu.com/api/v1/restaurants/{ikuy_id}/calendar"

    data = get_response_json_from_url_with_headers(url)

    meal_types = ["breakfast", "lunch", "dinner", "teatime"]
    availability = {}
    for meal in meal_types:
        for month in data[meal]:
            for day in month["days"]:
                if day["has_inventory"]:
                    day_num = day["day"]
                    mon_num = day["month"]
                    year_num = day["year"]
                    date_string = f"{year_num:04d}-{mon_num:02d}-{day_num:02d}"
                    if meal not in availability:
                        availability[meal] = {}
                    availability[meal][date_string] = day["best_price"]

    # sort the dictionary by date
    availability = dict(sorted(availability.items()))
    return availability


def get_hard_to_reserve_value(availability):
    # """
    # {
    #     "2024-03-17": 3800,
    #     "2024-03-18": 3800,
    #     "2024-03-20": 3800,
    #     ...
    # }
    # """
    # Only available dates are in the dictionary
    # If there is less than 5 days in next 30 days that are available, return True
    # Get all the dates in the next 30 days
    available_reservation_dates = list(availability.keys())
    # Make sure reservation dates have availability after 30 days from today
    has_reservation_after_30_days = has_available_dates_after(
        availability, str(datetime.now().date() + timedelta(days=30)))
    if not has_reservation_after_30_days:
        return False
    next_30_days = [str(datetime.now().date() + timedelta(days=i))
                    for i in range(0, 30)]
    available_next_30_days = [
        date for date in next_30_days if date in available_reservation_dates]

    if len(available_next_30_days) < HARD_TO_RESERVE_THRESHOLD:
        hard_to_reserve = True
    else:
        hard_to_reserve = False

    return hard_to_reserve


def trim_availability_by_target_date_range(availability, start_date: str, end_date: str):
    if DINNER not in availability:
        filtered_dinner_json = {}
    else:
        filtered_dinner_json = filter_availability(
            availability[DINNER],
            start_date,
            end_date,
        )

    if LUNCH not in availability:
        filtered_lunch_json = {}
    else:
        filtered_lunch_json = filter_availability(
            availability[LUNCH],
            start_date,
            end_date,
        )

    availability = {
        DINNER: filtered_dinner_json,
        LUNCH: filtered_lunch_json
    }
    return availability


def get_availability_ikyu(ikyu_id, start_date: str):
    raw_availability = get_availability_json_for_ikyu_id(ikyu_id)

    # Check if reservation is open
    is_reservation_open = False
    if DINNER in raw_availability.keys() and raw_availability[DINNER].keys():
        is_reservation_open = has_available_dates_after(
            raw_availability[DINNER], start_date
        )
    if not is_reservation_open:
        is_reservation_open = has_available_dates_after(
            raw_availability[LUNCH], start_date
        )

    availability = raw_availability
    hard_to_reserve_lunch = (LUNCH in raw_availability) and get_hard_to_reserve_value(
        raw_availability[LUNCH])
    hard_to_reserve_dinner = (DINNER in raw_availability) and get_hard_to_reserve_value(
        raw_availability[DINNER])
    availability[HARD_TO_RESERVE] = hard_to_reserve_lunch or hard_to_reserve_dinner
    availability[
        RESERVATION_STATUS
    ] = f"Likely open for reservation after {start_date}: {is_reservation_open}"

    return availability
