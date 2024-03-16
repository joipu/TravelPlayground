import os

from utils.file_utils import read_json_from_file, write_json_to_file_full_path

USER_CACHE_DIR = "user_session_cache"
if not os.path.exists(USER_CACHE_DIR):
    os.makedirs(USER_CACHE_DIR)


def get_user_cache_file_path(session_id):
    return f"{os.path.join(USER_CACHE_DIR, session_id)}.json"


def save_user_session(session_id, user_session):
    if "sessionId" not in user_session:
        user_session["sessionId"] = session_id
    write_json_to_file_full_path(get_user_cache_file_path(session_id), user_session)


def get_user_session(session_id):
    user_cache_file_path = get_user_cache_file_path(session_id)
    if os.path.exists(user_cache_file_path):
        session = read_json_from_file(user_cache_file_path)
        return session
    return {}


def build_session_json(
    session_id, query, locationGroups, restaurantTypes, startDate, endDate, plansForDay
):
    return {
        "sessionId": session_id,
        "query": query,
        "locationGroups": locationGroups,
        "restaurantTypes": restaurantTypes,
        "startDate": startDate,
        "endDate": endDate,
        "plansForDay": plansForDay,
    }
