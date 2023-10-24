from src.utils.cache_utils import (
    lookup_restaurant_type_code,
    lookup_tokyo_subregion_code,
)
from src.utils.constants import LOCATIONS, REASON, TOKYO_LOCATION_CODE
from src.utils.file_utils import read_json_from_file
from src.utils.human_readability_utils import get_human_readable_restaurant_info_blob
from src.utils.open_ai_utils import get_response_from_chatgpt
from src.utils.url_utils import build_query_url


def available_options_in_japanese(mapping_file_path):
    options_japanese = []
    code_json = read_json_from_file(mapping_file_path)
    for each in code_json:
        options_japanese.append(each["japanese"])
    return options_japanese


def parse_answer_from_chatgpt(answer, print_reasoning):
    answer = answer.strip()
    answer = answer.replace(" ,", ",").replace(", ", ",")
    suggested_items_string = answer.split("\n")[0]
    if print_reasoning:
        print(f"\n{answer}")
    return suggested_items_string.split(",")


def get_suggested_restaurant_type_codes(query):
    options_array_japanese = available_options_in_japanese("category_code_mapping.json")
    system_message = f"""If user wants to find food related to {query}, which ones of the following types may contain food they want to consider?\n{
      ", ".join(options_array_japanese)}.
Return all types that satisfy user's query in comma separately list on the first line. Do not end sentence with period. Do not format. Do not be conversational.
On your following lines, explain why you chose each of those types. Use the language of the user's query in your explanation.
Example answer:
焼肉, 鉄板焼
User asked for bbq in their query, and both 焼肉 and 鉄板焼 are types of bbq.
    """
    answer = get_response_from_chatgpt(query, system_message, "gpt-4")
    return parse_answer_from_chatgpt(answer, True)


def get_suggested_location_names(query):
    options_array_japanese = available_options_in_japanese("location_code_mapping.json")
    system_message = f"""If user wants to find food according to `{query}`, which one of the following location fits the best for their search?\n{
      ", ".join(options_array_japanese)}.
Return just one location from the list and nothing else on the first line. Do not end sentence with period. Do not format. Do not be conversational.
On your following lines, explain why you chose that location. Use the language of the user's query in your explanation.
Example answer:
東京
東京 is a direct match as user asked for Tokyo in their query.
    """
    answer = get_response_from_chatgpt(query, system_message, "gpt-4")
    return parse_answer_from_chatgpt(answer, True)


def get_suggested_tokyo_subregion_codes(query):
    options_array_japanese = available_options_in_japanese(
        "tokyo_subregion_code_mapping.json"
    )
    system_message = f"""If user wants to find all restaurants in Tokyo, and asked this: `{query}`,  which ones of the following region names may contain food they want to consider?\n{
      ", ".join(options_array_japanese)}.
Return all region names verbatim that satisfy user's query in comma separately list on the first line. Do not end sentence with period. Do not format. Do not be conversational.
On your following lines, explain why you chose each one of those locations. Use the language of the user's query in your explanation.
Example answer:
浅草, 銀座, 東銀座
User said they'll be shopping in Ginza, which translates to 銀座 and 東銀座 subregion. 浅草 is a nearby subregion.
    """
    answer = get_response_from_chatgpt(query, system_message, "gpt-4")
    return parse_answer_from_chatgpt(answer, True)


# Input:
# [group] 浅草, 上野, 押上, 両国, 蔵前
# [group] 渋谷, 神泉, 代々木公園, 表参道, 外苑前

# 用户提到他们将去浅草寺和上野公园，浅草和上野是此范围内的地区。 押上，両国，蔵前是周边地区。
# 用户还提到了他们将去渋谷sky，该地区包括渋谷，神泉，代々木公园。表参道，外苑前是附近的地区。
# Output:
# [
#   ["浅草", "上野", "押上", "両国", "蔵前"], ["渋谷", "神泉", "代々木公園", "表参道", "外苑前"]
# ]


