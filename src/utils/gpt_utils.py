from src.utils.file_utils import read_json_from_file
from src.utils.open_ai_utils import get_response_from_chatgpt


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
        print(answer)
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


def get_suggested_location_codes(query):
    options_array_japanese = available_options_in_japanese("location_code_mapping.json")
    system_message = f"""If user wants to find food according to {query}, which one of the following location fits the best for their search?\n{
      ", ".join(options_array_japanese)}.
Return just one location from the list and nothing else on the first line. Do not end sentence with period. Do not format. Do not be conversational.
On your following lines, explain why you chose that location. Use the language of the user's query in your explanation.
Example answer:
東京
東京 is a direct match as user asked for Tokyo in their query.
    """
    # print(system_message)
    answer = get_response_from_chatgpt(query, system_message, "gpt-4")
    return parse_answer_from_chatgpt(answer, True)


def get_suggested_tokyo_subregion_codes(query):
    options_array_japanese = available_options_in_japanese(
        "tokyo_subregion_code_mapping.json"
    )
    system_message = f"""If user wants to find all restaurants in Tokyo, and asked this: {query},  which ones of the following region names may contain food they want to consider?\n{
      ", ".join(options_array_japanese)}.
Return all region names verbatim that satisfy user's query in comma separately list on the first line. Do not end sentence with period. Do not format. Do not be conversational.
On your following lines, explain why you chose each one of those locations. Use the language of the user's query in your explanation.
Example answer:
浅草, 銀座, 東銀座
User said they'll be shopping in Ginza, which translates to 銀座 and 東銀座 subregion. 浅草 is a nearby subregion.
    """
    answer = get_response_from_chatgpt(query, system_message, "gpt-4")
    return parse_answer_from_chatgpt(answer, True)
