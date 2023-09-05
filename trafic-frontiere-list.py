
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

# Initialize a list to store the combined data
combined_data = []

# Iterate through the sources
for source in sources:
    # Construct the complete URL for each source
    url = base_url + source['url_vars']

    # Send an HTTP GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the table element with id "maplist"
        table = soup.find('div', {'id': 'maplist'}).find('table')

        # Iterate through the rows of the table
        for row in table.find('tbody').find_all('tr'):
            # Extract data from each column in the row
            columns = row.find_all('td')
            denumire = columns[0].text.strip()

            # Extract the numeric part from the "Timp" column using regex
            timp_text = columns[1].text.strip()
            timp_match = re.search(r'(\d+) min\.', timp_text)
            timp = int(timp_match.group(1)) if timp_match else None

            info = columns[2].text.strip()

            # Extract latitude and longitude from the "Unelte" URL using regex
            unelte_url = columns[3].find('a')['href'] if columns[3].find('a') else ''
            lat_long_match = re.search(r'(\d+\.\d+),(\d+\.\d+)', unelte_url)
            if lat_long_match:
                latitude = lat_long_match.group(1)
                longitude = lat_long_match.group(2)
            else:
                latitude = ''
                longitude = ''

            # Extract color from "Timp" column based on class
            timp_span = columns[1].find('span', {'class': re.compile(r'iwrow iws iw_\w+')})
            color_match = re.search(r'iw_(\w+)', timp_span['class'][2]) if timp_span else None
            level = color_match.group(1) if color_match else None

            # Add "tip_vehicol" and "sens" columns from the source
            tip_vehicol = source['tip_vehicol']
            sens = source['sens']

            # Append the data to the combined_data list as a tuple
            combined_data.append((denumire, timp, info, latitude, longitude, level, tip_vehicol, sens))
    else:
        print(f'Failed to fetch the URL for source: {source}. Status code: {response.status_code}')


# Write the combined data to a CSV file
with open(csv_filename, 'w', newline='', encoding='utf-8') as csv_file:
    writer = csv.writer(csv_file)
    # Write header row
    writer.writerow(['Denumire', 'Timp', 'Info', 'Latitude', 'Longitude', 'Level', 'tip_vehicol', 'sens'])
    # Write data rows
    writer.writerows(combined_data)

print(f'Data from multiple sources scraped and saved to {csv_filename}')
