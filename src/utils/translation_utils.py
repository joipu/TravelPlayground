from constants.translation_constants import cuisine_translation_map


def get_english_translation(japanese_name):
    return cuisine_translation_map.get(japanese_name, "N/A")
