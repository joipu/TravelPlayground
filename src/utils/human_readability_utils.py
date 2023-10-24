import datetime

from src.utils.constants import (
    AVAILABILITY,
    DINNER,
    DINNER_PRICE,
    FOOD_TYPE,
    LUNCH,
    LUNCH_PRICE,
    RATING,
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
