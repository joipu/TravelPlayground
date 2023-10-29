import re


def clean_string(input_string):
    cleaned_string = " ".join(input_string.split()).strip()
    return cleaned_string


def get_restaurant_name_ikyu(ikyu_html_soup):
    content = ikyu_html_soup.find_all(class_="restaurantName_dvSu5")
    return clean_string(content[0].get_text().strip())


def get_walking_time_ikyu(ikyu_html_soup):
    content = ikyu_html_soup.find_all(
        class_="contentHeaderItem_2RHAO contentHeaderAccessesButton_1Jl7k"
    )
    text_content = [item.get_text() for item in content][0]
    return clean_string(text_content)


def get_food_type_ikyu(ikyu_html_soup):
    content = ikyu_html_soup.find_all(class_="contentHeaderItem_2RHAO")
    text_content = [item.get_text() for item in content][1]
    return clean_string(text_content)


def get_lunch_price_ikyu(ikyu_html_soup):
    content = ikyu_html_soup.find_all(class_="timeZoneListItem_3bRvf")
    lunch_content = None
    for element in content:
        if "ランチ" in element.get_text():
            lunch_content = element
            break
    if lunch_content == None:
        return 0
    lunch_price = lunch_content.get_text().replace("ランチ", "")
    cleaned_lunch_price = clean_string(lunch_price)
    return extract_numeric_value(cleaned_lunch_price)


def get_dinner_price_ikyu(ikyu_html_soup):
    content = ikyu_html_soup.find_all(class_="timeZoneListItem_3bRvf")
    dinner_content = None
    for element in content:
        if "ディナー" in element.get_text():
            dinner_content = element
            break
    if dinner_content == None:
        return 0
    dinner_price = dinner_content.get_text().replace("ディナー", "")
    cleaned_dinner_price = clean_string(dinner_price)
    return extract_numeric_value(cleaned_dinner_price)


def extract_numeric_value(s):
    if s is None:
        return 0
    # Find all digits and comma characters and join them into a single string
    numeric_str = "".join(re.findall(r"[0-9,]", s))
    # Remove the comma and convert to an integer
    try:
        return int(numeric_str.replace(",", ""))
    except ValueError:
        return 0
