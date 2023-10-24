import os
import json
import re

from src.utils.constants import IKYU_ID
from src.utils.file_utils import read_json_from_file

CACHE_DIR = "cache_data"
RESTAURANT_INFO_CACHE_FILE_NAME = "restaurant_info_cache.json"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)


def get_ikyu_id_from_url(ikyu_url):
    # get 111310 from "https://restaurant.ikyu.com/111310/?num_guests=2"
    match = re.search(r"restaurant\.ikyu\.com/(\d+)", ikyu_url)
    if match:
        return match.group(1)
    else:
        print("🚨 Couldn't get restaurant ikyu id from url: ", ikyu_url)
        return None


def get_cached_restaurant_info_by_url(ikyu_url):
    ikyu_id = get_ikyu_id_from_url(ikyu_url)
    cached_info = get_cached_restaurant_info_by_ikyu_id(ikyu_id)
    if cached_info:
        cached_info[IKYU_ID] = ikyu_id
    return cached_info


def store_cached_restaurant_info_by_url(ikyu_url, restaurant_info):
    ikuy_id = get_ikyu_id_from_url(ikyu_url)
    return store_cached_restaurant_info_by_ikyu_id(ikuy_id, restaurant_info)


def get_cached_restaurant_info_by_ikyu_id(ikyu_id):
    cache_file_path = os.path.join(CACHE_DIR, RESTAURANT_INFO_CACHE_FILE_NAME)
    if os.path.exists(cache_file_path):
        with open(cache_file_path, "r", encoding="utf-8") as f:
            restaurant_info_cache = json.load(f)
            if ikyu_id in restaurant_info_cache:
                return restaurant_info_cache[ikyu_id]
    else:
        return {}


def store_cached_restaurant_info_by_ikyu_id(ikyu_id, restaurant_info):
    cache_file_path = os.path.join(CACHE_DIR, RESTAURANT_INFO_CACHE_FILE_NAME)
    if os.path.exists(cache_file_path):
        with open(cache_file_path, "r", encoding="utf-8") as f:
            restaurant_info_cache = json.load(f)
    else:
        restaurant_info_cache = {}
    restaurant_info_cache[ikyu_id] = restaurant_info
    with open(cache_file_path, "w", encoding="utf-8") as f:
        json.dump(restaurant_info_cache, f, ensure_ascii=False, indent=4)


def get_code_from_japanese_name(code, mapping_file_path):
    table = read_json_from_file(mapping_file_path)
    for item in table:
        if item["japanese"] == code:
            return item["code"]
    return ""


def lookup_restaurant_type_code(restaurant_type):
    return get_code_from_japanese_name(restaurant_type, "category_code_mapping.json")


def lookup_location_code(location_name):
    return get_code_from_japanese_name(location_name, "location_code_mapping.json")


def lookup_tokyo_subregion_code(subregion_name):
    return get_code_from_japanese_name(
        subregion_name, "tokyo_subregion_code_mapping.json"
    )
