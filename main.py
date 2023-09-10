import sys
import json
from urllib.parse import urlencode
from ikyu_search_parser import run_ikyu_search

from open_ai_utils import get_response_from_chatgpt

LOCATION_CHOICES = ['tokyo', 'osaka', 'kyoto']


def read_json_from_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)


def lookup_restaurant_type_code(restaurant_type):
    table = read_json_from_file('category_code_mapping.json')
    for item in table:
        if item['japanese'] == restaurant_type:
            return item['code']
    return ''


def lookup_location_code(location_name):
    table = read_json_from_file('location_code_mapping.json')
    for item in table:
        if item['japanese'] == location_name:
            return item['code']
    return ''


def build_query_urls(restaurant_types, location_code,
                     base_url='https://restaurant.ikyu.com/search'):
    restaurant_type_codes = [
        lookup_restaurant_type_code(rt) for rt in restaurant_types]
    location_code = lookup_location_code(location_code)
    urls = []
    pages_to_search = 3
    for xpge_value in range(1, pages_to_search + 1):
        codes_param = ','.join(restaurant_type_codes)
        params = {
            'pups': 2,
            'rtpc': codes_param,
            'xpge': xpge_value,
            'rac1': location_code,
            'pndt': 1,
            'ptaround': 0,
            'xsrt': 'gourmet'
        }

        query_string = urlencode(params, doseq=True)
        full_url = f'{base_url}?{query_string}'
        urls.append(full_url)

    return urls


def get_suggested_restaurant_type_codes(query):
    type_array_japanese = []
    code_json = read_json_from_file('category_code_mapping.json')
    for each in code_json:
        type_array_japanese.append(each['japanese'])

    system_message = f"""If user wants to find food related to {query}, which ones of the following may contain food they want to consider?\n{
      ", ".join(type_array_japanese)}.
Return your answer in comma separately list.
    """
    suggested_types = get_response_from_chatgpt(query, system_message, 'gpt-4')
    suggested_types = suggested_types.strip()
    suggested_types = suggested_types.replace(" ,", ",").replace(", ", ",")
    return suggested_types.split(',')


def get_suggested_location_codes(query):
    type_array_japanese = []
    code_json = read_json_from_file('location_code_mapping.json')
    for each in code_json:
        type_array_japanese.append(each['japanese'])

    system_message = f"""If user wants to find food according to {query}, which one of the following location fits the best for their search?\n{
      ", ".join(type_array_japanese)}.
Return just one location from the list and nothing else. Do not be conversational.
    """
    # print(system_message)
    suggested_types = get_response_from_chatgpt(query, system_message, 'gpt-4')
    suggested_types = suggested_types.strip()
    suggested_types = suggested_types.replace(" ,", ",").replace(", ", ",")
    return suggested_types.split(',')


def main():
    query = sys.argv[1]
    location_code_japanese = get_suggested_location_codes(query)[0]
    restaurant_type_codes_japanese = get_suggested_restaurant_type_codes(query)
    restaurant_type_codes_japanese_string = ', '.join(
        restaurant_type_codes_japanese)
    print(
        f"Looking for restaurant types: {restaurant_type_codes_japanese_string} in {location_code_japanese}")
    urls = build_query_urls(
        restaurant_type_codes_japanese, location_code_japanese)
    for url in urls:
        run_ikyu_search(url)


if __name__ == "__main__":
    main()
