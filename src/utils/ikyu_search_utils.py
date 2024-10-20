
import traceback
from bs4 import BeautifulSoup
from config import *
from utils.network import get_response_html_from_url_with_headers
from utils.ikyu_parse_utils import get_availability_ikyu
import os
from .file_utils import proj_root_dir

from .cache_utils import (
    convert_food_types_in_japanese_to_code,
    convert_tokyo_sub_regions_in_japanese_to_location_code,
    get_cached_restaurant_info_by_ikyu_id,
    store_cached_restaurant_info_by_ikyu_id,
)
from .constants import *
from .sort_options import SORT_OPTIONS

from utils.ikyu_url_builders import (
    build_ikyu_query_url_for_tokyo,
    build_ikyu_query_urls_from_known_url,
)


def search_restaurants_in_tokyo_yield(
    sub_regions_japanese, restaurant_types_japanese, sort_option
):
    restaurant_codes = convert_food_types_in_japanese_to_code(restaurant_types_japanese)
    subregion_codes = convert_tokyo_sub_regions_in_japanese_to_location_code(
        sub_regions_japanese
    )
    sort_code = SORT_OPTIONS[sort_option]
    search_root_url = build_ikyu_query_url_for_tokyo(restaurant_codes, subregion_codes, sort_code)
    all_urls = build_ikyu_query_urls_from_known_url(
        search_root_url, pages_to_search=PAGES_TO_SEARCH
    )
    yield from restaurants_from_search_urls_yield(all_urls)


def restaurants_from_search_urls_yield(urls):
    for url in urls:
        yield from restaurants_from_search_url_yield(url)

def get_dinner_price_from_availability(availability):
    if DINNER in availability.keys():
        return list(availability[DINNER].values())[0]
    else:
        return "Not available"

def get_lunch_price_from_availability(availability):
    if LUNCH in availability.keys():
        return list(availability[LUNCH].values())[0]
    else:
        return "Not available"


def restaurants_from_search_url_yield(url):
    """
    GET request to ikyu to get restaurant information.
    :param url: the URL to send GET request
    :return: the parsed/beautified Restaurant info
    """
    # Send a GET request to the URL
    response = get_response_html_from_url_with_headers(url)
    # Write response content to debug log file
    debug_log_dir = os.path.join(proj_root_dir(), "debug_log")
    if not os.path.exists(debug_log_dir):
        os.makedirs(debug_log_dir)
    
    with open(os.path.join(debug_log_dir, "ikyu_search_link_raw_content.html"), "w", encoding="utf-8") as f:
        f.write(response)

    # Parse the HTML content of the page with BeautifulSoup
    soup = BeautifulSoup(response, "html.parser")

    # Find all "section" elements with class "restaurantCard_jpBMy"
    sections = soup.find_all("section", class_="restaurantCard_jpBMy")
    if len(sections) == 0:
        print("No sections found in link: ", url)
        return
    else:
        print("Found ", len(sections), " sections in link: ", url)
        
    # Base URL for concatenation
    base_url = "https://restaurant.ikyu.com"
    # Find all restaurants per url

    for i in range(len(sections)):
        # Find the first href link in the section
        link = sections[i].find("a", href=True)
        # Link looks like /111516?num_guests=2&... 
        ikyu_id = link["href"].split("?")[0][1:]
        restaurant = get_cached_restaurant_info_by_ikyu_id(ikyu_id)
        if restaurant:
            # Make sure we have everything we need. Otherwise, we'll have to scrape it.
            has_all_info = (    
                RESTAURANT_NAME in restaurant.keys()
                and FOOD_TYPE in restaurant.keys()
                and RATING in restaurant.keys()
                and COVER_IMAGE_URL in restaurant.keys()
            )
            if has_all_info:
                yield restaurant
                continue
        try:
            restaurant = get_restaurant_info_from_ikyu_search_card_soup(
                sections[i]
            )
            restaurant[IKYU_ID] = ikyu_id
            restaurant[RESERVATION_LINK] = base_url + link["href"]
            restaurant[AVAILABILITY] = get_availability_ikyu(ikyu_id)
            restaurant[DINNER_PRICE] = get_dinner_price_from_availability(restaurant[AVAILABILITY])
            restaurant[LUNCH_PRICE] = get_lunch_price_from_availability(restaurant[AVAILABILITY])
            if restaurant is None:
                continue
            store_cached_restaurant_info_by_ikyu_id(ikyu_id, restaurant)

            yield restaurant
        except Exception as error:
            print(
                "❌ Error in getting restaurant info from link: ",
                base_url + link["href"],
            )
            print("Error: ", error)
            print("Stack trace:")
            print(traceback.format_exc())

def get_restaurant_info_from_ikyu_search_card_soup(soup):
    name = soup.find("h3", class_="restaurantName_2s_sg").text.strip()
    cover_image_url = get_restaurant_cover_image_url_ikyu(soup)
    description = soup.find("div", class_="retaurantArea_s9Crj").text
    parts = description.split("／")
    food_type = parts[1].strip()
    rating_element = soup.find("span", class_="restaurantCount_29PeJ")
    if rating_element:
        rating = rating_element.text
    else:
        rating = "No rating available"
    return {
        RESTAURANT_NAME: name,
        FOOD_TYPE: food_type,
        RATING: rating,
        COVER_IMAGE_URL: cover_image_url,
    }
    
def get_restaurant_cover_image_url_ikyu(ikyu_html_soup):
    content = ikyu_html_soup.find_all("div", class_="coverImages_3VYi2")
    if not content:
        return None
    image_element = content[0].find("meta")
    if not image_element:
        return None
    return image_element["content"]
    
