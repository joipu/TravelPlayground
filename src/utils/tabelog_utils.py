import urllib.parse
from bs4 import BeautifulSoup
from utils.html_utils import get_html_from_browser

from utils.ikyu_search_utils import get_html_from_url
from .constants import *

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

def get_tabelog_link_from_restaurant_name(search_words):
    try:
        search_url = (
            BING_SEARCH_URL + urllib.parse.quote(search_words) + " site%3Atabelog.com"
        )
        response = get_html_from_browser(search_url)
        soup = BeautifulSoup(response, "html.parser")
        all_results = soup.find_all(id="b_results")
        # Loop through all_results to find links
        for result in all_results:
            for cite in result.find_all("cite"):
                link = cite.get_text()
                if link.startswith("https://tabelog.com/"):
                    return link

    except Exception as e:
        print("🚨 Couldn't get tabelog link for: ", search_words)
        print(f"Error: {e}")
        return None


def get_tabelog_rating_from_tabelog_link(tabelog_link):
    try:
        response = get_html_from_url(tabelog_link)
        soup = BeautifulSoup(response, "html.parser")
        rating_element = soup.find(class_="rdheader-rating__score-val-dtl")
        rating_text = rating_element.get_text()
        rating = float(rating_text)
    except AttributeError or ValueError:
        print("🚨 Couldn't get rating from tabelog link: ", tabelog_link)
        rating = None
    return rating
