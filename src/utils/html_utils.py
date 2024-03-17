import time
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


def get_html_from_browser(url):
    return ""
    # Configure Firefox options for headless mode
    options = Options()
    options.headless = True

    # Start web browser
    driver = webdriver.Firefox(options=options)

    # Get source code
    driver.get(url)

    # Wait for 3 seconds
    time.sleep(3)

    html = driver.page_source

    # Close web browser
    driver.close()

    return html


def get_html_from_url(url):
    return requests.get(url).text
