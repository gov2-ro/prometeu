import requests
import csv
from bs4 import BeautifulSoup
import time
import random

output_csv = "data/posturi/posturi_gov_ro.csv"

def load_existing_data():
    try:
        existing_data = []
        with open(output_csv, "r", newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            existing_data = list(reader)
        return existing_data
    except FileNotFoundError:
        return []

def load_latest_jobs():
    try:
        latest_jobs = []
        with open(output_csv, "r", newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if 'link_url' in row and 'publicat' in row:
                    latest_jobs.append(f"{row['link_url']}+{row['publicat']}")
        return latest_jobs
    except FileNotFoundError:
        return []

def scrape_and_save_page(url, page_number, existing_data, latest_jobs):
    job_list = [] # Initialize job_list as an empty list
    try:
        print(f"Attempting to fetch page {page_number}...")
        response = requests.get(url, timeout=10) # Increase timeout to 10 seconds
        print(f"Page {page_number} fetched successfully.")
        soup = BeautifulSoup(response.text, 'html.parser')
        # Assuming job postings are in a list with class 'job-list'
        job_posts = soup.find_all('div', class_='job-list')
        for job in job_posts:
            title = job.find('h2').text
            link_url = job.find('a')['href']
            job_list.append({'title': title, 'link_url': link_url})
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching page {page_number}: {e}")
        raise SystemExit("Script terminated due to an error.")
    return job_list

def scrape_all_pages(base_url, max_pages):
    existing_data = load_existing_data()
    latest_jobs = load_latest_jobs()
    
    fieldnames = ['title', 'link_url', 'angajator', 'n', 'publicat', 'expira', 'locatie_name', 'locatie_url', 'dosar']
    with open(output_csv, "a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        
        for page_number in range(1, max_pages + 1):
            url = f"{base_url}/page/{page_number}/"
            print(f"Scraping page {page_number}...")
            try:
                jobs = scrape_and_save_page(url, page_number, existing_data, latest_jobs)
                for job in jobs:
                    writer.writerow(job)
            except requests.exceptions.ConnectionError:
                print(f"Connection error on page {page_number}. Retrying after a delay.")
                time.sleep(random.uniform(1, 5)) # Wait for a random time between 1 to 5 seconds
                # Retry the request here if necessary
            except Exception as e:
                print(f"An error occurred: {e}")
                raise SystemExit("Script terminated due to an error.")

    print("Scraping complete. Data appended incrementally to the same CSV file.")

if __name__ == "__main__":
    base_url = "http://posturi.gov.ro"
    max_pages = 47
    
    scrape_all_pages(base_url, max_pages)