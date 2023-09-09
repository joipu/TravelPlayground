import requests
from bs4 import BeautifulSoup
import urllib.parse

GOOGLE_SEARCH_URL = "https://www.google.com/search?q="


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
    try:
        content = ikyu_html_soup.find_all(
            class_="timeZoneListItem_3bRvf")
        price_content = content[0].find_all(
            class_="priceLabel_p2imo")
        text_content = [item.get_text() for item in price_content][0]
        return clean_string(text_content)
    except:
        return "No lunch price"


def get_restaurant_name(ikyu_html_soup):
    content = ikyu_html_soup.find_all(
        class_="restaurantName_dvSu5")
    return clean_string(content[0].get_text().strip())


def get_dinner_price(ikyu_html_soup):
    try:
        content = ikyu_html_soup.find_all(
            class_="timeZoneListItem_3bRvf")
        price_content = content[1].find_all(
            class_="priceLabel_p2imo")
        text_content = [item.get_text() for item in price_content][0]
        return clean_string(text_content)
    except:
        return "No dinner price"


def get_tablog_rating_from_restaurant_name_and_context(restaurant_name, context):
    search_url = GOOGLE_SEARCH_URL + \
        urllib.parse.quote(restaurant_name + " " +
                           context + "site: tabelog.com")
    response = get_html_from_url(search_url)
    soup = BeautifulSoup(response, 'html.parser')
    main_element = soup.find(id="main")
    rating_element = main_element.find_all(class_="oqSTJd")[0]
    return rating_element.get_text()


def get_info_from_ikyu_restaurant_link(ikyu_restaurant_link):
    print('🐳 Opening: ' + ikyu_restaurant_link)
    html = get_html_from_url(ikyu_restaurant_link)

    soup = BeautifulSoup(html, 'html.parser')

    restaurant_name = get_restaurant_name(soup)
    food_type = get_food_type(soup)
    walking_time = get_walking_time(soup)

    print(restaurant_name)
    print(food_type)
    print(walking_time)
    print(get_lunch_price(soup))
    print(get_dinner_price(soup))
    print("Rating: " + get_tablog_rating_from_restaurant_name_and_context(
        restaurant_name, food_type + " " + walking_time))
