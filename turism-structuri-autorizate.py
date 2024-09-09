import requests
import os
import logging
from bs4 import BeautifulSoup
from datetime import datetime
import urllib3
import time
import random

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://turism.gov.ro/web/autorizare-turism/"
dataRoot = "data/turism/structuri-autorizate/"
download_dir = dataRoot + 'downloads/'
log_filename = dataRoot + 'download_log.csv'
file_extensions = ['.xls', '.xlsx', '.doc', '.docx', '.pdf']

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://turism.gov.ro/',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
}

logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s - %(message)s')

os.makedirs(download_dir, exist_ok=True)

session = requests.Session()
session.headers.update(headers)

response = session.get(url, verify=False)
response.raise_for_status()

soup = BeautifulSoup(response.text, 'html.parser')
download_widgets = soup.find_all('div', class_='so-widget-sow-cta')

os.makedirs(dataRoot, exist_ok=True)

for widget in download_widgets:
    title = widget.find('h4', class_='sow-cta-title')
    subtitle = widget.find('h4', class_='sow-cta-subtitle')
    download_link = widget.find('a', download=True)
    
    if download_link and title and subtitle:
        file_url = download_link.get('href')
        title_text = title.text.strip()
        subtitle_text = subtitle.text.strip()
        print(f"Title: {title_text}")
        print(f"Subtitle: {subtitle_text}")
        print(f"URL: {file_url}")

        if any(file_url.endswith(ext) for ext in file_extensions):
            file_name = os.path.basename(file_url)

            try:
                time.sleep(random.uniform(1, 3))
                
                file_response = session.get(file_url, verify=False)
                file_response.raise_for_status()
                
                file_path = os.path.join(download_dir, file_name)
                with open(file_path, 'wb') as file:
                    file.write(file_response.content)
                
                file_size = os.path.getsize(file_path)
                
                logging.info(f"{file_name},{file_size},{file_url},{title_text.replace(',','_')},{subtitle_text.replace(',','_')},OK")
                print(f"Downloaded: {file_name}")

            except Exception as e:
                logging.error(f"{file_name},,{file_url},{title_text.replace(',','_')},{subtitle_text.replace(',','_')},{str(e)}")
                print(f"Failed to download: {file_name} - {str(e)}")

print(f"All files have been processed. Check {log_filename} for details.")