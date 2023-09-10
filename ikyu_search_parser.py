import sys
from bs4 import BeautifulSoup
import requests
import pandas as pd

from japan_restaurant_finder import get_sorted_info_from_ikyu_restaurant_link


def run_ikyu_search(url):
    # Send a GET request to the URL
    response = requests.get(url)

    # Parse the HTML content of the page with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all "section" elements with class "restaurantCard_jpBMy"
    sections = soup.find_all('section', class_='restaurantCard_jpBMy')

    # Base URL for concatenation
    base_url = 'https://restaurant.ikyu.com'

# Iterate over the sections
for section in sections:
    # Find the first href link in the section
    link = section.find('a', href=True)

    # Concatenate with the base URL and print
    # print(base_url + link['href'])
    data = get_sorted_info_from_ikyu_restaurant_link(base_url + link['href'])

    # Create a DataFrame from data
    df = pd.DataFrame(data)

    # Save the DataFrame to a CSV file
    df.to_csv('restaurants.csv', index=False)
