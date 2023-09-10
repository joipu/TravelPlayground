import re
import requests
import urllib.parse
from bs4 import BeautifulSoup
from selenium import webdriver

from cache import get_cached_restaurant_info_by_url, store_cached_restaurant_info_by_url

BING_SEARCH_URL = "https://www.bing.com/search?q="
RESTAURANT_NAME = "Restaurant Name"
FOOD_TYPE = "Food Type"
LUNCH_PRICE = "Lunch Price (円)"
DINNER_PRICE = "Dinner Price (円)"
RATING = "Rating"
RESERVATION_LINK = "Reservation Link"
WALKING_TIME = "Walking Time"


def get_html_from_browser(url):
    # Start web browser
    driver = webdriver.Firefox()

    # Get source code
    driver.get(url)
    html = driver.page_source

    # Close web browser
    driver.close()

    return html


def get_html_from_url(url): return requests.get(url).text


def clean_string(input_string):
    cleaned_string = ' '.join(input_string.split()).strip()
    return cleaned_string


def get_restaurant_name(ikyu_html_soup):
    content = ikyu_html_soup.find_all(
        class_="restaurantName_dvSu5")
    return clean_string(content[0].get_text().strip())


def get_walking_time(ikyu_html_soup):
    content = ikyu_html_soup.find_all(
        class_="contentHeaderItem_2RHAO contentHeaderAccessesButton_1Jl7k")
    text_content = [item.get_text() for item in content][0]
    return clean_string(text_content)


def get_food_type(ikyu_html_soup):
    content = ikyu_html_soup.find_all(
        class_="contentHeaderItem_2RHAO")
    text_content = [item.get_text() for item in content][1]
    return clean_string(text_content)


def get_lunch_price(ikyu_html_soup):
    content = ikyu_html_soup.find_all(
        class_="timeZoneListItem_3bRvf")
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
    content = ikyu_html_soup.find_all(
        class_="timeZoneListItem_3bRvf")
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
    search_url = BING_SEARCH_URL + \
        urllib.parse.quote(search_words) + " site%3Atabelog.com"
    response = get_html_from_browser(search_url)
    soup = BeautifulSoup(response, 'html.parser')
    all_results = soup.find_all(id="b_results")
    first_href = all_results[0].find('div', class_="tpmeta").get_text()
    return first_href


def get_tablog_rating_from_tablog_link(tablog_link):
    response = get_html_from_url(tablog_link)
    soup = BeautifulSoup(response, 'html.parser')
    rating_element = soup.find(class_="rdheader-rating__score-val-dtl")
    try:
        rating_text = rating_element.get_text()
        rating = float(rating_text)
    except AttributeError or ValueError:
        # Handle the exception if conversion fails (e.g., if the text isn't a valid number)
        rating = None
    return rating


def get_restaurant_info_from_ikyu_restaurant_link(ikyu_restaurant_link):
    restaurant_info = get_cached_restaurant_info_by_url(ikyu_restaurant_link)
    if restaurant_info:
        print("💾 Using cached data for: " + ikyu_restaurant_link)
        return restaurant_info
    print('🐳 Opening: ' + ikyu_restaurant_link)
    html = get_html_from_url(ikyu_restaurant_link)

    soup = BeautifulSoup(html, 'html.parser')

    restaurant_name = get_restaurant_name(soup)
    food_type = get_food_type(soup)
    walking_time = get_walking_time(soup)
    lunch_price = get_lunch_price(soup)
    dinner_price = get_dinner_price(soup)
    rating = get_tablog_rating_from_tablog_link(get_tablog_link_from_restaurant_name(
        restaurant_name + " " + food_type + " " + walking_time))
    restaurant_info = {
        RESTAURANT_NAME: restaurant_name,
        FOOD_TYPE: food_type,
        LUNCH_PRICE: lunch_price,
        DINNER_PRICE: dinner_price,
        RATING: rating,
        RESERVATION_LINK: ikyu_restaurant_link,
        WALKING_TIME: walking_time,
    }
    store_cached_restaurant_info_by_url(ikyu_restaurant_link, restaurant_info)
    return restaurant_info


def sort_by_multiple_criteria(data):
    # 1. Sort all data by rating in descending order
    sorted_data = sort_by_rating(data)

    # 2. Gather data in different rating ranges
    above_3_9 = [x for x in sorted_data if x[RATING]
                 is not None and x[RATING] >= 3.9]
    between_3_7_and_3_9 = [
        x for x in sorted_data if x[RATING] is not None and 3.7 <= x[RATING] < 3.9]
    between_3_5_and_3_7 = [
        x for x in sorted_data if x[RATING] is not None and 3.5 <= x[RATING] < 3.7]
    below_3_5 = [x for x in sorted_data if x[RATING]
                 is not None and x[RATING] < 3.5]
    # collect those with None rating
    none_rating = [x for x in sorted_data if x[RATING] is None]

    # 3. Sort each group by lunch price in ascending order
    above_3_9 = sorted(
        above_3_9, key=lambda x: x[LUNCH_PRICE] if x[LUNCH_PRICE] is not None else float('inf'))
    between_3_7_and_3_9 = sorted(
        between_3_7_and_3_9, key=lambda x: x[LUNCH_PRICE] if x[LUNCH_PRICE] is not None else float('inf'))
    between_3_5_and_3_7 = sorted(
        between_3_5_and_3_7, key=lambda x: x[LUNCH_PRICE] if x[LUNCH_PRICE] is not None else float('inf'))
    below_3_5 = sorted(
        below_3_5, key=lambda x: x[LUNCH_PRICE] if x[LUNCH_PRICE] is not None else float('inf'))
    # Sort this none_rating list based on lunch price, similarly to how we sorted the other lists. Append these to the end of the sorted lists.
    none_rating = sorted(
        none_rating, key=lambda x: x[LUNCH_PRICE] if x[LUNCH_PRICE] is not None else float('inf'))

    # 4. Merge all the sorted lists back together
    return above_3_9 + between_3_7_and_3_9 + between_3_5_and_3_7 + below_3_5 + none_rating


def sort_by_rating(data):
    return sorted(data, key=lambda x: (x[RATING] is not None, x[RATING]), reverse=True)


def extract_numeric_value(s):
    if s is None:
        return 0
    # Find all digits and comma characters and join them into a single string
    numeric_str = ''.join(re.findall(r'[0-9,]', s))
    # Remove the comma and convert to an integer
    try:
        return int(numeric_str.replace(',', ''))
    except ValueError:
        return 0
