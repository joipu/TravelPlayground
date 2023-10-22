import re
import time
import requests
import urllib.parse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from .cache import (
    get_cached_restaurant_info_by_url,
    store_cached_restaurant_info_by_url,
)
from .utils.constants import *


def get_html_from_browser(url):
    # Configure Firefox options for headless mode
    options = Options()
    options.headless = True

    # Start web browser
    driver = webdriver.Firefox(options=options)

    # Get source code
    driver.get(url)

    # Wait for 3 seconds
    time.sleep(3)

    html = driver.page_source

    # Close web browser
    driver.close()

    return html


def get_html_from_url(url):
    return requests.get(url).text


def clean_string(input_string):
    cleaned_string = " ".join(input_string.split()).strip()
    return cleaned_string


def get_restaurant_name(ikyu_html_soup):
    content = ikyu_html_soup.find_all(class_="restaurantName_dvSu5")
    return clean_string(content[0].get_text().strip())


def get_walking_time(ikyu_html_soup):
    content = ikyu_html_soup.find_all(
        class_="contentHeaderItem_2RHAO contentHeaderAccessesButton_1Jl7k"
    )
    text_content = [item.get_text() for item in content][0]
    return clean_string(text_content)


def get_food_type(ikyu_html_soup):
    content = ikyu_html_soup.find_all(class_="contentHeaderItem_2RHAO")
    text_content = [item.get_text() for item in content][1]
    return clean_string(text_content)


def get_lunch_price(ikyu_html_soup):
    content = ikyu_html_soup.find_all(class_="timeZoneListItem_3bRvf")
    lunch_content = None
    for element in content:
        if "ランチ" in element.get_text():
            lunch_content = element
            break
    if lunch_content == None:
        return 0
    lunch_price = lunch_content.get_text().replace("ランチ", "")
    cleaned_lunch_price = clean_string(lunch_price)
    return extract_numeric_value(cleaned_lunch_price)


def get_dinner_price(ikyu_html_soup):
    content = ikyu_html_soup.find_all(class_="timeZoneListItem_3bRvf")
    dinner_content = None
    for element in content:
        if "ディナー" in element.get_text():
            dinner_content = element
            break
    if dinner_content == None:
        return 0
    dinner_price = dinner_content.get_text().replace("ディナー", "")
    cleaned_dinner_price = clean_string(dinner_price)
    return extract_numeric_value(cleaned_dinner_price)


def get_tablog_link_from_restaurant_name(search_words):
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

    except:
        print("🚨 Couldn't get tablog link for: ", search_words)
        return None


def get_tablog_rating_from_tablog_link(tablog_link):
    try:
        response = get_html_from_url(tablog_link)
        soup = BeautifulSoup(response, "html.parser")
        rating_element = soup.find(class_="rdheader-rating__score-val-dtl")
        rating_text = rating_element.get_text()
        rating = float(rating_text)
    except AttributeError or ValueError:
        print("🚨 Couldn't get rating from tablog link: ", tablog_link)
        rating = None
    return rating


def get_restaurant_info_from_ikyu_restaurant_link(ikyu_restaurant_link):
    restaurant_info = get_cached_restaurant_info_by_url(ikyu_restaurant_link)
    if (
        restaurant_info
        and restaurant_info[RATING] is not None
        and restaurant_info[RATING] > 0
    ):
        print("💾 Using cached data for: " + restaurant_info[RESTAURANT_NAME])
        return restaurant_info
    try:
        html = get_html_from_url(ikyu_restaurant_link)
    except:
        print("🚨 Couldn't get HTML for: ", ikyu_restaurant_link)
        return None

    soup = BeautifulSoup(html, "html.parser")

    restaurant_name = get_restaurant_name(soup)
    food_type = get_food_type(soup)
    walking_time = get_walking_time(soup)
    lunch_price = get_lunch_price(soup)
    dinner_price = get_dinner_price(soup)
    tablog_link = get_tablog_link_from_restaurant_name(
        restaurant_name + " " + food_type + " " + walking_time
    )
    if tablog_link is None:
        print(
            f"❗ Couldn't find tablog link for: {restaurant_name}, using 0 for rating."
        )
        rating = 0
    else:
        rating = get_tablog_rating_from_tablog_link(tablog_link)
    restaurant_info = {
        RESTAURANT_NAME: restaurant_name,
        FOOD_TYPE: food_type,
        LUNCH_PRICE: lunch_price,
        DINNER_PRICE: dinner_price,
        RATING: rating,
        RESERVATION_LINK: ikyu_restaurant_link,
        WALKING_TIME: walking_time,
    }
    print(
        f"🍱 Retrieved data for: {restaurant_info[RESTAURANT_NAME]} with rating {restaurant_info[RATING]}"
    )
    store_cached_restaurant_info_by_url(ikyu_restaurant_link, restaurant_info)
    return restaurant_info


def extract_numeric_value(s):
    if s is None:
        return 0
    # Find all digits and comma characters and join them into a single string
    numeric_str = "".join(re.findall(r"[0-9,]", s))
    # Remove the comma and convert to an integer
    try:
        return int(numeric_str.replace(",", ""))
    except ValueError:
        return 0
