from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from config import PAGES_TO_SEARCH
from utils.constants import TOKYO_LOCATION_CODE


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
    print("🔍 Sub region codes: ", sub_region_codes)
    codes_param = ",".join(restaurant_type_codes)
    params = {
        "pups": 4,
        "rtpc": codes_param,
        "rac1": location_code,
        "rac2": ",".join(sub_region_codes),
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


def build_search_url_from_location_group_tokyo(subregion_codes, restaurant_type_codes):
    url = build_ikyu_query_url(
        restaurant_type_codes, TOKYO_LOCATION_CODE, subregion_codes
    )
    return url
