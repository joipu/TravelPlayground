import os
from utils.cache_utils import (
    get_cache_file_for_location_group,
    get_cached_restaurant_info_by_ikyu_id,
    get_output_dir,
)
from utils.constants import *
from utils.file_utils import read_json_from_file, write_json_to_file_full_path
from itertools import product, combinations

from utils.human_readability_utils import restaurant_one_line

# [
#   {
#     "date": "2020-01-01",
#     "meal" "lunch",
#     "restaurant": {}
#     "price": 10000
#   }
#   {
#     "date": "2020-01-01",
#     "meal" "lunch",
#     "restaurant": {}
#     "price": 10000
#   }
# ]


def weight_for_reservation(restaurant, price):
    if restaurant[RATING] == 0 or restaurant[RATING] is None:
        return 0
    return (restaurant[RATING] - 3.5) * 1000000 / price


# Input
# {
#     DATE: date,
#     LOCATION_GROUP: locationGroup,
#     LUNCH: lunchAvailability[RESTAURANT],
#     DINNER: dinnerAvailability[RESTAURANT],
# }
def weight_for_plan(plan):
    return weight_for_reservation(
        plan[LUNCH][RESTAURANT], plan[LUNCH][PRICE]
    ) + weight_for_reservation(plan[DINNER][RESTAURANT], plan[DINNER][PRICE])


# Return a list of date in format of "2020-01-01"
def get_all_dates_in_range():
    return ALL_DAYS_IN_RANGE


def get_all_restaurants_for_location_group(locationGroup):
    file_path = get_cache_file_for_location_group(locationGroup)
    restaurant_ids = read_json_from_file(file_path)
    restaurants = [get_cached_restaurant_info_by_ikyu_id(id) for id in restaurant_ids]
    return restaurants


def get_availabilities_for_location_date(locationGroup, date, meal):
    all_restaurants_for_loc = get_all_restaurants_for_location_group(locationGroup)
    availabilities = []
    for restaurant in all_restaurants_for_loc:
        if AVAILABILITY in restaurant.keys():
            # If restaurant is still available for reservation in future.
            if restaurant[AVAILABILITY][RESERVATION_STATUS].endswith("False"):
                if meal == "lunch":
                    if restaurant[LUNCH_PRICE] > 0:
                        availabilities.append(
                            {
                                RESTAURANT: restaurant,
                                PRICE: restaurant[LUNCH_PRICE],
                            }
                        )
                elif meal == "dinner":
                    if restaurant[DINNER_PRICE] > 0:
                        availabilities.append(
                            {
                                RESTAURANT: restaurant,
                                PRICE: restaurant[DINNER_PRICE],
                            }
                        )
            elif meal in restaurant[AVAILABILITY].keys():
                if date in restaurant[AVAILABILITY][meal].keys():
                    if restaurant[AVAILABILITY][meal][date] > 0:
                        availabilities.append(
                            {
                                RESTAURANT: restaurant,
                                PRICE: restaurant[AVAILABILITY][meal][date],
                            }
                        )

    return availabilities


def get_all_location_date_plans(locationGroups):
    all_dates = get_all_dates_in_range()
    all_plans = []
    for locationGroup in locationGroups:
        for date in all_dates:
            lunchAvailabilities = get_availabilities_for_location_date(
                locationGroup, date, "lunch"
            )
            dinnerAvailabilities = get_availabilities_for_location_date(
                locationGroup, date, "dinner"
            )
            for lunchAvailability in lunchAvailabilities:
                for dinnerAvailability in dinnerAvailabilities:
                    plan = {
                        DATE: date,
                        LOCATION_STRING: "_".join(locationGroup[LOCATIONS]),
                        LUNCH: lunchAvailability,
                        DINNER: dinnerAvailability,
                    }
                    plan[WEIGHT] = weight_for_plan(plan)
                    # print(f"{plan[DATE]} {plan[WEIGHT]}")
                    all_plans.append(plan)
    return all_plans


def rank_location_date_plans(plans):
    for plan in plans:
        plan[WEIGHT] = weight_for_plan(plan)
    return sorted(plans, key=lambda x: x[WEIGHT], reverse=True)


def get_best_combos(locationGroups):
    plans = get_all_location_date_plans(locationGroups)
    combos = find_best_combinations(plans)
    return combos


def find_best_combinations(plans):
    # Create a dictionary to hold plans by location
    plans_by_location = {}
    for plan in plans:
        # print(plan)
        location = plan[LOCATION_STRING]
        if location not in plans_by_location:
            plans_by_location[location] = []
        plans_by_location[location].append(plan)

    for location in plans_by_location.keys():
        plans_by_location[location].sort(key=lambda x: x[WEIGHT], reverse=True)
        plans_by_location[location] = plans_by_location[location][:10]

    # output_file_name = "plans_by_location.json"
    # output_dir = get_output_dir()
    # write_json_to_file_full_path(
    #     os.path.join(output_dir, output_file_name), plans_by_location
    # )
    # return

    # Create an empty list to hold valid combinations
    valid_combinations = []

    # Generate all combinations using itertools.product
    for r in range(1, len(plans_by_location) + 1):
        for subset_keys in combinations(plans_by_location.keys(), r):
            subset_values = [plans_by_location[k] for k in subset_keys]

            # Generate all combinations using itertools.product
            for combo in product(*subset_values):
                # Initialize variables to hold used dates and total weight for each combination
                used_dates = set()
                food_types = set()
                total_weight = 0
                valid = True

                for plan in combo:
                    # Check for duplicate dates in the combination
                    if plan[DATE] in used_dates:
                        valid = False
                        break
                    if plan[LUNCH][RESTAURANT][FOOD_TYPE] in food_types:
                        valid = False
                        break
                    food_types.add(plan[LUNCH][RESTAURANT][FOOD_TYPE])
                    if plan[DINNER][RESTAURANT][FOOD_TYPE] in food_types:
                        valid = False
                        break
                    food_types.add(plan[DINNER][RESTAURANT][FOOD_TYPE])
                    used_dates.add(plan[DATE])
                    total_weight += plan[WEIGHT]

                if valid:
                    valid_combinations.append(
                        {"plans": list(combo), "weight": total_weight}
                    )

    # Sort valid combinations by total weight in descending order
    valid_combinations.sort(key=lambda x: x[WEIGHT], reverse=True)

    for plans_and_weight in valid_combinations:
        plans = plans_and_weight["plans"]
        for plan in plans:
            print(plan)
            if isinstance(plan[LUNCH], dict) and RESTAURANT in plan[LUNCH].keys():
                plan[LUNCH] = restaurant_one_line(plan[LUNCH][RESTAURANT])
            if isinstance(plan[DINNER], dict) and RESTAURANT in plan[DINNER].keys():
                plan[DINNER] = restaurant_one_line(plan[DINNER][RESTAURANT])

    output_file_name = "plans_by_location.json"
    output_dir = get_output_dir()
    write_json_to_file_full_path(
        os.path.join(output_dir, output_file_name), valid_combinations[:100]
    )
    return valid_combinations
