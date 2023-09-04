
dataRoot = 'data/posturi/'
csvFile = dataRoot + 'posturi.csv'
from datetime import datetime
import requests
import csv
from bs4 import BeautifulSoup
import os


def pdate2date(input_date):
    romanian_months = {
        'ianuarie': 'January',
        'februarie': 'February',
        'martie': 'March',
        'aprilie': 'April',
        'mai': 'May',
        'iunie': 'June',
        'iulie': 'July',
        'august': 'August',
        'septembrie': 'September',
        'octombrie': 'October',
        'noiembrie': 'November',
        'decembrie': 'December'
    }

    # Convert the input date to a datetime object using the custom month dictionary
    for romanian_month, english_month in romanian_months.items():
        input_date = input_date.replace(romanian_month, english_month)

    date_obj = datetime.strptime(input_date, "%d %B,%Y")

    # Format the date as "dd/MM/yyyy"
    formatted_date = date_obj.strftime("%d/%m/%Y")

    # Print the formatted date
    return formatted_date


# Function to create the CSV file if it doesn't exist
def create_csv_file():
    if not os.path.isfile(csvFile):
        with open(csvFile, "w", newline="", encoding="utf-8") as csv_file:
            fieldnames = ['title', 'link_url', 'angajator', 'tip', 'publicat', 'expira', 'locatie_name', 'locatie_url', 'dosar']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

# Function to load the latest 10 rows from the CSV file
def load_latest_data():
    try:
        latest_data = []
        with open(csvFile, "r", newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            rows = list(reader)
            if len(rows) > 10:
                latest_data = rows[-10:]  # Load the latest 10 rows
            else:
                latest_data = rows
    except FileNotFoundError:
        latest_data = []
    latest_list = []
    
    for rrow in latest_data:
        latest_list.append(rrow['link_url']+rrow['publicat'])
    print(latest_list)
    return latest_list

# Function to scrape data from a single page and write new data to a CSV file
def scrape_and_save_page(url, page_number, existing_data):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    job_list = []
    
    # Find all the article boxes
    article_boxes = soup.select('article.box')
    
    for box in article_boxes:
        job = {}
        job['title'] = box.select_one('div.title a').text
        job['link_url'] = box.select_one('div.title a')['href'].replace('http://posturi.gov.ro/anunt/','')

        job['angajator'] = box.select_one('div.angajator').text
        job['tip'] = ', '.join([n.text for n in box.select('div.n')])
        
        data_div = box.select_one('li.data div.data')
        data_items = [item.strip() for item in data_div.stripped_strings]
        # Filter the elements by their text content
        data_publicat = data_items[0].replace('Publicat în: ', '').strip()       

        job['publicat'] = pdate2date(data_publicat)

        
        job['expira'] = data_items[1].replace('Expiră in ', '').strip()
        
        locatie_div = box.select_one('li.locatie div.locatie')
        job['locatie_name'] = locatie_div.text.strip()
        job['locatie_url'] = locatie_div.a['href'].replace('http://posturi.gov.ro/?judet=', '')
        
        job['dosar'] = box.select_one('div.dosar').text
        
        job_list.append(job)
    
        # check if exists
    
    # Combine the new data with existing data
    all_jobs = existing_data + job_list
    
    # Check for new data by comparing with the latest 30 rows
    new_jobs = []
    for job in job_list:
        if not any(job['link_url'] + job['publicat'] in row['link_url'] + row['publicat'] for row in existing_data):
            new_jobs.append(job)
    
    # Append new data to the CSV file
    fieldnames = ['title', 'link_url', 'angajator', 'tip', 'publicat', 'expira', 'locatie_name', 'locatie_url', 'dosar']
    with open(csvFile, "a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        for job in new_jobs:
            writer.writerow(job)
    
    return new_jobs

# Function to scrape and paginate through all pages
def scrape_all_pages(base_url, max_pages):
    create_csv_file()  # Create the CSV file if it doesn't exist
    existing_data = load_latest_data()
    
    for page_number in range(1, max_pages + 1):
        url = f"{base_url}/page/{page_number}/"
        print(f"Scraping page {page_number}...")
        new_jobs = scrape_and_save_page(url, page_number, existing_data)
    
    print(f"Scraping complete. Saved {len(new_jobs)} new records.")

if __name__ == "__main__":
    base_url = "http://posturi.gov.ro"
    max_pages = 47
    
    scrape_all_pages(base_url, max_pages)
