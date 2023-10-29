from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from src.config import PAGES_TO_SEARCH
from src.utils.cache_utils import (
    get_all_restaurant_type_codes,
    lookup_location_code,
    lookup_restaurant_type_code,
    lookup_tokyo_subregion_code,
)
from src.utils.constants import LOCATIONS, TOKYO_LOCATION_CODE
from src.utils.gpt_utils import (
    get_suggested_location_names,
    get_suggested_restaurant_type_codes,
    get_suggested_tokyo_subregion_codes,
)


def build_ikyu_query_url_for_tokyo(
    restaurant_type_codes,
    sub_region_codes,
):
    return build_ikyu_query_url(
        restaurant_type_codes,
        TOKYO_LOCATION_CODE,
        sub_region_codes,
    )


def build_ikyu_query_url(
    restaurant_type_codes,
    location_code,
    sub_region_codes,
):
    print("🔍 Building query URL...")
    print("🔍 Restaurant type codes: ", restaurant_type_codes)
    print("🔍 Location code: ", location_code)
    codes_param = ",".join(restaurant_type_codes)
    params = {
        "pups": 2,
        "rtpc": codes_param,
        "rac1": location_code,
        "rac3": ",".join(sub_region_codes),
        "pndt": 1,
        "ptaround": 0,
        "xsrt": "gourmet",
        "xpge": 1,
    }

    query_string = urlencode(params, doseq=True)
    full_url = f"https://restaurant.ikyu.com/search?{query_string}"
    print("🔍 Query URL: ", full_url)
    return full_url


def build_ikyu_query_urls_from_known_url(known_url, pages_to_search=PAGES_TO_SEARCH):
    # Parse the URL and its parameters
    url_parts = urlparse(known_url)
    query_params = parse_qs(url_parts.query)

    urls = []
    for xpge_value in range(1, pages_to_search + 1):
        # Update the 'xpge' parameter
        query_params["xpge"] = xpge_value

        # Construct the new URL
        new_query_string = urlencode(query_params, doseq=True)
        new_url_parts = url_parts._replace(query=new_query_string)
        new_url = urlunparse(new_url_parts)

        urls.append(new_url)

    return urls


def build_search_url_from_location_group_tokyo(subregion_codes):
    restaurant_type_codes = get_all_restaurant_type_codes()
    url = build_ikyu_query_url(
        restaurant_type_codes, TOKYO_LOCATION_CODE, subregion_codes
    )
    return url


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
    url = build_ikyu_query_url(restaurant_type_codes, location_code, subregion_codes)
    urls = build_ikyu_query_urls_from_known_url(url)
    return urls
