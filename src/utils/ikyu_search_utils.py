
import traceback
from bs4 import BeautifulSoup
import requests
from config import *
from utils.ikyu_parse_utils import get_availability_ikyu

from utils.html_utils import get_html_from_url

from utils.ikyu_parse_utils import (
    get_dinner_price_ikyu,
    get_food_type_ikyu,
    get_lunch_price_ikyu,
    get_restaurant_name_ikyu,
    get_walking_time_ikyu,
    get_restaurant_rating_ikyu,
)
from utils.tabelog_utils import (
    get_tabelog_link_from_restaurant_name,
    get_tabelog_rating_from_tabelog_link,
)
from .cache_utils import (
    get_ikyu_id_from_url,
    store_cached_restaurant_info_by_url,
    convert_food_types_in_japanese_to_code,
    convert_tokyo_sub_regions_in_japanese_to_location_code,
)
from .constants import *

from utils.ikyu_url_builders import (
    build_ikyu_query_url_for_tokyo,
    build_ikyu_query_urls_from_known_url,
)


def search_restaurants_in_tokyo_yield(
    sub_regions_japanese, restaurant_types_japanese
):
    restaurant_codes = convert_food_types_in_japanese_to_code(restaurant_types_japanese)
    subregion_codes = convert_tokyo_sub_regions_in_japanese_to_location_code(
        sub_regions_japanese
    )
    search_root_url = build_ikyu_query_url_for_tokyo(restaurant_codes, subregion_codes)
    all_urls = build_ikyu_query_urls_from_known_url(
        search_root_url, pages_to_search=PAGES_TO_SEARCH
    )
    yield from restaurants_from_search_urls_yield(all_urls)


def restaurants_from_search_urls_yield(urls):
    for url in urls:
        yield from restaurants_from_search_url_yield(url)


def restaurants_from_search_url_yield(url):
    # Send a GET request to the URL
    response = requests.get(url)

    # Parse the HTML content of the page with BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all "section" elements with class "restaurantCard_jpBMy"
    sections = soup.find_all("section", class_="restaurantCard_jpBMy")

    # Base URL for concatenation
    base_url = "https://restaurant.ikyu.com"
    # Find all restaurants per url

    for i in range(len(sections)):
        # Find the first href link in the section
        link = sections[i].find("a", href=True)

        # Concatenate with the base URL and print
        # print(base_url + link['href'])
        try:
            restaurant = restaurant_from_ikyu_restaurant_link(
                base_url + link["href"]
            )
            if restaurant is None:
                continue
            yield restaurant
        except Exception as error:
            print(
                "❌ Error in getting restaurant info from link: ",
                base_url + link["href"],
            )
            print("Error: ", error)
            print("Stack trace:")
            print(traceback.format_exc())


def restaurants_from_search_url(url):
    # Send a GET request to the URL
    response = requests.get(url)

    # Parse the HTML content of the page with BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all "section" elements with class "restaurantCard_jpBMy"
    sections = soup.find_all("section", class_="restaurantCard_jpBMy")

    # Base URL for concatenation
    base_url = "https://restaurant.ikyu.com"
    # Find all restaurants per url
    restaurants = []
    for i in range(len(sections)):
        # Find the first href link in the section
        link = sections[i].find("a", href=True)

        # Concatenate with the base URL and print
        # print(base_url + link['href'])
        try:
            restaurant = restaurant_from_ikyu_restaurant_link(
                base_url + link["href"]
            )
            if restaurant is None:
                continue
            restaurants.append(restaurant)
        except Exception as error:
            print(
                "❌ Error in getting restaurant info from link: ",
                base_url + link["href"],
            )
            print("Error: ", error)
            print("Stack trace:")
            print(traceback.format_exc())
            pass

    return restaurants
    

def get_tabelog_rating_for_restaurant(restaurant_info, restaurant_name, food_type, walking_time):
    if (
        restaurant_info
        and TABLOG_LINK in restaurant_info.keys()
        and restaurant_info[TABLOG_LINK]
    ):
        tabelog_link = restaurant_info[TABLOG_LINK]
        rating = get_tabelog_rating_from_tabelog_link(tabelog_link)
    else:
        tabelog_link = get_tabelog_link_from_restaurant_name(
            restaurant_name + " " + food_type + " " + walking_time
        )
        if tabelog_link is None:
            tabelog_link = ""
            print(
                f"❗ Couldn't find tabelog link for: {restaurant_name}, using 0 for rating."
            )
            rating = 0
        else:
            rating = get_tabelog_rating_from_tabelog_link(tabelog_link)
    return rating

def restaurant_from_ikyu_restaurant_link(ikyu_restaurant_link):
    html = get_html_from_url(ikyu_restaurant_link)
    soup = BeautifulSoup(html, "html.parser")

    restaurant_name = get_restaurant_name_ikyu(soup)
    food_type = get_food_type_ikyu(soup)
    walking_time = get_walking_time_ikyu(soup)
    lunch_price = get_lunch_price_ikyu(soup)
    dinner_price = get_dinner_price_ikyu(soup)
    ikyu_id = get_ikyu_id_from_url(ikyu_restaurant_link)
    rating = get_restaurant_rating_ikyu(soup)
    availability = get_availability_ikyu(ikyu_id)
    restaurant_info = {
        RESTAURANT_NAME: restaurant_name,
        IKYU_ID: ikyu_id,
        FOOD_TYPE: food_type,
        LUNCH_PRICE: lunch_price,
        DINNER_PRICE: dinner_price,
        RATING: rating,
        RESERVATION_LINK: ikyu_restaurant_link,
        WALKING_TIME: walking_time,
        AVAILABILITY: availability,
    }
    print(
        f"🍱 Retrieved data for: {restaurant_info[RESTAURANT_NAME]} with rating {restaurant_info[RATING]}"
    )
    store_cached_restaurant_info_by_url(ikyu_restaurant_link, restaurant_info)
    return restaurant_info
