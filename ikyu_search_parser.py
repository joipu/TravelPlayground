from bs4 import BeautifulSoup
import requests

from japan_restaurant_finder import get_restaurant_info_from_ikyu_restaurant_link


def run_ikyu_search(url):
    # Send a GET request to the URL
    response = requests.get(url)

    # Parse the HTML content of the page with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all "section" elements with class "restaurantCard_jpBMy"
    sections = soup.find_all('section', class_='restaurantCard_jpBMy')

    # Base URL for concatenation
    base_url = 'https://restaurant.ikyu.com'

    # Send a GET request to the URL
    response = requests.get(url)

    # Parse the HTML content of the page with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all "section" elements with class "restaurantCard_jpBMy"
    sections = soup.find_all('section', class_='restaurantCard_jpBMy')

    # Find all restaurants per url
    restaurants = []
    for i in range(len(sections)):
        # Find the first href link in the section
        link = sections[i].find('a', href=True)

        # Concatenate with the base URL and print
        # print(base_url + link['href'])
        restaurant = get_restaurant_info_from_ikyu_restaurant_link(base_url + link['href'])
        restaurants.append(restaurant)

    return restaurants
