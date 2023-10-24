from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from src.config import PAGES_TO_SEARCH


def build_query_url(
    restaurant_type_codes,
    location_code,
    sub_region_codes,
):
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
    return full_url


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
