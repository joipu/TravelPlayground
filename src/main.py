import sys
import os
import pandas as pd
from src.config import (
    DIVIDE_AND_CONQUER,
    SEARCH_BY_CITY,
    SEARCH_IN_KYOTO,
    USE_KNOWN_URL,
    WORK_MODE,
)
from src.utils.all_restaurant_search import (
    build_location_to_restaurant_mapping,
    restaurant_availability_by_date,
)
from src.utils.cache_utils import (
    get_all_cached_restaurant_info,
    get_output_dir,
    lookup_restaurant_type_code,
    lookup_tokyo_subregion_code,
)
from src.utils.file_utils import (
    read_json_from_file,
    write_content_to_file,
    write_json_to_file_full_path,
)
from src.utils.gpt_utils import (
    get_gpt_recommendations,
    restaurant_list_in_human_readable_string,
)
from src.utils.ikyu_availability_utils import (
    get_availabilities_for_ikyu_restaurant,
    get_html_from_ikyu,
)

from src.utils.ikyu_url_builders import (
    build_ikyu_query_url,
    build_ikyu_query_urls_from_known_url,
    build_search_urls_from_query,
)
from src.utils.plan_reservation import find_best_combinations, get_best_combos
from .utils.ikyu_search_utils import (
    restaurants_from_search_urls,
    restaurants_from_search_url,
)
from .utils.sorting_utils import sort_by_price, sort_by_rating
from .utils.constants import *


def print_restaurant_list(all_restaurants, filtered, output_file):
    output = restaurant_list_in_human_readable_string(all_restaurants, filtered)
    output_file = os.path.join(get_output_dir(), output_file)
    write_content_to_file(output, output_file)


def get_recommendation_for_location_group(location_group, restaurant_types, query):
    print(f"Searching for {', '.join(location_group[LOCATIONS])}")
    subregion_codes = [
        lookup_tokyo_subregion_code(subregion_japanese)
        for subregion_japanese in location_group[LOCATIONS]
    ]
    url = build_ikyu_query_url(restaurant_types, TOKYO_LOCATION_CODE, subregion_codes)
    urls = build_ikyu_query_urls_from_known_url(url, pages_to_search=2)
    all_restaurants = restaurants_from_search_urls(urls, use_cache=False)
    recommendations_string = get_gpt_recommendations(
        query, restaurant_types, all_restaurants, "2023-12-03", "2023-12-09"
    )
    location_group_japanese = ", ".join(location_group[LOCATIONS])
    output_dir = get_output_dir()
    file_name = f"{location_group_japanese}.txt"
    print(f"Recommendations for {location_group_japanese}\n")

    print(recommendations_string)
    write_content_to_file(recommendations_string, os.path.join(output_dir, file_name))
    return recommendations_string


def divide_and_conquer(query):
    # restaurant_types_japanese = get_suggested_restaurant_type_codes(query)
    restaurant_types_japanese = "ステーキ／グリル料理,和食,懐石・会席料理,割烹・小料理,京料理,魚介・海鮮料理,鉄板焼,寿司,天ぷら,すき焼き／しゃぶしゃぶ,焼鳥,鍋,うなぎ料理,和食その他,焼肉,ブッフェ,ラウンジ,バー,ワインバー,ビアガーデン・BBQ".split(
        ","
    )

    restaurant_types = [
        lookup_restaurant_type_code(code_japanese)
        for code_japanese in restaurant_types_japanese
    ]
    # print(f"Restaurant types: {', '.join(restaurant_types_japanese)}")
    # return

    file_name = "search_groups.json"
    current_dir = os.path.dirname(__file__)
    aboslute_file_path = os.path.join(current_dir, file_name)
    search_groups = read_json_from_file(aboslute_file_path)
    # search_groups = build_location_groups_for_tokyo(query)
    # print("Search groups: ")
    # print(json.dumps(search_groups, indent=4))

    # Each search group is responsible for one location group, like first x pages of one url.
    for search_group in search_groups:
        get_recommendation_for_location_group(search_group, restaurant_types, query)


def load_saved_location_groups():
    file_name = "search_groups.json"
    current_dir = os.path.dirname(__file__)
    aboslute_file_path = os.path.join(current_dir, file_name)
    search_groups = read_json_from_file(aboslute_file_path)
    return search_groups


def do_search():
    restaurant_dict = get_all_cached_restaurant_info()
    all_restaurants = list(restaurant_dict.values())
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


def main():
    location_groups = load_saved_location_groups()
    get_best_combos(location_groups)

    # print("hello")
    # print(combos)
    # for combo in combos:
    # print(combo)
    return
    # restaurant_availability_by_date()
    # return
    if WORK_MODE == DIVIDE_AND_CONQUER:
        divide_and_conquer(sys.argv[1])
    else:
        if WORK_MODE == USE_KNOWN_URL:
            urls = build_ikyu_query_urls_from_known_url(sys.argv[1])
        elif WORK_MODE == SEARCH_IN_KYOTO:
            urls = build_search_urls_from_query(sys.argv[1], True)
        elif WORK_MODE == SEARCH_BY_CITY:
            urls = build_search_urls_from_query(sys.argv[1], False)

        # Find restaurants for all URLs
        all_restaurants = []
        for url in urls:
            restaurants_per_url = restaurants_from_search_url(url, use_cache=False)
            print(f"🚧 Found {len(restaurants_per_url)} restaurants for {url} 🚧")
            all_restaurants.extend(restaurants_per_url)

        # Post-process the list of restaurants
        restaurants_sorted_by_lunch_price = sort_by_price(all_restaurants, LUNCH_PRICE)
        restaurants_sorted_by_dinner_price = sort_by_price(
            all_restaurants, DINNER_PRICE
        )

        # Create a DataFrame from data
        df1 = pd.DataFrame(restaurants_sorted_by_lunch_price)
        df2 = pd.DataFrame(restaurants_sorted_by_dinner_price)

        # Save the DataFrame to a CSV file
        output_dir = get_output_dir()
        df1.to_csv(os.path.join(output_dir, "lunch_restaurants.csv"), index=True)
        df2.to_csv(os.path.join(output_dir, "dinner_restaurants.csv"), index=True)

        print_restaurant_list(all_restaurants, False, "all_restaurants.txt")
        print_restaurant_list(all_restaurants, True, "restaurants_with_spots.txt")

    print("🆗 Finished!")


if __name__ == "__main__":
    main()
