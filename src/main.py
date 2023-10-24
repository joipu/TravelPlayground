import sys
import os
import pandas as pd
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from src.config import PAGES_TO_SEARCH, SEARCH_IN_KYOTO, USE_KNOWN_URL
from src.utils.cache_utils import (
    lookup_location_code,
    lookup_restaurant_type_code,
    lookup_tokyo_subregion_code,
)
from src.utils.gpt_utils import (
    get_suggested_location_names,
    get_suggested_restaurant_type_codes,
    get_suggested_tokyo_subregion_codes,
)

from src.utils.human_readability_utils import (
    get_human_readable_restaurant_info_blob,
)
from src.utils.url_utils import build_query_url, build_query_urls_from_known_url
from .ikyu_search_parser import run_ikyu_search
from .utils.sorting_utils import sort_by_price
from .utils.constants import (
    LUNCH_PRICE,
    DINNER_PRICE,
)


def get_output_dir():
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return os.path.abspath(output_dir)


def restaurant_list_in_human_readable_string(all_restaurants, filtered):
    all_results = ""
    for restaurant in all_restaurants:
        output = get_human_readable_restaurant_info_blob(restaurant, filtered)
        if output:
            all_results += output + "\n\n"
    return all_results


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
        location_code = "03001"
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


def main():
    if USE_KNOWN_URL:
        urls = build_query_urls_from_known_url(sys.argv[1])
    else:
        urls = build_search_urls_from_query(sys.argv[1], SEARCH_IN_KYOTO)

    # Find restaurants for all URLs
    all_restaurants = []
    for url in urls:
        restaurants_per_url = run_ikyu_search(url)
        print(f"🚧 Found {len(restaurants_per_url)} restaurants for {url} 🚧")
        all_restaurants.extend(restaurants_per_url)

    # Post-process the list of restaurants
    restaurants_sorted_by_lunch_price = sort_by_price(all_restaurants, LUNCH_PRICE)
    restaurants_sorted_by_dinner_price = sort_by_price(all_restaurants, DINNER_PRICE)

    # Create a DataFrame from data
    df1 = pd.DataFrame(restaurants_sorted_by_lunch_price)
    df2 = pd.DataFrame(restaurants_sorted_by_dinner_price)

    # Save the DataFrame to a CSV file
    output_dir = get_output_dir()
    df1.to_csv(os.path.join(output_dir, "lunch_restaurants.csv"), index=True)
    df1.to_csv(os.path.join(output_dir, "dinner_restaurants.csv"), index=True)

    print_restaurant_list(all_restaurants, False, "all_restaurants.txt")
    print_restaurant_list(all_restaurants, True, "restaurants_with_spots.txt")

    print("🆗 Finished!")


if __name__ == "__main__":
    main()
