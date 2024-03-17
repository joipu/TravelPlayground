import re

import requests
from utils.constants import DINNER, EARLIEST_TARGET_RESERVATION_DATE, LATEST_TARGET_RESERVATION_DATE, LUNCH, RESERVATION_STATUS
from utils.ikyu_availability_utils import filter_availability, has_available_dates_after


def clean_string(input_string):
    cleaned_string = " ".join(input_string.split()).strip()
    return cleaned_string

def get_restaurant_rating_ikyu(ikyu_html_soup):
    content = ikyu_html_soup.find_all(class_="ratingContainer_2inv_")
    if not content:
        return "No rating available"
    parts = content[0].get_text().split("（")
    rating = clean_string(parts[0])
    if not rating:
        return "No rating available"
    return rating

def get_restaurant_name_ikyu(ikyu_html_soup):
    content = ikyu_html_soup.find_all(class_="restaurantName_dvSu5")
    return clean_string(content[0].get_text().strip())


def get_walking_time_ikyu(ikyu_html_soup):
    content = ikyu_html_soup.find_all(
        class_="contentHeaderItem_2RHAO contentHeaderAccessesButton_1Jl7k"
    )
    text_content = [item.get_text() for item in content][0]
    return clean_string(text_content)


def get_availability_json_for_ikyu_id(ikuy_id):
    url = f"https://restaurant.ikyu.com/api/v1/restaurants/{ikuy_id}/calendar"

    # HTTP headers as specified
    headers = {
        "authority": "restaurant.ikyu.com",
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh-TW;q=0.7,zh;q=0.6",
        "referer": f"https://restaurant.ikyu.com/{ikuy_id}/lunch?num_guests=2",
        "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    meal_types = ["breakfast", "lunch", "dinner", "teatime"]
    availability = {}
    for meal in meal_types:
        for month in data[meal]:
            for day in month["days"]:
                if day["has_inventory"]:
                    day_num = day["day"]
                    mon_num = day["month"]
                    year_num = day["year"]
                    date_string = f"{year_num}-{mon_num}-{day_num}"
                    if meal not in availability:
                        availability[meal] = {}
                    availability[meal][date_string] = day["best_price"]
            
    # sort the dictionary by date
    availability = dict(sorted(availability.items()))
    return availability
    
    

def get_availability_ikyu(ikyu_id):
    raw_availability = get_availability_json_for_ikyu_id(ikyu_id)
    
    # Check if reservation is open
    is_reservation_open = False
    if raw_availability[DINNER].keys():
        is_reservation_open = has_available_dates_after(
            raw_availability[DINNER], EARLIEST_TARGET_RESERVATION_DATE
        )
    if not is_reservation_open:
        is_reservation_open = has_available_dates_after(
            raw_availability[LUNCH], EARLIEST_TARGET_RESERVATION_DATE
        )

    if DINNER not in raw_availability:
        filtered_dinner_json = {}
    else:
        filtered_dinner_json = filter_availability(
            raw_availability[DINNER],
            EARLIEST_TARGET_RESERVATION_DATE,
            LATEST_TARGET_RESERVATION_DATE,
        )
        
    if LUNCH not in raw_availability:
        filtered_lunch_json = {}
    else:
        filtered_lunch_json = filter_availability(
            raw_availability[LUNCH],
            EARLIEST_TARGET_RESERVATION_DATE,
            LATEST_TARGET_RESERVATION_DATE,
        )
        
    availability = {}
    availability[
        RESERVATION_STATUS
    ] = f"Likely open for reservation after {EARLIEST_TARGET_RESERVATION_DATE}: {is_reservation_open}"
    if filtered_dinner_json.keys():
        availability[DINNER] = filtered_dinner_json

    if filtered_lunch_json.keys():
        availability[LUNCH] = filtered_lunch_json

    return availability
        
    


def get_food_type_ikyu(ikyu_html_soup):
    content = ikyu_html_soup.find_all(class_="contentHeaderItem_2RHAO")
    text_content = [item.get_text() for item in content][1]
    return clean_string(text_content)


def get_lunch_price_ikyu(ikyu_html_soup):
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


def get_dinner_price_ikyu(ikyu_html_soup):
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
