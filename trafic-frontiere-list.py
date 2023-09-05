
url = 'https://www.politiadefrontiera.ro/ro/traficonline/'
csv_filename = 'data/politia-de-frontiera/trafic-frontiere.csv'

import requests
from bs4 import BeautifulSoup
import csv
import re

# Define the base URL
base_url = url

# Define the sources with different url_vars
sources = [
    {"tip_vehicol": "Autoturisme", "sens": "Intrare", "url_vars": "?vt=1&vw=2&dt=1"},
    {"tip_vehicol": "Autoturisme", "sens": "Ieșire", "url_vars": "?vt=1&vw=2&dt=2"},
    {"tip_vehicol": "Camioane", "sens": "Intrare", "url_vars": "?vt=2&vw=2&dt=1"},
    {"tip_vehicol": "Camioane", "sens": "Ieșire", "url_vars": "?vt=2&vw=2&dt=2"}
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

combined_data = []

for source in sources:
    url = base_url + source['url_vars']
    try:
        response = requests.get(url, headers=headers)
    except requests.exceptions.ConnectionError:
        response.status_code = "Connection refused"

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('div', {'id': 'maplist'}).find('table')

        for row in table.find('tbody').find_all('tr'):
            columns = row.find_all('td')
            denumire = columns[0].text.strip()

            timp_text = columns[1].text.strip()
            timp_match = re.search(r'(\d+) min\.', timp_text)
            timp = int(timp_match.group(1)) if timp_match else None

            info = columns[2].text.strip()

            unelte_url = columns[3].find('a')['href'] if columns[3].find('a') else ''
            lat_long_match = re.search(r'(\d+\.\d+),(\d+\.\d+)', unelte_url)
            if lat_long_match:
                latitude = lat_long_match.group(1)
                longitude = lat_long_match.group(2)
            else:
                latitude = ''
                longitude = ''

            timp_span = columns[1].find('span', {'class': re.compile(r'iwrow iws iw_\w+')})
            color_match = re.search(r'iw_(\w+)', timp_span['class'][2]) if timp_span else None
            level = color_match.group(1) if color_match else None

            tip_vehicol = source['tip_vehicol']
            sens = source['sens']

            combined_data.append((denumire, timp, info, latitude, longitude, level, tip_vehicol, sens))
    else:
        print(f'Failed to fetch the URL for source: {source}. Status code: {response.status_code}')


with open(csv_filename, 'w', newline='', encoding='utf-8') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(['Denumire', 'Timp', 'Info', 'Latitude', 'Longitude', 'Level', 'tip_vehicol', 'sens'])
    writer.writerows(combined_data)

print(f'Scraped & saved to {csv_filename}')
