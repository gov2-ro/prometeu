import requests
import json
from bs4 import BeautifulSoup

# FIXME: doesn't check for previous data - overwrites all

dataRoot = 'data/posturi/'
jsonFile = dataRoot + 'posturi.csv'

# Function to load existing data from a JSON file
def load_existing_data():
    try:
        with open(jsonFile, "r", encoding="utf-8") as json_file:
            existing_data = json.load(json_file)
    except FileNotFoundError:
        existing_data = []
    return existing_data

# Function to check if a job with the same link_url and locatie_name exists in the data
def job_exists(existing_data, job):
    for existing_job in existing_data:
        if (existing_job['link_url'] == job['link_url']) and (existing_job['locatie_name'] == job['locatie_name']):
            return True
    return False

# Function to scrape data from a single page and save it incrementally to a JSON file
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
        job['n'] = [n.text for n in box.select('div.n')]
        
        data_div = box.select_one('li.data div.data')
        
        # Filter the elements by their text content
        data_items = [item.strip() for item in data_div.stripped_strings]
        job['publicat'] = data_items[0]
        job['expira'] = data_items[1]
        
        locatie_div = box.select_one('li.locatie div.locatie')
        job['locatie_name'] = locatie_div.text.strip()
        job['locatie_url'] = locatie_div.a['href']
        
        job['dosar'] = box.select_one('div.dosar').text
        
        if not job_exists(existing_data, job):
            job_list.append(job)
    
    # Combine the new data with existing data
    all_jobs = existing_data + job_list
    
    # Save all data to the same JSON file
    with open(jsonFile, "w", encoding="utf-8") as json_file:
        json.dump(all_jobs, json_file, ensure_ascii=False, indent=4)
    
    return job_list

# Function to scrape and paginate through all pages
def scrape_all_pages(base_url, max_pages):
    existing_data = load_existing_data()
    
    for page_number in range(1, max_pages + 1):
        url = f"{base_url}/page/{page_number}/"
        print(f"Scraping page {page_number}...")
        jobs = scrape_and_save_page(url, page_number, existing_data)
    
    print("Scraping complete. Data saved incrementally in the same JSON file.")

if __name__ == "__main__":
    base_url = "http://posturi.gov.ro"
    max_pages = 47
    
    scrape_all_pages(base_url, max_pages)