def group_locations_and_reasons(input_string):
    lines = input_string.strip().split("\n")
    results = []
    current_dict = {}

    for line in lines:
        if "[locations]" in line:
            locations = line.replace("[locations]", "").strip().split(", ")
            locations = [location.strip() for location in locations]
            current_dict[LOCATIONS] = locations
        elif "[reason]" in line:
            reason = line.replace("[reason]", "").strip()
            current_dict[REASON] = reason
            results.append(current_dict)
            current_dict = {}

    return results


# Query would be "I want to visit 浅草寺，明治神宫"
# Output would be a list of URLs, each for a destination, bundling when appropriate
def build_location_groups_for_tokyo(query):
    options_array_japanese = available_options_in_japanese(
        "tokyo_subregion_code_mapping.json"
    )
    system_message = f"""User asked the query: `{query}`\n You want to help them come up with a few search option sets to help them find restaurants. The following are all available options for the user to choose from:\n{", ".join(options_array_japanese)}\nYou need to look at their query, break down the geographically nearby groups, and for each group, build a search option set. For example, if user mentioned a few places in Ginza, you should build a search option set for Ginza that includes all nearby subregions. If user mentioned places in both Ginza and Asakusa, you should build a search option set for Ginza and another for Asakusa.

1. Each group should have a [locations] line, and a [reason] line. Each takes up only one line.
2. Return the location sets on the line with `[locations]`. Return all region names verbatim in comma separately list on each line. Do not end sentence with period. Do not format. Do not be conversational.
3. For your [reason] line, provide an explanation for how those locations addressed user's query. Use the same language as the user's query.
Example answer:
[locations] 銀座, 東銀座
[reason] You said you'll be shopping in Ginza, which translates to 銀座 and 東銀座 subregion. 
[locations] 浅草, 上野, 押上
[reason] You said you will be visiting 浅草寺 and 上野公园, which translates to 浅草 and 上野 subregion. 押上 is a nearby subregion.
    """

    answer = get_response_from_chatgpt(query, system_message, "gpt-4")
    return group_locations_and_reasons(answer)


def restaurant_list_in_human_readable_string(all_restaurants, filtered):
    all_results = ""
    for restaurant in all_restaurants:
        output = get_human_readable_restaurant_info_blob(restaurant, filtered)
        if output:
            all_results += output + "\n\n"
    return all_results


def get_gpt_recommendations(query, search_group, all_restaurants):
    all_restaurants_info = restaurant_list_in_human_readable_string(
        all_restaurants, True
    )
    locations_string = ", ".join(search_group[LOCATIONS])
    system_message = f"You are helping the user pick good dates to visit one region according to restaurant availabilities in that region. User's query is {query}, and we broke it into several restaurant searches, with each search catering one part of their query. For example, if they are visiting many attractions in Tokyo, one search will be for one group of geographically nearby attractions. And there may have a few searches depending on how many regions the query covers.\n Now, you are looking at one search. Locations in this search are {locations_string}. This is because {search_group[REASON]}. Next we will give you the restaurants info from this search, and you should give 3 tentative itineraries for the user to consider.\n Each should have 1. The date and activities for the region, according to their query and potentially expanding on it. Also include which restaurants to book for lunch & dinner. 2. Ignore restaurants with rating below 3.5. 3. Prioritize restaurants with highest rating, but make each restaurant appear in only one itinerary 4. Skip the restaurants with no availability or are far from the activities, or are significantly more expensive than similarly rated restaurants, and list those restaurants out with the reasons. 5. For each restaurant, list their rating, price, and explicitly CONFIRM they have AVAILABILITY that day. If they have NO AVAILABILITY listed but says they are likely open for reservation after 2023-12-3, explicitly mention that in your answer. 6. Provide response in the same language as user's query. \n Here are all the restaurants and their info:\n{all_restaurants_info}\n"
    print("🤖 Asking GPT: ", system_message)
    answer = get_response_from_chatgpt(query, system_message, "gpt-4")
    return answer
