import requests

def get_html_from_url(url):
    response = requests.get(url)
    return response.content.decode("utf-8")

def get_html_from_browser_with_headers(url):
    headers = {
        "authority": "restaurant.ikyu.com",
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh-TW;q=0.7,zh;q=0.6",
        "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }

    response = requests.get(url, headers=headers)
    return response.text