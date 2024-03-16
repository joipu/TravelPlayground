import datetime
from utils.cache_utils import type_japanese_to_chinese

from utils.constants import (
    AVAILABILITY,
    DINNER,
    DINNER_PRICE,
    FOOD_TYPE,
    LUNCH,
    LUNCH_PRICE,
    RATING,
    RESERVATION_LINK,
    RESERVATION_STATUS,
    RESTAURANT_NAME,
    WALKING_TIME,
)


def yenToUSD(yen):
    return int(yen / 149.0)


def describe_availability(data):
    # Sort the data by date
    sorted_dates = sorted(data.keys())

    # Initialize variables
    output = "Available on "
    prev_date = None
    range_start = None

    for _, date_str in enumerate(sorted_dates):
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

        # Check for consecutive dates
        if prev_date is not None and date_obj == prev_date + datetime.timedelta(days=1):
            if range_start is None:
                range_start = prev_date
        else:
            if range_start is not None:
                output += f"{range_start.strftime('%m/%d')} to {prev_date.strftime('%m/%d')}, "
                range_start = None
            else:
                output += f"{prev_date.strftime('%m/%d')}, " if prev_date else ""

        prev_date = date_obj

    # Add the last date or range
    if range_start is not None:
        output += (
            f"{range_start.strftime('%m/%d')} through {prev_date.strftime('%m/%d')}"
        )
    else:
        output += f"{prev_date.strftime('%m/%d')}"

    return output


def restaurant_one_line(restaurant_info):
    name = restaurant_info[RESTAURANT_NAME]
    type = type_japanese_to_chinese(restaurant_info[FOOD_TYPE])
    rating = restaurant_info[RATING]

    lunch_special_icon = ""
    if restaurant_info[LUNCH_PRICE] > 0 and restaurant_info[DINNER_PRICE] > 0:
        if restaurant_info[LUNCH_PRICE] < 0.5 * restaurant_info[DINNER_PRICE]:
            lunch_special_icon = "🍱"

    cheap_price = 99999
    cheap_icon = ""
    if restaurant_info[LUNCH_PRICE] > 0:
        cheap_price = restaurant_info[LUNCH_PRICE]
    if (
        restaurant_info[DINNER_PRICE] > 0
        and restaurant_info[DINNER_PRICE] < cheap_price
    ):
        cheap_price = restaurant_info[DINNER_PRICE]
    if cheap_price < 10000:
        cheap_icon = "💰"
    if cheap_price < 7000:
        cheap_icon = "💰💰"
    if cheap_price < 5000:
        cheap_icon = "💰💰💰"

    return f"{cheap_icon}{lunch_special_icon} {name}, {type}, {rating}, lunch: {restaurant_info[LUNCH_PRICE]}, dinner: {restaurant_info[DINNER_PRICE]}, {restaurant_info[RESERVATION_LINK]}"


def get_human_readable_restaurant_info_blob(restaurant, empty_if_no_availability=False):
    output = ""
    output += f"{restaurant[RESTAURANT_NAME]}\n"
    output += f"{restaurant[FOOD_TYPE]}\n"
    output += f"Rating: {restaurant[RATING]}/5\n"
    output += f"Location: {restaurant[WALKING_TIME]}\n"
    output += f"Lunch: ${yenToUSD(restaurant[LUNCH_PRICE])}\n"
    output += f"Dinner: ${yenToUSD(restaurant[DINNER_PRICE])}\n"
    is_available = False
    if LUNCH in restaurant[AVAILABILITY].keys():
        is_available = True
        output += "Lunch availability:\n"
        output += f"{describe_availability(restaurant[AVAILABILITY][LUNCH])}\n"
    if DINNER in restaurant[AVAILABILITY].keys():
        is_available = True
        output += "Dinner availability:\n"
        output += f"{describe_availability(restaurant[AVAILABILITY][DINNER])}\n"
    if RESERVATION_STATUS in restaurant[AVAILABILITY].keys():
        if restaurant[AVAILABILITY][RESERVATION_STATUS].endswith("True"):
            prefix = "👍"
            is_available = True
        else:
            prefix = "❌"
        output += f"{prefix} {restaurant[AVAILABILITY][RESERVATION_STATUS]}\n"
    output += "\n"
    if empty_if_no_availability:
        if is_available:
            return output
        return ""
    else:
        return output
