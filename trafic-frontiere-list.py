""" 
Intrare: 5 artere; Iesire: 7 artere. Trafic intens - numar mare de autoturisme prezente la verificarile de frontiera pe sensul de iesire din tara. RECOMANDARE: pentru evitarea aglomerarilor, puteti folosi si alte puncte de trecere a frontierei!
Denumire  |  Timp  |  Info  |  Unelte
- [x] fetch tables/list
- [ ] fetch map
- [x] export CSV
- [ ] Detect fields inside Info:
    - [ ] nr artere intrare / ieșire
    - [ ] recomandari: 
    - [ ] trafic intens:
    - [ ] tonaj admis
    - [ ] orar
- [x] export json
- [ ] export GeoJson - see trafic-frontiere-markers.py
 """


url = 'https://www.politiadefrontiera.ro/ro/traficonline/'
filename  = 'data/politia-de-frontiera/trafic-frontiere'

import requests, csv, re
import pandas as pd
from bs4 import BeautifulSoup
zicolumns = ['Denumire', 'Timp', 'Info', 'Latitude', 'Longitude', 'Status', 'Tip vehicul', 'Sens']
# Define the base URL
base_url = url

# Define the sources with different url_vars
sources = [
    {"tip_vehicul": "Autoturisme", "sens": "Intrare", "url_vars": "?vw=2&vt=1&dt=1"},
    {"tip_vehicul": "Autoturisme", "sens": "Ieșire", "url_vars": "?vw=2&vt=1&dt=2"},
    {"tip_vehicul": "Camioane", "sens": "Intrare", "url_vars": "?vw=2&vt=2&dt=1"},
    {"tip_vehicul": "Camioane", "sens": "Ieșire", "url_vars": "?vw=2&vt=2&dt=2"}
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}



def extract_fields(html):
    combined_data = []
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('div', {'id': 'maplist'}).find('table')

    for row in table.find('tbody').find_all('tr'):
        columns = row.find_all('td')
        denumire = columns[0].text.strip()

        timp_text = columns[1].text.strip()
        timp_match = re.search(r'(\d+) min\.', timp_text)
        timp = int(timp_match.group(1)) if timp_match else None

        info = columns[2].text.strip()
        # TODO: detect details in info, recomandări etc
        """ 
        Intrare: 5 artere; Iesire: 6 artere. Trafic intens - numar mare de autoturisme prezente la verificarile de frontiera pe ambele sensuri. RECOMANDARE: pentru evitarea aglomerarilor, puteti folosi si alte puncte de trecere a frontierei! 
        - split by '.' into sentences
        check for: recomandare, trafic intens -, arter
            """
        infoz=info.split('.')

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

        tip_vehicul = source['tip_vehicul']
        sens = source['sens']

        combined_data.append([denumire, timp, info, latitude, longitude, level, tip_vehicul, sens])
    return combined_data

allnice = 1
for source in sources:
    url = base_url + source['url_vars']
    try:
        response = requests.get(url, headers=headers)
    except requests.exceptions.ConnectionError:
        allnice = 0
        # response.status_code = "Connection refused"
        # TODO: logging

    if allnice and response.status_code == 200:
        combined_data = extract_fields(response.text)
    else:
        print(f'Failed to fetch the URL for source: {source}. Status code: {response.status_code}')
        # TODO: logging


if allnice:
    with open(filename + '.csv', 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(zicolumns)
        writer.writerows(combined_data)

    csv_obj = pd.DataFrame(combined_data, columns = zicolumns)
    # csv_obj.to_json(filename + '.json', orient = "records", date_format = "epoch", double_precision = 10, force_ascii = True, date_unit = "ms", default_handler = None)
    csv_obj.to_json(filename + '.json', orient = "records", force_ascii = False, indent=2 )

    print(f'Scraped & saved to {filename}.csv/json')

else:
    print('meh buba')