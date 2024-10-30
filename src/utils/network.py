import os
import requests
from config import GOOGLE_PLACES_API_URL
from dotenv import load_dotenv
from utils.constants import *


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
    headers = {
        "authority": "restaurant.ikyu.com",
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh-TW;q=0.7,zh;q=0.6",
        "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }

    response = requests.get(url, headers=headers)
    return response


def get_response_from_google_place_text_search_api(
        text_query,
        url=GOOGLE_PLACES_API_URL
):
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": google_api_key,
        "X-Goog-FieldMask": "places.displayName,places.rating,places.googleMapsUri"
    }
    data = {
        "textQuery": text_query
    }

    return requests.post(url, headers=headers, json=data)
