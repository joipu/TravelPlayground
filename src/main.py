import sys
import json
import os
import pandas as pd
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from .ikyu_search_parser import run_ikyu_search
from datetime import datetime, timedelta
from .utils.open_ai_utils import get_response_from_chatgpt
from .utils.sorting_utils import sort_by_price
from .utils.constants import (
    AVAILABILITY,
    DINNER,
    FOOD_TYPE,
    LUNCH,
    LUNCH_PRICE,
    DINNER_PRICE,
    RATING,
    RESERVATION_STATUS,
    RESTAURANT_NAME,
    WALKING_TIME,
)

PAGES_TO_SEARCH = 5
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


def get_output_dir():
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return os.path.abspath(output_dir)


def yenToUSD(yen):
    return int(yen / 149.0)

def describe_availability(data):
    # Sort the data by date
    sorted_dates = sorted(data.keys())

    # Initialize variables
    output = "Available on "
    prev_date = None
    range_start = None

    for i, date_str in enumerate(sorted_dates):
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Check for consecutive dates
        if prev_date is not None and date_obj == prev_date + timedelta(days=1):
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

    # Add price information
    price = next(iter(data.values()))

    return output
    
    

def print_output_in_human_readable_format(all_restaurants, filtered, output_file):
    all_results = ""
    for restaurant in all_restaurants:
        output = ""
        output += f"{restaurant[RESTAURANT_NAME]}\n"
        output += f"{restaurant[FOOD_TYPE]}\n"
        output += f"Rating: {restaurant[RATING]}/5\n"
        output += f"Location: {restaurant[WALKING_TIME]}\n"
        output += f"Lunch: ${yenToUSD(restaurant[LUNCH_PRICE])}\n"
        output += f"Dinner: ${yenToUSD(restaurant[DINNER_PRICE])}\n"
        
        should_print = False
        if LUNCH in restaurant[AVAILABILITY].keys():
            should_print = True
            output += f"Lunch availability:\n"
            output += f"{describe_availability(restaurant[AVAILABILITY][LUNCH])}\n"
        if DINNER in restaurant[AVAILABILITY].keys():
            should_print = True
            output += f"Dinner availability:\n"
            output += f"{describe_availability(restaurant[AVAILABILITY][DINNER])}\n"
        if RESERVATION_STATUS in restaurant[AVAILABILITY].keys():
            if restaurant[AVAILABILITY][RESERVATION_STATUS].endswith("True"):
                prefix = "👍"
                should_print = True
            else:
                prefix = "❌"    
            output += f"{prefix} {restaurant[AVAILABILITY][RESERVATION_STATUS]}\n"
        output += "\n"
        if filtered:
            if should_print:
                all_results += output
        else:
            all_results += output

    output_file = os.path.join(get_output_dir(), output_file)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(all_results)


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
    output_dir = get_output_dir()
    df1.to_csv(os.path.join(output_dir, "lunch_restaurants.csv"), index=True)
    df1.to_csv(os.path.join(output_dir, "dinner_restaurants.csv"), index=True)

    print_output_in_human_readable_format(all_restaurants, False, "all_restaurants.txt")
    print_output_in_human_readable_format(all_restaurants, True, "restaurants_with_spots.txt")

    print("🆗 Finished!")


if __name__ == "__main__":
    main()
