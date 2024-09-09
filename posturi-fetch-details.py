indexcsv = 'data/posturi_gov_ro.csv'
base_url = "http://posturi.gov.ro"

import csv, os, time,  requests, random
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime


ROMANIAN_MONTHS = {
    'ianuarie': '01', 'februarie': '02', 'martie': '03', 'aprilie': '04',
    'mai': '05', 'iunie': '06', 'iulie': '07', 'august': '08',
    'septembrie': '09', 'octombrie': '10', 'noiembrie': '11', 'decembrie': '12'
}

def parse_romanian_date(date_string):
    # Remove 'Publicat în: ' prefix
    date_string = date_string.replace('Publicat în: ', '')
    
    # Split the date string
    day, month_year = date_string.split(' ', 1)
    month, year = month_year.split(',')
    
    # Convert month name to number
    month_num = ROMANIAN_MONTHS[month.lower()]
    
    # Create a datetime object
    date_obj = datetime(int(year), int(month_num), int(day))
    
    # Format the date as desired
    return date_obj.strftime('%Y/%m/%d')

def fetch_html(url):
    
    response = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': base_url,
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        'TE': 'Trailers'
    })
    
    return response.text

def extract_main_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    main_content = soup.find('main', id='main', class_='site-main')
    return str(main_content) if main_content else ''

def get_slug(url):
    parsed_url = urlparse(url)
    path = parsed_url.path.strip('/')
    return path.split('/')[-1] if path else 'index'

def create_directory(date_str):
    directory = os.path.join('data', 'anunturi', date_str)
    os.makedirs(directory, exist_ok=True)
    return directory

def save_html(content, directory, filename):
    file_path = os.path.join(directory, f"{filename}.html")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def process_csv(csv_path):
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            url = row['url']
            date_str = row['publicat_in']
            
            formatted_date = parse_romanian_date(date_str)
            
            html = fetch_html(url)
            main_content = extract_main_content(html)
            slug = get_slug(url)
            directory = create_directory(formatted_date)
            save_html(main_content, directory, slug)
            print(f"Processed: {url}")
            sleep_time = random.uniform(0.5, 1.1)  # Random sleep time between 2 and 5 seconds
            time.sleep(sleep_time)

if __name__ == "__main__":
    csv_path = indexcsv
    process_csv(csv_path)