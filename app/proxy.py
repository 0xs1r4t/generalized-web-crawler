import os
import requests
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path)

PROXY_ENDPOINT_URL = os.getenv("PROXY_ENDPOINT_URL")

if not PROXY_ENDPOINT_URL:
    raise ValueError("PROXY_ENDPOINT_URL environment variable is not set")


def get_page(url):
    response = requests.get(f"{PROXY_ENDPOINT_URL}?url={url}")
    return response.text


if __name__ == "__main__":
    html = get_page("https://www.myntra.com")
    print(html)
