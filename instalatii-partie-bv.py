data_root = 'data/local/BV/stare-partii/'
out_csv = 'poiana-bv-instalatii.csv'

import requests
from bs4 import BeautifulSoup
import pandas as pd
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def scrape_data():
    url = 'https://www.discoverpoiana.ro/ro/instalatii'
    
    # Set up a retry mechanism
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    # Send a GET request to the URL
    response = session.get(url, headers=headers)
    
    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data. Status code: {response.status_code}")

    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    data = []
    for box in soup.find_all("div", class_="installation-box"):
        instalatie = box.find("h3").get_text(strip=True) if box.find("h3") else ""
        stare = ""
        program = ""

        for p in box.find_all("p"):
            if "Stare teleferic:" in p.get_text():
                stare = p.get_text().replace("Stare teleferic:", "").strip()
            if "Orar de funcționare:" in p.get_text():
                program = p.get_text().replace("Orar de funcționare:", "").strip()

        data.append([instalatie, stare, program])

    return data

def save_to_csv(data, file_name):
    df = pd.DataFrame(data, columns=["Instalatie", "Stare", "Program"])
    df.to_csv(file_name, index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    try:
        data = scrape_data()
        save_to_csv(data, data_root + out_csv)
        print("Data scraped and saved successfully.")
    except Exception as e:
        print(str(e))