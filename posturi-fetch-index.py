output_csv = "data/posturi/posturi_gov_ro.csv"
fieldnames = ['pozitie', 'url', 'angajator', 'detalii', 'publicat_in', 'expira_in', 'judet', 'url_judet', 'tip', 'updates']
base_url = "http://posturi.gov.ro"

import requests, csv, random, time, os, sys
from bs4 import BeautifulSoup
from datetime import datetime

def load_existing_data():
    try:
        existing_data = {}
        with open(output_csv, "r", newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                existing_data[row['url']] = row
        return existing_data
    except FileNotFoundError:
        return {}

def save_data(jobs):
    with open(output_csv, "r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        existing_fieldnames = reader.fieldnames
    
    with open(output_csv, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=existing_fieldnames)
        writer.writeheader()
        
        for job in jobs.values():
            # Ensure all required fields are present
            for field in existing_fieldnames:
                if field not in job:
                    job[field] = ""
            
            writer.writerow(job)
    
    print(f"Data saved to {output_csv}")

def write_header():
    if not os.path.exists(output_csv) or os.stat(output_csv).st_size == 0:
        with open(output_csv, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

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

def compare_and_update(existing_job, new_job):
    updates = []
    for key in new_job:
        if key != 'updates' and key in existing_job and existing_job[key] != new_job[key]:
            updates.append(key)
    
    if updates:
        update_info = f"{datetime.now().strftime('%Y-%m-%d')}: {', '.join(updates)}"
        if existing_job.get('updates'):
            existing_job['updates'] += f"; {update_info}"
        else:
            existing_job['updates'] = update_info
        
        for key in updates:
            existing_job[key] = new_job[key]
        return existing_job, True
    else:
        return existing_job, False
def scrape_and_save_page(url, page_number, existing_data):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'http://posturi.gov.ro',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        'TE': 'Trailers'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    updated = False
    new_entries = 0
    
    article_boxes = soup.select('article.box')
    
    for box in article_boxes:
        job = {}
        job['pozitie'] = box.select_one('div.title a').text
        job['url'] = box.select_one('div.title a')['href']
        job['angajator'] = box.select_one('div.angajator').text
        job['detalii'] = ', '.join([n.text for n in box.select('div.n')])
        
        data_div = box.select_one('li.data div.data')
        data_items = [item.strip() for item in data_div.stripped_strings]
        job['publicat_in'] = data_items[0]
        job['expira_in'] = data_items[1]
        
        locatie_div = box.select_one('li.locatie div.locatie')
        job['judet'] = locatie_div.text.strip()
        job['url_judet'] = locatie_div.a['href']
        
        job['tip'] = box.select_one('div.dosar').text
        
        if job['url'] in existing_data:
            existing_job = existing_data[job['url']]
            updated_job, was_updated = compare_and_update(existing_job, job)
            existing_data[job['url']] = updated_job
            updated = updated or was_updated
        else:
            job['updates'] = f"{datetime.now().strftime('%Y-%m-%d')}: New entry"
            existing_data[job['url']] = job
            new_entries += 1
            updated = True
    
    print(f"Page {page_number}: {new_entries} new entries, {len(article_boxes) - new_entries} existing entries checked.")
    return updated

def scrape_all_pages(base_url, max_pages):
    existing_data = load_existing_data()
    
    for page_number in range(1, max_pages + 1):
        url = f"{base_url}/page/{page_number}/"
        print(f"Scraping page {page_number}...")
        updated = scrape_and_save_page(url, page_number, existing_data)
        if not updated:
            print(f"No new or updated entries found on page {page_number}. Stopping the script.")
            break
        sleep_time = random.uniform(0.5, 1.1)
        time.sleep(sleep_time)
    
    save_data(existing_data)
    print("Scraping complete.")

def main():
    try:
        max_pages = get_total_pages(base_url)
        print(f"Total pages to scrape: {max_pages}")
        write_header()
        scrape_all_pages(base_url, max_pages)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        # Log the full traceback
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()


 
    
    

