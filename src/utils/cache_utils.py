import datetime
import os
import re

from utils.constants import *
from utils.file_utils import (
    read_json_from_file,
    read_json_from_file_in_resources,
    write_json_to_file_full_path,
)

CACHE_DIR = "cache_data"
RESTAURANT_INFO_CACHE_FILE_NAME = "restaurant_info_cache.json"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)


def get_full_output_path(file_name):
    full_path = os.path.join(get_output_dir(), file_name)
    return full_path


def get_output_dir():
    root_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    output_dir = os.path.join(root_dir, "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return os.path.abspath(output_dir)


def get_ikyu_id_from_url(ikyu_url):
    # get 111310 from "https://restaurant.ikyu.com/111310/?num_guests=2"
    match = re.search(r"restaurant\.ikyu\.com/(\d+)", ikyu_url)
    if match:
        return match.group(1)
    else:
        print("🚨 Couldn't get restaurant ikyu id from url: ", ikyu_url)
        return None


def get_all_cached_restaurant_info():
    cache_file_path = os.path.join(CACHE_DIR, RESTAURANT_INFO_CACHE_FILE_NAME)
    if os.path.exists(cache_file_path):
        restaurant_info_cache = read_json_from_file(cache_file_path)
        return restaurant_info_cache
    return {}


def get_cached_restaurant_info_by_ikyu_id(ikyu_id):
    cache_file_path = os.path.join(CACHE_DIR, RESTAURANT_INFO_CACHE_FILE_NAME)
    if os.path.exists(cache_file_path):
        restaurant_info_cache = read_json_from_file(cache_file_path)
        if ikyu_id in restaurant_info_cache:
            if LAST_UPDATE_TIME in restaurant_info_cache[ikyu_id]:
                last_update_time = restaurant_info_cache[ikyu_id][LAST_UPDATE_TIME]
                if (
                    datetime.now()
                    - datetime.strptime(last_update_time, "%Y-%m-%d %H:%M:%S")
                    < timedelta(hours=1)
                ):
                    return restaurant_info_cache[ikyu_id]
    return {}


def store_cached_restaurant_info_by_ikyu_id(ikyu_id, restaurant_info):
    cache_file_path = os.path.join(CACHE_DIR, RESTAURANT_INFO_CACHE_FILE_NAME)
    if os.path.exists(cache_file_path):
        restaurant_info_cache = read_json_from_file(cache_file_path)
    else:
        restaurant_info_cache = {}
    restaurant_info[LAST_UPDATE_TIME] = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    restaurant_info_cache[ikyu_id] = restaurant_info
    write_json_to_file_full_path(cache_file_path, restaurant_info_cache)

def translate_from_japanese_name_to_code(japanese_name, mapping_file_path, output_language):
    table = read_json_from_file_in_resources(mapping_file_path)
    japanese_name = japanese_name.strip()
    for item in table:
        if item["japanese"] == japanese_name:
            return item[output_language]
    return japanese_name
    

def translate_from_japanese_name(japanese_name, mapping_file_path, output_language):
    table = read_json_from_file_in_resources(mapping_file_path)
    japanese_name = japanese_name.strip()
    all_names = japanese_name.split("・")
    all_translated_names = []
    for name in all_names:
        for item in table:
            if item["japanese"] == name:
                all_translated_names.append(item[output_language])
                break
        else:
            all_translated_names.append(name)
    return "・".join(all_translated_names)    

def convert_tokyo_sub_regions_in_japanese_to_location_code(tokyo_sub_regions):
    return [lookup_tokyo_subregion_code(region) for region in tokyo_sub_regions]


def convert_food_types_in_japanese_to_code(restaurant_types):
    return [
        lookup_restaurant_type_code(restaurant_type)
        for restaurant_type in restaurant_types
    ]


def convert_food_types_in_japanese_to_chinese(restaurant_types):
    return [
        type_japanese_to_chinese(restaurant_type)
        for restaurant_type in restaurant_types
    ]


def lookup_restaurant_type_code(restaurant_type):
    return translate_from_japanese_name(
        restaurant_type, "category_code_mapping.json", "code"
    )
    

def type_japanese_to_chinese(type_japanese):
    return translate_from_japanese_name(
        type_japanese, "category_code_mapping.json", "chinese"
    )


def lookup_tokyo_subregion_code(subregion_name):
    return translate_from_japanese_name_to_code(
        subregion_name, "tokyo_region_code_mapping.json", "code"
    )


def get_cache_file_for_location_group(location_group):
    cache_file_name = "_".join(location_group["locations"]) + ".json"
    cache_file_path = os.path.join(get_output_dir(), cache_file_name)
    return cache_file_path
