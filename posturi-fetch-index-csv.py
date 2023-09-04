import requests
import csv
from bs4 import BeautifulSoup

dataRoot = 'data/posturi/'
csvFile = dataRoot + 'posturi.csv'

# Function to load existing data from a CSV file
def load_existing_data():
    try:
        existing_data = []
        with open(csvFile, "r", newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                existing_data.append(row)
    except FileNotFoundError:
        existing_data = []
    return existing_data

# Function to scrape data from a single page and append it to a CSV file
def scrape_and_save_page(url, page_number, existing_data):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    job_list = []
    
    # Find all the article boxes
    article_boxes = soup.select('article.box')
    
    for box in article_boxes:
        job = {}
        job['title'] = box.select_one('div.title a').text
        job['link_url'] = box.select_one('div.title a')['href']
        job['angajator'] = box.select_one('div.angajator').text
        job['n'] = ', '.join([n.text for n in box.select('div.n')])
        
        data_div = box.select_one('li.data div.data')
        
        # Filter the elements by their text content
        data_items = [item.strip() for item in data_div.stripped_strings]
        job['publicat'] = data_items[0]
        job['expira'] = data_items[1]
        
        locatie_div = box.select_one('li.locatie div.locatie')
        job['locatie_name'] = locatie_div.text.strip()
        job['locatie_url'] = locatie_div.a['href']
        
        job['dosar'] = box.select_one('div.dosar').text
        
        # Check if the record with the same link_url and locatie_name already exists
        if not any(item['link_url'] == job['link_url'] and item['locatie_name'] == job['locatie_name'] for item in existing_data):
            job_list.append(job)
    
    # Combine the new data with existing data
    all_jobs = existing_data + job_list
    
    # Append all data to the same CSV file
    fieldnames = ['title', 'link_url', 'angajator', 'n', 'publicat', 'expira', 'locatie_name', 'locatie_url', 'dosar']
    with open(csvFile, "a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        
        # Write headers only if the file is empty
        if not existing_data:
            writer.writeheader()
        
        for job in job_list:
            writer.writerow(job)
    
    return job_list

# Function to scrape and paginate through all pages
def scrape_all_pages(base_url, max_pages):
    existing_data = load_existing_data()
    
    for page_number in range(1, max_pages + 1):
        url = f"{base_url}/page/{page_number}/"
        print(f"Scraping page {page_number}...")
        jobs = scrape_and_save_page(url, page_number, existing_data)
        
        # If no new jobs were added on this page, stop scraping
        if not jobs:
            print("No new jobs found on this page. Stopping scraping.")
            break
    
    print("Scraping complete. Data appended incrementally to the same CSV file.")

if __name__ == "__main__":
    base_url = "http://posturi.gov.ro"
    max_pages = 47
    
    scrape_all_pages(base_url, max_pages)
