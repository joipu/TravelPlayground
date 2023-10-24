# How many pages of ikyu results to check. About 18 results per page.
PAGES_TO_SEARCH = 1

# If you already have an ikyu URL and want to skip the GPT url building part, set this to True and pass the URL as your argument instead of the query. This is useful for debugging or for building restaurant cache.
USE_KNOWN_URL = "use_known_url"

# If enabled, this will assume you're searching in Tokyo and will refine your search to Tokyo subregions.
SEARCH_IN_KYOTO = "search_in_tokyo"

# If true, this will build a separate URL for each location. Only works for Tokyo.
DIVIDE_AND_CONQUER = "divide_and_conquer"

# This is default. This will search on city level, e.g. Tokyo, Kyoto, etc.
SEARCH_BY_CITY = "search_by_city"

WORK_MODE = SEARCH_BY_CITY
