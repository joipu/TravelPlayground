import os
from src.utils.cache_utils import (
    get_all_cached_restaurant_info,
    get_cache_file_for_location_group,
    get_cache_location_groups_from_query,
    get_full_output_path,
    get_output_dir,
    store_cached_restaurant_info_by_ikyu_id,
    type_japanese_to_chinese,
)
from src.utils.constants import *
from src.utils.file_utils import write_json_to_file_full_path
from src.utils.human_readability_utils import restaurant_one_line
from src.utils.ikyu_search_utils import search_restaurants_in_tokyo
from src.utils.sorting_utils import sort_by_rating


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


def fix_restaurant_info():
    all_restaurants_by_id = get_all_cached_restaurant_info()
    for key in all_restaurants_by_id.keys():
        restaurant_info = all_restaurants_by_id[key]
        restaurant_info[IKYU_ID] = key
        store_cached_restaurant_info_by_ikyu_id(key, restaurant_info)


def restaurant_availability_by_date():
    all_restaurants = []
    all_restaurants.extend(restaurant_cost_less_than_10000())
    all_restaurants.extend(all_restaurant_with_lunch_half_dinner_price())
    all_restaurants = remove_duplicate_restaurants(all_restaurants)

    month = "2023-12"
    all_days = []
    for i in range(4, 10):
        day = f"{month}-{i:02}"
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


def build_location_to_restaurant_mapping():
    loc_groups_json = get_cache_location_groups_from_query()
    restaurant_types_japanese = "ステーキ／グリル料理,和食,懐石・会席料理,割烹・小料理,京料理,魚介・海鮮料理,鉄板焼,寿司,天ぷら,すき焼き／しゃぶしゃぶ,焼鳥,鍋,うなぎ料理,和食その他,焼肉,ブッフェ,ラウンジ,バー,ワインバー,ビアガーデン・BBQ".split(
        ","
    )
    for loc_group in loc_groups_json:
        # get all the restaurants
        all_restaurants = search_restaurants_in_tokyo(
            loc_group["locations"], restaurant_types_japanese, use_cache=True
        )

        # cache_file_name = "_".join(loc_group["locations"]) + ".json"
        cache_file_path = get_cache_file_for_location_group(loc_group)
        all_restaurant_ids = [restaurant[IKYU_ID] for restaurant in all_restaurants]
        write_json_to_file_full_path(cache_file_path, all_restaurant_ids)
