import os
from utils.constants import get_all_dates_in_range
from utils.cache_utils import (
    get_all_cached_restaurant_info,
    get_full_output_path,
    get_output_dir,
)
from utils.constants import *
from utils.file_utils import write_json_to_file_full_path
from utils.human_readability_utils import restaurant_one_line
from utils.sorting_utils import sort_by_rating


def load_all_restaurants_in_array():
    restaurant_dict = get_all_cached_restaurant_info()
    all_restaurants = list(restaurant_dict.values())
    return all_restaurants


def all_restaurant_with_lunch_half_dinner_price():
    all_restaurants = load_all_restaurants_in_array()
    recorded_restaurants = []
    for restaurant_info in all_restaurants:
        if restaurant_info[RATING] != None and restaurant_info[RATING] > 3.5:
            if (
                restaurant_info[LUNCH_PRICE] != None
                and restaurant_info[LUNCH_PRICE] > 0
                and restaurant_info[DINNER_PRICE] != None
            ):
                if restaurant_info[LUNCH_PRICE] < (0.5 * restaurant_info[DINNER_PRICE]):
                    recorded_restaurants.append(restaurant_info)

    recorded_restaurants = sort_by_rating(recorded_restaurants)
    output_file_name = "restaurant_lunch_half_dinner_price.json"
    full_path = os.path.join(get_output_dir(), output_file_name)
    write_json_to_file_full_path(full_path, recorded_restaurants)
    return recorded_restaurants


def restaurant_cost_less_than_10000():
    all_restaurants = load_all_restaurants_in_array()
    recorded_restaurants = []
    for restaurant_info in all_restaurants:
        if restaurant_info[RATING] != None and restaurant_info[RATING] > 3.5:
            cheap_price = 99999
            if restaurant_info[LUNCH_PRICE] > 0:
                cheap_price = restaurant_info[LUNCH_PRICE]
            if (
                restaurant_info[DINNER_PRICE] > 0
                and restaurant_info[DINNER_PRICE] < cheap_price
            ):
                cheap_price = restaurant_info[DINNER_PRICE]
            if cheap_price < 10000:
                recorded_restaurants.append(restaurant_info)

    recorded_restaurants = sort_by_rating(recorded_restaurants)
    output_file_name = "restaurant_cost_less_than_10000.json"
    full_path = os.path.join(get_output_dir(), output_file_name)
    write_json_to_file_full_path(full_path, recorded_restaurants)
    return recorded_restaurants


def remove_duplicate_restaurants(all_restaurant):
    # remove duplicates by restaurant[IKYU_ID]
    seen = set()
    unique_restaurants = []
    for restaurant in all_restaurant:
        if restaurant[IKYU_ID] not in seen:
            unique_restaurants.append(restaurant)
            seen.add(restaurant[IKYU_ID])
    return unique_restaurants


def restaurant_availability_by_date():
    all_restaurants = []
    all_restaurants.extend(restaurant_cost_less_than_10000())
    all_restaurants.extend(all_restaurant_with_lunch_half_dinner_price())
    all_restaurants = remove_duplicate_restaurants(all_restaurants)

    all_days = []
    for day in get_all_dates_in_range():
        available_restaurant_for_lunch = []
        available_restaurant_for_dinner = []
        for restaurant_info in all_restaurants:
            if AVAILABILITY in restaurant_info.keys():
                if LUNCH in restaurant_info[AVAILABILITY].keys():
                    if day in restaurant_info[AVAILABILITY][LUNCH].keys():
                        available_restaurant_for_lunch.append(restaurant_info)
                if DINNER in restaurant_info[AVAILABILITY].keys():
                    if day in restaurant_info[AVAILABILITY][DINNER].keys():
                        available_restaurant_for_dinner.append(restaurant_info)
        available_restaurant_for_lunch = sort_by_rating(available_restaurant_for_lunch)
        available_restaurant_for_dinner = sort_by_rating(
            available_restaurant_for_dinner
        )
        day_json = {
            "date": day,
            "lunch": [
                restaurant_one_line(restaurant_info)
                for restaurant_info in available_restaurant_for_lunch
            ],
            "dinner": [
                restaurant_one_line(restaurant_info)
                for restaurant_info in available_restaurant_for_dinner
            ],
        }
        all_days.append(day_json)
    write_json_to_file_full_path(
        get_full_output_path("restaurant_availability_by_date.json"), all_days
    )
