import concurrent.futures

from utils.tabelog_search_utils import get_tabelog_data
from utils.google_search_utils import get_google_data
from utils.constants import TABELOG_RATING, TABELOG_LINK, GOOGLE_RATING, GOOGLE_LINK


def fetch_ratings_and_links_async(restaurant_ids_and_names):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(get_ratings_and_links_for_restaurant, ikyu_id, name): (ikyu_id, name)
                for ikyu_id, name in restaurant_ids_and_names
        }

        combined_ratings_and_links = {}
        for future in futures:
            ikyu_id, restaurant_name = futures[future] # unpack the keys of dict that we passed to the async func
            try:
                # Emit the response from the async future
                combined_ratings_and_links[ikyu_id] = future.result()
            except Exception as e:
                print(f"Error fetching ratings for {ikyu_id} - {restaurant_name}: {e}")
                combined_ratings_and_links[ikyu_id] = {
                    TABELOG_RATING: None,
                    TABELOG_LINK: None,
                    GOOGLE_RATING: None,
                    GOOGLE_LINK: None
                }
    return combined_ratings_and_links


def get_ratings_and_links_for_restaurant(ikyu_id, restaurant_name):
    result = {}
    tabelog_data = get_tabelog_data(ikyu_id, restaurant_name)
    if tabelog_data:
        rating, link = tabelog_data
        result[TABELOG_RATING] = rating
        result[TABELOG_LINK] = link
    else:
        result[TABELOG_RATING] = None
        result[TABELOG_LINK] = None

    google_data = get_google_data(ikyu_id, restaurant_name)
    if google_data:
        google_rating, google_link = google_data
        result[GOOGLE_RATING] = google_rating
        result[GOOGLE_LINK] = google_link
    else:
        result[GOOGLE_RATING] = None
        result[GOOGLE_LINK] = None

    return result
