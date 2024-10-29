import concurrent.futures

from utils.tabelog_search_utils import get_tabelog_data
from utils.google_search_utils import get_google_rating
from utils.constants import TABELOG_RATING, TABELOG_LINK, GOOGLE_RATING


def fetch_ratings_and_links_async(restaurant_names):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(get_ratings_and_links_for_restaurant, name):
                name for name in restaurant_names
        }

        combined_ratings_and_links = {}
        for future in futures:
            name = futures[future]
            try:
                combined_ratings_and_links[name] = future.result()
            except Exception as e:
                print(f"Error fetching ratings for {name}: {e}")
                combined_ratings_and_links[name] = {
                    TABELOG_RATING: None,
                    TABELOG_LINK: None,
                    GOOGLE_RATING: None
                }

    return combined_ratings_and_links


def get_ratings_and_links_for_restaurant(restaurant_name):
    result = {}
    tabelog_data = get_tabelog_data(restaurant_name)
    if tabelog_data:
        rating, link = tabelog_data
        result[TABELOG_RATING] = rating
        result[TABELOG_LINK] = link
    else:
        result[TABELOG_RATING] = None
        result[TABELOG_LINK] = None

    google_rating = get_google_rating(restaurant_name)
    result[GOOGLE_RATING] = google_rating

    return result
