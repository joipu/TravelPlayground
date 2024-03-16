from datetime import datetime, timedelta

BING_SEARCH_URL = "https://www.bing.com/search?q="

# Column names for presenting restaurant data
RESTAURANT_NAME = "Restaurant Name"
FOOD_TYPE = "Food Type"
LUNCH_PRICE = "Lunch Price (円)"
DINNER_PRICE = "Dinner Price (円)"
RATING = "Rating"
TABLOG_LINK = "Tablog Link"
RESERVATION_LINK = "Reservation Link"
WALKING_TIME = "Walking Time"
AVAILABILITY = "Availability"
IKYU_ID = "Ikyu ID"
EARLIEST_TARGET_RESERVATION_DATE = "2024-3-17"
LATEST_TARGET_RESERVATION_DATE = "2024-4-3"
UPDATED_TIME = "Updated Time"
DATE = "date"
RESERVATION_STATUS = "Reservation Status"
LUNCH = "lunch"
DINNER = "dinner"
LOCATION_GROUP = "location_group"
RESTAURANT = "restaurant"
WEIGHT = "weight"
PRICE = "price"
TOKYO_LOCATION_CODE = "03001"
REASON = "reason"
LOCATIONS = "locations"
LOCATION_STRING = "location_string"

def fill_dates(start_date, end_date):
    # Convert string dates to datetime objects
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Initialize the list with the start date
    date_list = [start.strftime("%Y-%m-%d")]
    
    # Increment the start date until it equals the end date
    while start < end:
        start += timedelta(days=1)
        date_list.append(start.strftime("%Y-%m-%d"))
    
    return date_list

ALL_DAYS_IN_RANGE = fill_dates(EARLIEST_TARGET_RESERVATION_DATE, LATEST_TARGET_RESERVATION_DATE)