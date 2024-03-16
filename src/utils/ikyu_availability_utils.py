import datetime
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from utils.constants import (
    DINNER,
    EARLIEST_TARGET_RESERVATION_DATE,
    LATEST_TARGET_RESERVATION_DATE,
    LUNCH,
    RESERVATION_STATUS,
)
from utils.ikyu_parse_utils import get_restaurant_name_ikyu


def has_lunch_button(html):
    soup = BeautifulSoup(html, "html.parser")
    lunch_button = soup.findAll("a", attrs={"aria-label": "lunch"})
    if not lunch_button:
        return False
    return len(lunch_button) > 0


def has_teatime_button(html):
    soup = BeautifulSoup(html, "html.parser")
    button = soup.findAll("a", attrs={"aria-label": "teatime"})
    if not button:
        return False
    return len(button) > 0


def has_dinner_button(html):
    soup = BeautifulSoup(html, "html.parser")
    dinner_buttons = soup.findAll("a", attrs={"aria-label": "dinner"})
    if not dinner_buttons:
        return False
    return len(dinner_buttons) > 0


def get_html_from_ikyu(url):
    # Configure Firefox options for headless mode
    options = Options()
    options.add_argument("-headless")
    # Start web browser
    driver = webdriver.Firefox(options=options)

    # Get source code
    driver.get(url)

    html_dinner = None
    html_lunch = None

    has_lunch = has_lunch_button(driver.page_source) or has_teatime_button(
        driver.page_source
    )
    has_dinner = has_dinner_button(driver.page_source)
    has_both = has_lunch and has_dinner

    # If there's only lunch or dinner button, get the html directly.
    if not has_both and has_lunch:
        html_lunch = driver.page_source

    if not has_both and has_dinner:
        html_dinner = driver.page_source

    if has_both:
        # Dinner is always the default.
        html_dinner = driver.page_source
        lunch_button = driver.find_element(
            "xpath",
            "//a[@class='timeZoneButton_2ebcA isDynamicPricingUi_3gS_6' and @aria-label='lunch']",
        )
        lunch_button.click()
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
    if html is None:
        return {}
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

        if month == 12:
            year = "2023"
        else:
            year = "2024"
        # print(f"{year}-{month}-{day}: {price}")
        availability_json.update({f"{year}-{month}-{day}": price})
    return availability_json


def has_available_dates_after(availability_json, date_string):
    date_objects = [
        datetime.datetime.strptime(date, "%Y-%m-%d")
        for date in availability_json.keys()
    ]
    if len(date_objects) == 0:
        return False
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


def fetch_restaurant_opening_from_ikyu(ikyu_id):
    availability = {}
    url = f"https://restaurant.ikyu.com/{ikyu_id}?num_guests=2"
    dinner_html, lunch_html = get_html_from_ikyu(url)

    html = dinner_html if dinner_html is not None else lunch_html
    if html is None:
        return availability

    # Get restaurant name so we can print it out
    restaurant_name = get_restaurant_name_ikyu(BeautifulSoup(html, "html.parser"))
    print("🗓️ Getting availability for: ", restaurant_name)

    dinner_json = get_available_dates_and_price_from_html(dinner_html)
    lunch_json = get_available_dates_and_price_from_html(lunch_html)

    # Check if reservation is open
    is_reservation_open = False
    if dinner_json.keys():
        is_reservation_open = has_available_dates_after(
            dinner_json, EARLIEST_TARGET_RESERVATION_DATE
        )
    if not is_reservation_open:
        is_reservation_open = has_available_dates_after(
            lunch_json, EARLIEST_TARGET_RESERVATION_DATE
        )
    availability[
        RESERVATION_STATUS
    ] = f"Likely open for reservation after {EARLIEST_TARGET_RESERVATION_DATE}: {is_reservation_open}"

    filtered_dinner_json = filter_availability(
        dinner_json,
        EARLIEST_TARGET_RESERVATION_DATE,
        LATEST_TARGET_RESERVATION_DATE,
    )
    filtered_lunch_json = filter_availability(
        lunch_json,
        EARLIEST_TARGET_RESERVATION_DATE,
        LATEST_TARGET_RESERVATION_DATE,
    )

    if filtered_dinner_json.keys():
        availability[DINNER] = filtered_dinner_json

    if filtered_lunch_json.keys():
        availability[LUNCH] = filtered_lunch_json

    return availability
