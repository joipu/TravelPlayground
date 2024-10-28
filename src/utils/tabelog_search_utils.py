import re
import unidecode
import urllib.parse
from bs4 import BeautifulSoup
from pykakasi import kakasi
from rapidfuzz import fuzz
from urllib.parse import urlencode
from utils.network import get_response_html_from_url_with_headers
from .file_utils import write_response_to_debug_log_file

# Initialize Kakasi for transliteration
kakasi_instance = kakasi()
kakasi_instance.setMode("H", "a")  # Hiragana to ASCII
kakasi_instance.setMode("K", "a")  # Katakana to ASCII
kakasi_instance.setMode("J", "a")  # Kanji to ASCII
converter = kakasi_instance.getConverter()

def get_tabelog_data(restaurant_search_name):
    tabelog_url = build_tabelog_query_url_for_restaurant(restaurant_search_name)
    return request_and_parse_tabelog_result(
        tabelog_url,
        urllib.parse.unquote(restaurant_search_name)
    )


def build_tabelog_query_url_for_restaurant(restaurant_name):
    params = {
        "vs": 1,
        "sa": "",
        "sk": restaurant_name,
        "sw": restaurant_name
    }

    query_string = urlencode(params, doseq=True)
    full_url = f"https://tabelog.com/rstLst/?{query_string}"
    return full_url


def request_and_parse_tabelog_result(url, restaurant_search_name):
    response = get_response_html_from_url_with_headers(url)

    write_response_to_debug_log_file(response, "debug_log", "tabelog_search_link_raw_content.html")

    # Parse the HTML content of the page with BeautifulSoup
    soup = BeautifulSoup(response, "html.parser")

    # Find all <a> tags with class "list-rst__rst-name-target cpy-rst-name"
    restaurant_name_tags = soup.find_all("a", class_="list-rst__rst-name-target cpy-rst-name")
    for restaurant_name_tag in restaurant_name_tags:
        restaurant_name = restaurant_name_tag.text.strip()
        restaurant_link = restaurant_name_tag.get('href')

        # Find the target restaurant by comparing restaurant title strings
        if are_restaurant_names_matching(restaurant_name, restaurant_search_name):
            parent_element = restaurant_name_tag.find_parent("div", class_="list-rst__rst-data")
            score_tag = parent_element.find("span", class_="c-rating__val c-rating__val--strong list-rst__rating-val")
            score = score_tag.text.strip() if score_tag else None

            return score, restaurant_link

    print("⚠️️ Cannot find matched restaurant on Tabelog! "
          "restaurant_search_name: ", restaurant_search_name,
          "search url: ", url)
    return None


def are_restaurant_names_matching(name_1, name_2, threshold=90):
    """
    Compare two strings after normalization to determine if they match.
    Uses exact matching and fuzzy matching based on a similarity threshold.
    """
    normalized_name_1 = normalize_string(name_1)
    normalized_name_2 = normalize_string(name_2)

    # Exact match
    if normalized_name_1 in normalized_name_1 or normalized_name_2 in normalized_name_1:
        return True

    # Fuzzy match using token_set_ratio
    similarity = fuzz.token_set_ratio(normalized_name_1, normalized_name_2)
    return similarity >= threshold


def normalize_string(s):
    # Transliterate Japanese scripts to Romaji using pykakasi
    s = converter.do(s)
    # Replace special characters (e.g. '・', '-'), or multiple spaces with a single space
    s = re.sub(r'[・\-—]+', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    # For case-insensitive comparison
    s = s.lower()
    # Remove diacritics for standard Latin representation (e.g. café jalapeño -> cafe jalapeno)
    s = unidecode.unidecode(s)

    return s.strip()
