import os
from utils.constants import LOCATIONS, REASON
from utils.file_utils import (
    get_resources_dir_path,
    read_content_from_file,
    read_json_from_file_in_resources,
)
from utils.human_readability_utils import get_human_readable_restaurant_info_blob
from utils.open_ai_utils import get_response_from_chatgpt


def available_options_in_japanese(mapping_file_path):
    options_japanese = []
    code_json = read_json_from_file_in_resources(mapping_file_path)
    for each in code_json:
        options_japanese.append(each["japanese"])
    return options_japanese


def parse_answer_from_chatgpt(answer, print_reasoning):
    answer = answer.strip()
    answer = answer.replace(" ,", ",").replace(", ", ",")
    suggested_items_string = answer.split("\n")[0]
    if print_reasoning:
        print("\n🤖 Reasoning: gpt_utils, line 25")
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
    answer = get_response_from_chatgpt(query, system_message, "gpt-4-1106-preview")
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
    answer = get_response_from_chatgpt(query, system_message, "gpt-4-1106-preview")
    return parse_answer_from_chatgpt(answer, True)


def get_suggested_tokyo_subregion_codes(query):
    options_array_japanese = available_options_in_japanese(
        "tokyo_subregion_code_mapping.json"
    )
    system_message = f"""If user wants to find restaurants on a trip to Tokyo, and asked this: `{query}`,  which ones of the following region names should they consider? Choose the areas that fit their query the best. Do no include surrounding areas.\n{
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
# Output will be:
# [
#   {
#     "locations": ["浅草", "上野", "押上"],
#     "reason": "你说你会去浅草寺和上野公园，这对应到浅草和上野地区。押上是附近的地区。"
#   },
#   {
#     "locations": ["渋谷", "神泉", "代々木公园"],
#     "reason": "你说你会去Shibuya sky和吉卜力美术馆，这对应到渋谷和神泉地区。代々木公园是附近的地区。"
#   }
# ]
def build_location_groups_for_tokyo(query):
    options_array_japanese = available_options_in_japanese(
        "tokyo_subregion_code_mapping.json"
    )
    system_message = f"""User asked the query: `{query}`\n You want to help them come up with a few search option sets to help them find restaurants. The following are all available options for the user to choose from:\n{", ".join(options_array_japanese)}\nYou need to look at their query, break down the geographically nearby groups, and for each group, build a search option set. For example, if user mentioned a few places in Ginza, you should build a search option set for Ginza that includes all subregions. If user mentioned places in both Ginza and Asakusa, you should build a search option set for Ginza and another for Asakusa.

1. Each group should have a [locations] line, and a [reason] line. Each takes up only one line.
2. Return the location sets on the line with `[locations]`. Return all region names verbatim in comma separately list on each line. Do not end sentence with period. Do not format. Do not be conversational.
3. Do not include nearby sub-regions. Only the regions directly mentioned in user's query. For example, if user mentioned 築地, do not include nearby regions such as 月島.
4. For your [reason] line, provide an explanation for how those locations addressed user's query. Use the same language as the user's query.
Example answer:
[locations] 銀座, 東銀座
[reason] You said you'll be shopping in Ginza, which translates to 銀座 and 東銀座 subregion. 
[locations] 浅草, 上野, 押上
[reason] You said you will be visiting 浅草寺 and 上野公园, which translates to 浅草 and 上野 subregion.
    """
    try:
        answer = get_response_from_chatgpt(query, system_message, "gpt-4-1106-preview")
        return group_locations_and_reasons(answer)
    except:
        raise Exception("Failed to get response from GPT-4")


def restaurant_list_in_human_readable_string(all_restaurants, filtered):
    all_results = ""
    for restaurant in all_restaurants:
        output = get_human_readable_restaurant_info_blob(restaurant, filtered)
        if output:
            all_results += output + "\n\n"
    return all_results


def get_gpt_recommendations(query, search_group, all_restaurants, start_date, end_date):
    all_restaurants_info = restaurant_list_in_human_readable_string(
        all_restaurants, True
    )
    locations_string = ", ".join(search_group[LOCATIONS])
    main_prompt_file_path = os.path.join(
        get_resources_dir_path(), "divide_and_conquer_gpt_prompt_criteria.txt"
    )
    main_prompt = read_content_from_file(main_prompt_file_path)

    system_message = f"You are helping the user pick good dates to visit one region according to restaurant availabilities in that region. User's query is {query}, and we broke it into several restaurant searches, with each search catering one part of their query. For example, if they are visiting many attractions in Tokyo, one search will be for one group of geographically nearby attractions. And there may have a few searches depending on how many regions the query covers.\n Now, you are looking at one search. Locations in this search are {locations_string}. This is because {search_group[REASON]}\n User's trip is from {start_date} to {end_date}. {main_prompt}\n Here are all the restaurants and their info:\n{all_restaurants_info}\n"
    print("🤖 Asking GPT: ", system_message)
    answer = get_response_from_chatgpt(query, system_message, "gpt-4")
    return answer
