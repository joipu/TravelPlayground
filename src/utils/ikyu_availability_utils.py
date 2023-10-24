import datetime
import json
import re
import sys
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from src.utils.constants import (
    DINNER,
    EARLIEST_TARGET_RESERVATION_DATE,
    LATEST_TARGET_RESERVATION_DATE,
    LUNCH,
    RESERVATION_STATUS,
)


def get_html_from_ikyu(url):
    # Configure Firefox options for headless mode
    options = Options()
    options.add_argument("-headless")
    # Start web browser
    driver = webdriver.Firefox(options=options)

    # Get source code
    driver.get(url)

    html_dinner = driver.page_source
    try:
        button = driver.find_element(
            "xpath",
            "//a[@class='timeZoneButton_2ebcA isDynamicPricingUi_3gS_6' and @aria-label='lunch']",
        )
        button.click()
    except Exception as e:
        if "Message: Unable to locate element:" in str(e):
            print(f"❗ No lunch button found: {url}")
            driver.close()
            return html_dinner, None
        else:
            print(f"❌ Error in getting lunch button: {url}, {e}")
            raise e

    html_lunch = driver.page_source

    # Close web browser
    driver.close()

    return html_dinner, html_lunch


def strip_spaces(text):
    return re.sub(r"^\s+|\s+$", "", text)


# Get 11 from "2023 年 11 月"
def get_month_from_string(month_string):
    numbers = re.findall(r"\d+", month_string)
    month = int(numbers[1])
    return month


# Get 24200 from "24,200円"
def get_price_from_string(price_string):
    try:
        numbers = re.findall(r"\d+", price_string.replace(",", ""))
        amount = int(numbers[0])
        return amount
    except Exception as e:
        # Use 0 if price is not available
        return 0


def get_available_dates_and_price_from_html(html):
    """
    returns:
    {
        "2023-11-01": 24200,
        "2023-11-02": 25200,
    }
    """

    soup = BeautifulSoup(html, "html.parser")

    # Find all "section" elements with class "restaurantCard_jpBMy"
    available_buttons = soup.find_all("button", class_="isBestPrice_2jhgZ")
    availability_json = {}
    # Iterate over the sections
    for button in available_buttons:
        parent = button.parent
        month_element = parent.findChildren("h2", recursive=False)[0]
        month = get_month_from_string(strip_spaces(month_element.text))

        date_element = button.findChildren("span", recursive=False)[0]
        day = strip_spaces(date_element.contents[0])

        subchildren = date_element.findChildren("div", recursive=False)[0]
        price = get_price_from_string(strip_spaces(subchildren.text))

        year = "2023"
        # print(f"{year}-{month}-{day}: {price}")
        availability_json.update({f"{year}-{month}-{day}": price})
    return availability_json


def has_available_dates_after(availability_json, date_string):
    date_objects = [
        datetime.datetime.strptime(date, "%Y-%m-%d")
        for date in availability_json.keys()
    ]
    latest_date = max(date_objects)
    check_date = datetime.datetime.strptime(date_string, "%Y-%m-%d")
    return latest_date > check_date


def filter_availability(availability_json, begin_date_str, end_date_str):
    # Convert string dates to datetime objects for comparison
    date_objects = {
        datetime.datetime.strptime(date, "%Y-%m-%d"): value
        for date, value in availability_json.items()
    }

    # Convert begin_date_str and end_date_str to datetime objects
    begin_date = datetime.datetime.strptime(begin_date_str, "%Y-%m-%d")
    end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")

    # Filter the dates that fall between the begin and end date
    filtered_data = {
        date: value
        for date, value in date_objects.items()
        if begin_date <= date <= end_date
    }

    # Update the JSON string with filtered data
    response = {
        date.strftime("%Y-%m-%d"): value for date, value in filtered_data.items()
    }
    return response


def get_availabilities_for_ikyu_restaurant(ikyu_id):
    url = f"https://restaurant.ikyu.com/{ikyu_id}?num_guests=2"
    dinner_html, lunch_html = get_html_from_ikyu(url)
    dinner_json = get_available_dates_and_price_from_html(dinner_html)
    is_reservation_open = has_available_dates_after(
        dinner_json, EARLIEST_TARGET_RESERVATION_DATE
    )
    result = {}
    filtered_dinner_json = filter_availability(
        dinner_json,
        EARLIEST_TARGET_RESERVATION_DATE,
        LATEST_TARGET_RESERVATION_DATE,
    )

    if filtered_dinner_json.keys():
        result[DINNER] = filtered_dinner_json

    if lunch_html is not None:
        lunch_json = get_available_dates_and_price_from_html(lunch_html)
        if not is_reservation_open:
            is_reservation_open = has_available_dates_after(
                lunch_json, EARLIEST_TARGET_RESERVATION_DATE
            )
        filtered_lunch_json = filter_availability(
            lunch_json,
            EARLIEST_TARGET_RESERVATION_DATE,
            LATEST_TARGET_RESERVATION_DATE,
        )

        if filtered_lunch_json.keys():
            result[LUNCH] = filtered_lunch_json

    result[
        RESERVATION_STATUS
    ] = f"Likely open for reservation after {EARLIEST_TARGET_RESERVATION_DATE}: {is_reservation_open}"

    return result
