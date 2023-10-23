import sys
import json
import os
import pandas as pd
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from .ikyu_search_parser import run_ikyu_search

from .utils.open_ai_utils import get_response_from_chatgpt
from .utils.sorting_utils import sort_by_price
from .utils.constants import LUNCH_PRICE, DINNER_PRICE

PAGES_TO_SEARCH = 10
USE_KNOWN_URL = False
SEARCH_IN_KYOTO = False


def read_json_from_file(filename):
    # Build the full path to the JSON file to avoid depending on the current working directory from which the script is run
    # Get the directory where the current main.py is located
    script_dir = os.path.dirname(__file__)
    absolute_file_path = os.path.join(script_dir, "resources", filename)
    with open(absolute_file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def lookup_restaurant_type_code(restaurant_type):
    table = read_json_from_file("category_code_mapping.json")
    for item in table:
        if item["japanese"] == restaurant_type:
            return item["code"]
    return ""


def lookup_location_code(location_name):
    table = read_json_from_file("location_code_mapping.json")
    for item in table:
        if item["japanese"] == location_name:
            return item["code"]
    return ""


def lookup_tokyo_subregion_code(subregion_name):
    table = read_json_from_file("tokyo_subregion_code_mapping.json")
    for item in table:
        if item["japanese"] == subregion_name:
            return item["code"]
    return ""


def build_query_urls_from_known_url(known_url):
    # Parse the URL and its parameters
    url_parts = urlparse(known_url)
    query_params = parse_qs(url_parts.query)

    urls = []
    for xpge_value in range(1, PAGES_TO_SEARCH + 1):
        # Update the 'xpge' parameter
        query_params["xpge"] = xpge_value

        # Construct the new URL
        new_query_string = urlencode(query_params, doseq=True)
        new_url_parts = url_parts._replace(query=new_query_string)
        new_url = urlunparse(new_url_parts)

        urls.append(new_url)

    return urls


def build_query_urls(
    restaurant_type_codes,
    location_code,
    sub_region_codes,
    base_url="https://restaurant.ikyu.com/search",
):
    urls = []
    print(f"🚧 Searching the first {PAGES_TO_SEARCH} pages of results 🚧")
    for xpge_value in range(1, PAGES_TO_SEARCH + 1):
        codes_param = ",".join(restaurant_type_codes)
        params = {
            "pups": 2,
            "rtpc": codes_param,
            "rac1": location_code,
            "rac3": ",".join(sub_region_codes),
            "pndt": 1,
            "ptaround": 0,
            "xsrt": "gourmet",
            "xpge": xpge_value,
        }

        query_string = urlencode(params, doseq=True)
        full_url = f"{base_url}?{query_string}"
        urls.append(full_url)

    return urls


def get_suggested_restaurant_type_codes(query):
    type_array_japanese = []
    code_json = read_json_from_file("category_code_mapping.json")
    for each in code_json:
        type_array_japanese.append(each["japanese"])

    system_message = f"""If user wants to find food related to {query}, which ones of the following types may contain food they want to consider?\n{
      ", ".join(type_array_japanese)}.
Return all types that satisfy user's query in comma separately list on the first line. Do not end sentence with period. Do not format. Do not be conversational.
On your following lines, explain why you chose each of those types. Use the language of the user's query in your explanation.
Example answer:
焼肉, 鉄板焼
User asked for bbq in their query, and both 焼肉 and 鉄板焼 are types of bbq.
    """
    # print(system_message)
    answer = get_response_from_chatgpt(query, system_message, "gpt-4")
    answer = answer.strip()
    answer = answer.replace(" ,", ",").replace(", ", ",")
    suggested_types_string = answer.split("\n")[0]
    print(answer)
    return suggested_types_string.split(",")


def get_suggested_location_codes(query):
    type_array_japanese = []
    code_json = read_json_from_file("location_code_mapping.json")
    for each in code_json:
        type_array_japanese.append(each["japanese"])

    system_message = f"""If user wants to find food according to {query}, which one of the following location fits the best for their search?\n{
      ", ".join(type_array_japanese)}.
Return just one location from the list and nothing else on the first line. Do not end sentence with period. Do not format. Do not be conversational.
On your following lines, explain why you chose that location. Use the language of the user's query in your explanation.
Example answer:
東京
東京 is a direct match as user asked for Tokyo in their query.
    """
    # print(system_message)
    answer = get_response_from_chatgpt(query, system_message, "gpt-4")
    answer = answer.strip()
    answer = answer.replace(" ,", ",").replace(", ", ",")
    suggested_types_string = answer.split("\n")[0]
    print(answer)
    return suggested_types_string.split(",")


def get_suggested_tokyo_subregion_codes(query):
    type_array_japanese = []
    code_json = read_json_from_file("tokyo_subregion_code_mapping.json")
    for each in code_json:
        type_array_japanese.append(each["japanese"])

    system_message = f"""If user wants to find all restaurants in Tokyo, and asked this: {query},  which ones of the following region names may contain food they want to consider?\n{
      ", ".join(type_array_japanese)}.
Return all region names verbatim that satisfy user's query in comma separately list on the first line. Do not end sentence with period. Do not format. Do not be conversational.
On your following lines, explain why you chose each one of those locations. Use the language of the user's query in your explanation.
Example answer:
浅草, 銀座, 東銀座
User said they'll be shopping in Ginza, which translates to 銀座 and 東銀座 subregion. 浅草 is a nearby subregion.
    """
    # print(system_message)
    answer = get_response_from_chatgpt(query, system_message, "gpt-4")
    answer = answer.strip()
    answer = answer.replace(" ,", ",").replace(", ", ",")
    suggested_subregions = answer.split("\n")[0]
    print(answer)
    return suggested_subregions.split(",")


def print_search_scope(restaurant_types, area, subregions):
    types_string = ", ".join(restaurant_types)
    if len(subregions) == 0:
        subregions_string = "all subregions"
    else:
        subregions_string = ", ".join(subregions)
    print(f"🔍 Looking for {types_string} in {area} ({subregions_string}) 🔍")


def main():
    if USE_KNOWN_URL:
        known_url = sys.argv[1]
        urls = build_query_urls_from_known_url(known_url)
    elif SEARCH_IN_KYOTO:
        query = sys.argv[1]
        location_code = "03001"
        subregion_codes_japanese = get_suggested_tokyo_subregion_codes(query)
        restaurant_type_codes_japanese = get_suggested_restaurant_type_codes(query)
        print_search_scope(
            restaurant_type_codes_japanese, "Tokyo", subregion_codes_japanese
        )
        restaurant_type_codes = [
            lookup_restaurant_type_code(rt) for rt in restaurant_type_codes_japanese
        ]

        subregion_codes = [
            lookup_tokyo_subregion_code(code) for code in subregion_codes_japanese
        ]
        urls = build_query_urls(restaurant_type_codes, location_code, subregion_codes)
        print("🔗 Example search url:")
        print(urls[0])
    else:
        query = sys.argv[1]
        location_code_japanese = get_suggested_location_codes(query)[0]
        restaurant_type_codes_japanese = get_suggested_restaurant_type_codes(query)
        restaurant_type_codes_japanese_string = ", ".join(
            restaurant_type_codes_japanese
        )
        print_search_scope(
            restaurant_type_codes_japanese_string, location_code_japanese, []
        )

        restaurant_type_codes = [
            lookup_restaurant_type_code(rt) for rt in restaurant_type_codes_japanese
        ]
        location_code = lookup_location_code(location_code)
        urls = build_query_urls(restaurant_type_codes, location_code, [])
        print("🔗 Example search url:")
        print(urls[0])

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
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    df1.to_csv(os.path.join(output_dir, "lunch_restaurants.csv"), index=True)
    df1.to_csv(os.path.join(output_dir, "dinner_restaurants.csv"), index=True)

    print("🆗 Finished!")


if __name__ == "__main__":
    main()
