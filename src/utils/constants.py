from datetime import datetime, timedelta

BING_SEARCH_URL = "https://www.bing.com/search?q="

# Column names for presenting restaurant data
RESTAURANT_NAME = "Restaurant Name"
FOOD_TYPE = "Food Type"
LUNCH_PRICE = "Lunch Price (円)"
DINNER_PRICE = "Dinner Price (円)"
RATING = "Rating"
IKYU_RATING = "Ikyu Rating"
TABLOG_LINK = "Tablog Link"
RESERVATION_LINK = "Reservation Link"
WALKING_TIME = "Walking Time"
AVAILABILITY = "Availability"
IKYU_ID = "Ikyu ID"
EARLIEST_TARGET_RESERVATION_DATE = "2024-3-17"
LATEST_TARGET_RESERVATION_DATE = "2024-4-2"
LAST_UPDATE_TIME = "Last Update Time"
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
HARD_TO_RESERVE = "Hard to Reserve"

HARD_TO_RESERVE_THRESHOLD = 8

YAKITORI = ["焼鳥", "焼肉"]

ALL_FOOD_TYPES_EXCEPT_CHINESE =  [
        "洋食",
        "フランス料理",
        "イタリア料理",
        "スペイン料理",
        "ステーキ／グリル料理",
        "洋食その他",
        "和食",
        "懐石・会席料理",
        "割烹・小料理",
        "京料理",
        "魚介・海鮮料理",
        "鉄板焼",
        "寿司",
        "天ぷら",
        "すき焼き／しゃぶしゃぶ",
        "焼鳥",
        "鍋",
        "うなぎ料理",
        "和食その他",
        "中華",
        "中国料理",
        "飲茶・点心",
        "中華その他",
        "アジア・エスニック",
        "焼肉",
        "韓国料理",
        "タイ料理",
        "ベトナム料理",
        "インド料理",
        "アジア・エスニックその他",
        "ブッフェ",
        "ラウンジ",
        "バー",
        "ワインバー",
        "ビアガーデン・BBQ"
    ]

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

def get_all_dates_in_range():
    return ALL_DAYS_IN_RANGE