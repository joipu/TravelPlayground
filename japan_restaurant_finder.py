import requests
from bs4 import BeautifulSoup
import urllib.parse
from selenium import webdriver
import os

BING_SEARCH_URL = "https://www.bing.com/search?q="
data = []


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
        return "No lunch price"
    lunch_price = lunch_content.get_text().replace("ランチ", "")
    return clean_string(lunch_price)


def get_restaurant_name(ikyu_html_soup):
    content = ikyu_html_soup.find_all(
        class_="restaurantName_dvSu5")
    return clean_string(content[0].get_text().strip())


def get_dinner_price(ikyu_html_soup):
    content = ikyu_html_soup.find_all(
        class_="timeZoneListItem_3bRvf")
    dinner_content = None
    for element in content:
        if "ディナー" in element.get_text():
            dinner_content = element
            break
    if dinner_content == None:
        return "No dinner price"
    dinner_price = dinner_content.get_text().replace("ディナー", "")
    return clean_string(dinner_price)


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
    main_element = soup.find(id="main")
    rating_element = soup.find(class_="rdheader-rating__score-val-dtl")
    rating_text = rating_element.get_text()
    try:
        rating = float(rating_text)
    except ValueError:
        # Handle the exception if conversion fails (e.g., if the text isn't a valid number)
        rating = None
    return rating


def get_info_from_ikyu_restaurant_link(ikyu_restaurant_link):
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

    # Append a dictionary with restuarant data to the list
    data.append({
        "Restaurant Name": restaurant_name,
        "Food Type": food_type,
        "Walking Time": walking_time,
        "Lunch Price": lunch_price,
        "Dinner Price": dinner_price,
        "Rating": rating,
        "Reservation Link": ikyu_restaurant_link,
    })

    return data
