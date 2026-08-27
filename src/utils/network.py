import os
from urllib.parse import urlparse

import requests
from config import GOOGLE_PLACES_API_URL
from curl_cffi import requests as curl_requests
from dotenv import load_dotenv
from utils.constants import *

CHROME_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
# Ikyu blocks plain requests at the TLS-fingerprint layer, so it needs curl_cffi.
# Tabelog does the opposite: curl_cffi's Chrome fingerprint trips Cloudflare,
# while plain requests passes. Pick the transport per host.
IMPERSONATE_HOSTS = ("ikyu.com",)


def get_html_from_url(url):
    response = requests.get(url)
    return response.content.decode(UTF_8_ENCODING)


def get_response_json_from_url_with_headers(url):
    response = get_response_from_browser_with_headers(url)
    return response.json()


def get_response_html_from_url_with_headers(url):
    response = get_response_from_browser_with_headers(url)
    return response.content.decode(UTF_8_ENCODING)


def get_response_from_browser_with_headers(url):
    host = urlparse(url).hostname or ""
    if host.endswith(IMPERSONATE_HOSTS):
        return curl_requests.get(url, impersonate="chrome", timeout=(5, 15))
    return requests.get(url, headers={"user-agent": CHROME_UA}, timeout=(5, 15))


def get_response_from_google_place_text_search_api(
    text_query, url=GOOGLE_PLACES_API_URL
):
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": google_api_key,
        "X-Goog-FieldMask": "places.displayName,places.rating,places.googleMapsUri",
    }
    data = {"textQuery": text_query}

    return requests.post(url, headers=headers, json=data)
