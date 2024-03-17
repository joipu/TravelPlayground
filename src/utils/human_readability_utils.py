from utils.cache_utils import type_japanese_to_chinese

from utils.constants import (
    DINNER_PRICE,
    FOOD_TYPE,
    LUNCH_PRICE,
    RATING,
    RESERVATION_LINK,
    RESTAURANT_NAME,
)


def restaurant_one_line(restaurant_info):
    name = restaurant_info[RESTAURANT_NAME]
    type = type_japanese_to_chinese(restaurant_info[FOOD_TYPE])
    rating = restaurant_info[RATING]

    lunch_special_icon = ""
    if restaurant_info[LUNCH_PRICE] > 0 and restaurant_info[DINNER_PRICE] > 0:
        if restaurant_info[LUNCH_PRICE] < 0.5 * restaurant_info[DINNER_PRICE]:
            lunch_special_icon = "🍱"

    cheap_price = 99999
    cheap_icon = ""
    if restaurant_info[LUNCH_PRICE] > 0:
        cheap_price = restaurant_info[LUNCH_PRICE]
    if (
        restaurant_info[DINNER_PRICE] > 0
        and restaurant_info[DINNER_PRICE] < cheap_price
    ):
        cheap_price = restaurant_info[DINNER_PRICE]
    if cheap_price < 10000:
        cheap_icon = "💰"
    if cheap_price < 7000:
        cheap_icon = "💰💰"
    if cheap_price < 5000:
        cheap_icon = "💰💰💰"

    return f"{cheap_icon}{lunch_special_icon} {name}, {type}, {rating}, lunch: {restaurant_info[LUNCH_PRICE]}, dinner: {restaurant_info[DINNER_PRICE]}, {restaurant_info[RESERVATION_LINK]}"
