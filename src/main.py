import json
import sys
import os
import pandas as pd
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from src.config import (
    DIVIDE_AND_CONQUER,
    SEARCH_BY_CITY,
    SEARCH_IN_KYOTO,
    USE_KNOWN_URL,
    WORK_MODE,
)
from src.utils.cache_utils import (
    lookup_location_code,
    lookup_restaurant_type_code,
    lookup_tokyo_subregion_code,
)
from src.utils.gpt_utils import (
    build_location_groups_for_tokyo,
    get_gpt_recommendations,
    get_suggested_location_names,
    get_suggested_restaurant_type_codes,
    get_suggested_tokyo_subregion_codes,
    restaurant_list_in_human_readable_string,
)

from src.utils.human_readability_utils import (
    get_human_readable_restaurant_info_blob,
)
from src.utils.url_utils import build_query_url, build_query_urls_from_known_url
from .ikyu_search_parser import run_ikyu_search
from .utils.sorting_utils import sort_by_price
from .utils.constants import (
    LOCATIONS,
    LUNCH_PRICE,
    DINNER_PRICE,
    TOKYO_LOCATION_CODE,
)


def get_output_dir():
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return os.path.abspath(output_dir)


def print_restaurant_list(all_restaurants, filtered, output_file):
    output = restaurant_list_in_human_readable_string(all_restaurants, filtered)
    output_file = os.path.join(get_output_dir(), output_file)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output)


def build_search_urls_from_query(query, search_in_tokyo):
    restaurant_type_codes_japanese = get_suggested_restaurant_type_codes(query)
    restaurant_type_codes = [
        lookup_restaurant_type_code(code_japanese)
        for code_japanese in restaurant_type_codes_japanese
    ]
    if search_in_tokyo:
        location_code = TOKYO_LOCATION_CODE
        subregion_codes_japanese = get_suggested_tokyo_subregion_codes(query)

    else:
        location_code_japanese = get_suggested_location_names(query)[0]
        location_code = lookup_location_code(location_code_japanese)
        subregion_codes_japanese = []
    subregion_codes = [
        lookup_tokyo_subregion_code(code_japanese)
        for code_japanese in subregion_codes_japanese
    ]
    url = build_query_url(restaurant_type_codes, location_code, subregion_codes)
    urls = build_query_urls_from_known_url(url)
    return urls


def get_restaurants_from_urls(urls):
    all_restaurants = []
    for url in urls:
        restaurants_per_url = run_ikyu_search(url)
        all_restaurants.extend(restaurants_per_url)
    return all_restaurants


def divide_and_conquer(query):
    restaurant_types_japanese = get_suggested_restaurant_type_codes(query)
    # restaurant_types_japanese = [
    #     "和食,懐石・会席料理,割烹・小料理,京料理,魚介・海鮮料理,鉄板焼,寿司,天ぷら,すき焼き／しゃぶしゃぶ,焼鳥,鍋,うなぎ料理,和食その他,中華,中国料理,飲茶・点心,中華その他,焼肉,韓国料理,ブッフェ,ラウンジ,バー,ワインバー,ビアガーデン・BBQ"
    # ]
    restaurant_types = [
        lookup_restaurant_type_code(code_japanese)
        for code_japanese in restaurant_types_japanese
    ]

    # with open("search_groups.json", "r") as f:
    #     search_groups = json.load(f)
    search_groups = build_location_groups_for_tokyo(query)
    # print("Search groups: ")
    # print(json.dumps(search_groups, indent=4))

    # Each search group is responsible for one location group, like first x pages of one url.
    for search_group in search_groups:
        print(f"Searching for {', '.join(search_group[LOCATIONS])}")
        subregion_codes = [
            lookup_tokyo_subregion_code(subregion_japanese)
            for subregion_japanese in search_group[LOCATIONS]
        ]
        url = build_query_url(restaurant_types, TOKYO_LOCATION_CODE, subregion_codes)
        urls = build_query_urls_from_known_url(url, pages_to_search=1)
        all_restaurants = get_restaurants_from_urls(urls)
        recommendations_string = get_gpt_recommendations(
            query, search_group, all_restaurants
        )
        location_group_japanese = ", ".join(search_group[LOCATIONS])
        print(f"Recommendations for {location_group_japanese}\n")
        print(recommendations_string)


def main():
    if WORK_MODE == DIVIDE_AND_CONQUER:
        divide_and_conquer(sys.argv[1])
    else:
        if WORK_MODE == USE_KNOWN_URL:
            urls = build_query_urls_from_known_url(sys.argv[1])
        elif WORK_MODE == SEARCH_IN_KYOTO:
            urls = build_search_urls_from_query(sys.argv[1], True)
        elif WORK_MODE == SEARCH_BY_CITY:
            urls = build_search_urls_from_query(sys.argv[1], False)

        # Find restaurants for all URLs
        all_restaurants = []
        for url in urls:
            restaurants_per_url = run_ikyu_search(url)
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
