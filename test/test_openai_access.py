import urllib3
from urllib3.exceptions import HTTPError
import json
from dotenv import find_dotenv, load_dotenv
import os

# Constants for headers
def build_headers() -> dict:
    """
    Builds the headers dictionary based on the defined constants.
    
    Returns:
        dict: A dictionary of HTTP headers.
    """

    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

    OPENAI_ORGANIZATION = os.environ.get("OPENAI_ORGANIZATION")
    if OPENAI_ORGANIZATION:
        headers["OpenAI-Organization"] = OPENAI_ORGANIZATION

    OPENAI_ORGANIZATION = os.environ.get("OPENAI_PROJECT")
    if OPENAI_PROJECT:
        headers["OpenAI-Project"] = OPENAI_ORGANIZATION

    return headers

def test_api_key():
    """
    Tests the OpenAI API key by making a request to the models endpoint.
    Prints the success message or the encountered HTTPS error.
    """
    http = urllib3.PoolManager()
    url = "https://api.openai.com/v1/models"
    headers = build_headers()

    try:
        response = http.request("GET", url, headers=headers)
        if response.status == 200:
            print("API key is valid. Request successful.")
        else:
            print(f"Request failed with status code: {response.status}")
            print("Response:", json.loads(response.data.decode('utf-8')))
    except HTTPError as e:
        print(f"HTTPS error occurred: {e}")

if __name__ == "__main__":
    OPENAI_ORGANIZATION = None  # Replace if applicable, else set to None
    OPENAI_PROJECT = None  # Replace if applicable; Org then required
    _ = load_dotenv(find_dotenv())
    test_api_key()