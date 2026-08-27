import re
import traceback

from bs4 import BeautifulSoup
from config import *
from utils.ikyu_parse_utils import get_availability_ikyu
from utils.ikyu_url_builders import (
    build_ikyu_query_url_for_tokyo,
    build_ikyu_query_urls_from_known_url,
)
from utils.network import get_response_html_from_url_with_headers

from .cache_utils import (
    convert_food_types_in_japanese_to_code,
    convert_tokyo_sub_regions_in_japanese_to_location_code,
)
from .constants import *
from .file_utils import write_response_to_debug_log_file
from .sort_options import SORT_OPTIONS


def search_restaurants_in_tokyo_yield(
    sub_regions_japanese,
    restaurant_types_japanese,
    sort_option,
    start_date: str,
    num_people,
):
    restaurant_codes = convert_food_types_in_japanese_to_code(restaurant_types_japanese)
    subregion_codes = convert_tokyo_sub_regions_in_japanese_to_location_code(
        sub_regions_japanese
    )
    sort_code = SORT_OPTIONS[sort_option]
    search_root_url = build_ikyu_query_url_for_tokyo(
        restaurant_codes, subregion_codes, sort_code, num_people
    )
    all_urls = build_ikyu_query_urls_from_known_url(
        search_root_url, pages_to_search=PAGES_TO_SEARCH
    )
    yield from restaurants_from_search_urls_yield(all_urls, start_date)


def restaurants_from_search_urls_yield(urls, start_date: str):
    for url in urls:
        yield from restaurants_from_search_url_yield(url, start_date)


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


def restaurants_from_search_url_yield(url, start_date: str):
    """
    GET request to ikyu to get restaurant information.
    :param url: the URL to send GET request
    :return: the parsed/beautified Restaurant info
    """
    # Send a GET request to the URL
    response = get_response_html_from_url_with_headers(url)
    # Write response content to debug log file
    write_response_to_debug_log_file(
        response, "debug_log", "ikyu_search_link_raw_content.html"
    )

    # Parse the HTML content of the page with BeautifulSoup
    soup = BeautifulSoup(response, "html.parser")

    # Find all "section" elements with class "restaurantCard_jpBMy"
    sections = soup.find_all("section", class_="panda-jTWvec")
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
        # Link looks like href="/108103?visitorsCount=2"
        ikyu_id = link["href"].split("?")[0][1:]
        # restaurant = get_cached_restaurant_info_by_ikyu_id(ikyu_id)
        restaurant = {}
        # if restaurant:
        #     # Make sure we have everything we need. Otherwise, we'll have to scrape it.
        #     has_all_info = (
        #         RESTAURANT_NAME in restaurant.keys()
        #         and FOOD_TYPE in restaurant.keys()
        #         and RATING in restaurant.keys()
        #         and COVER_IMAGE_URL in restaurant.keys()
        #     )
        #     if has_all_info:
        #         yield restaurant
        #         continue
        try:
            restaurant = get_restaurant_info_from_ikyu_search_card_soup(sections[i])
            restaurant[IKYU_ID] = ikyu_id
            restaurant[RESERVATION_LINK] = base_url + link["href"]
            restaurant[AVAILABILITY] = get_availability_ikyu(ikyu_id, start_date)
            restaurant[DINNER_PRICE] = get_dinner_price_from_availability(
                restaurant[AVAILABILITY]
            )
            restaurant[LUNCH_PRICE] = get_lunch_price_from_availability(
                restaurant[AVAILABILITY]
            )
            if restaurant is None:
                continue
            # store_cached_restaurant_info_by_ikyu_id(ikyu_id, restaurant)

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
    # The name is the card's restaurant link (href="/<ikyu_id>?...") whose text
    # isn't the bare review count. Matched structurally rather than by the hashed
    # CSS-module classes, which change every time Ikyu rebuilds their styles.
    name = None
    for link in soup.find_all("a", href=True):
        if re.match(r"^/\d+(\?|$)", link["href"]):
            link_text = link.get_text(strip=True)
            if link_text and not link_text.isdigit():
                name = link_text
                break
    if name is None:
        raise ValueError("Could not find restaurant name in search card")

    # Cover photos are lazy-loaded client-side, so the server HTML only carries
    # placeholder/label/icon assets. Skip those; None means "no photo".
    cover_image_url = None
    cover_image = soup.find(
        "img",
        src=re.compile(r"restaurant\.img-ikyu\.com/(?!rsImg/(guide|label|icon)/)"),
    )
    if cover_image and cover_image.has_attr("src"):
        cover_image_url = cover_image["src"]

    # Description reads "<station> <distance>／<cuisine>". Take the leaf div, or
    # we'd match an ancestor holding the whole card's concatenated text.
    food_type = "Unknown"
    for element in soup.find_all("div"):
        text = element.get_text(strip=True)
        if "／" in text and len(text) < 80 and not element.find("div"):
            parts = text.split("／")
            if len(parts) > 1 and parts[1].strip():
                food_type = parts[1].strip()
                break

    rating = None
    rating_element = soup.find("div", itemprop="ratingValue")
    if rating_element and rating_element.text:
        rating = rating_element.text.strip()

    return {
        RESTAURANT_NAME: name,
        FOOD_TYPE: food_type,
        RATING: rating,
        COVER_IMAGE_URL: cover_image_url,
    }
