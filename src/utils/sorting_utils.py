from .constants import RATING


def sort_by_price(data, sort_criteria):
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
    none_rating = [x for x in sorted_data if x[RATING] is None]

    # 3. Sort each group by lunch price in ascending order
    above_3_9 = sort_by_price_criteria(above_3_9, sort_criteria)
    between_3_7_and_3_9 = sort_by_price_criteria(between_3_7_and_3_9, sort_criteria)
    between_3_5_and_3_7 = sort_by_price_criteria(between_3_5_and_3_7, sort_criteria)
    below_3_5 = sort_by_price_criteria(below_3_5, sort_criteria)
    none_rating = sort_by_price_criteria(none_rating, sort_criteria)

    # 4. Merge all the sorted lists back together
    return above_3_9 + between_3_7_and_3_9 + between_3_5_and_3_7 + below_3_5 + none_rating


def sort_by_rating(data):
    return sorted(data, key=lambda x: (x[RATING] is not None, x[RATING]), reverse=True)


def sort_by_price_criteria(group, sort_criteria):
        return sorted(group, key=lambda x: x[sort_criteria] if x[sort_criteria] is not None else float('inf'))
