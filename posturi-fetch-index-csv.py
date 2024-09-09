output_csv = "data/posturi/posturi_gov_ro.csv"
fieldnames = ['angajator', 'detalii', 'publicat_in', 'expira_in', 'judet', 'url_judet', 'tip']


import requests, csv, random, time
from bs4 import BeautifulSoup

def load_existing_data():
    try:
        existing_data = []
        with open(output_csv, "r", newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            existing_data = list(reader)
        return existing_data
    except FileNotFoundError:
        return []

def write_header():
    with open(output_csv, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

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

def get_total_pages(base_url):
    url = base_url + "/page/1/"
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
    soup = BeautifulSoup(response.content, 'html.parser')

    pagination_div = soup.select_one('div.ast-pagination')
    if pagination_div:
        next_link = pagination_div.find('a', class_='next page-numbers')
        if next_link:
            last_page_link = next_link.find_previous_sibling('a')
            if last_page_link and last_page_link.text.strip().isdigit():
                max_pages = int(last_page_link.text.strip())
            else:
                max_pages = 1  # Fallback if we can't find a valid last page link
        else:
            max_pages = 1  # Fallback if we can't find the next link
    else:
        max_pages = 1  # Fallback if we can't find the pagination div

    return max_pages

def scrape_and_save_page(url, page_number, existing_data, latest_jobs):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'http://posturi.gov.ro',  # Set the referrer to the base URL
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        'TE': 'Trailers'
    }
    response = requests.get(url, headers=headers)

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
        
        job_key = f"{job['link_url']}+{job['publicat']}"
        
        # Check if the job already exists in the latest_jobs list
        if job_key in latest_jobs:
            print(f"Job already exists: {job_key}. Stopping the script.")
            return
        
        job_list.append(job)
    
    # Combine the new data with existing data
    all_jobs = existing_data + job_list
    
    # Append all data to the same CSV file
    fieldnames = ['title', 'link_url', 'angajator', 'n', 'publicat', 'expira', 'locatie_name', 'locatie_url', 'dosar']
    with open(output_csv, "a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        for job in job_list:
            writer.writerow(job)
    
    return job_list

def scrape_all_pages(base_url, max_pages):
    existing_data = load_existing_data()
    latest_jobs = load_latest_jobs()
    
    for page_number in range(1, max_pages + 1):
        url = f"{base_url}/page/{page_number}/"
        print(f"Scraping page {page_number}...")
        jobs = scrape_and_save_page(url, page_number, existing_data, latest_jobs)
        sleep_time = random.uniform(0.5, 1.1)  # Random sleep time between 2 and 5 seconds
        time.sleep(sleep_time)

    
    print("Scraping complete. Data appended incrementally to " + output_csv)

if __name__ == "__main__":
    base_url = "http://posturi.gov.ro"
    max_pages = get_total_pages (base_url)
    # write_header()

    
    scrape_all_pages(base_url, max_pages)
