""" 
 
 """

url = 'https://www.politiadefrontiera.ro/ro/traficonline/'
filename = 'data/politia-de-frontiera/trafic-frontiere-map'

import requests, re, json5
import pandas as pd
from bs4 import BeautifulSoup


zicolumns = ['Denumire', 'Timp', 'Info', 'Latitude', 'Longitude', 'Status', 'Tip vehicul', 'Sens']

base_url = url
sources = [{
    "tip_vehicul": "Autoturisme",
    "sens": "Intrare",
        "url_vars": "?vw=1&vt=1&dt=1"
    }, {
        "tip_vehicul": "Autoturisme",
        "sens": "Ieșire",
        "url_vars": "?vw=1&vt=1&dt=2"
    }, {
        "tip_vehicul": "Camioane",
        "sens": "Intrare",
        "url_vars": "?vw=1&vt=2&dt=1"
    }, {
        "tip_vehicul": "Camioane",
        "sens": "Ieșire",
        "url_vars": "?vw=1&vt=2&dt=2"
    }]

headers = {
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

title_pattern = r'<strong>(.*?)<\/strong>'
wait_time_pattern = r'Timp de așteptare (\d+) min.'
info_pattern = r'hlrow">(.*?)<\/span>'
vehicle_pattern = r'fa-(.*?)"></i>'
status_pattern = r'iw_(.*?)">'

def extract_json(carne):
    soup = BeautifulSoup(carne, 'html.parser')
    # script_tag = soup.find('script', text=re.compile(r'var markers = \[.*?\];', re.DOTALL))
    script_tag = soup.find('script', string=re.compile(r'var markers = \[.*?\];', re.DOTALL))

    javascript_code = script_tag.text

    matches = re.search(r'var markers = (\[.*?\]);', javascript_code, re.DOTALL)
    if matches:
        json_str = matches.group(1)
        json_str = json_str.replace('\n', '').replace('\t', '')      
        markers = json5.loads(json_str)
        return markers
    else:
        print("JSON data not found in the script tag.")

combined_data = []

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
        jlist = extract_json(response.text)
        # jjson is a list of json dicts
        # detect fields in description
        
        for element in jlist:
            newobj = {}
            # title = wait_time = info = vehicle = status = ''
            title = re.search(title_pattern, element['description']).group(1)
            wait_time = int(re.search(wait_time_pattern, element['description']).group(1))
            info = re.search(info_pattern, element['description']).group(1)
            vehicle = re.search(vehicle_pattern, element['description']).group(1)
            status = re.search(status_pattern, element['description']).group(1)

            newobj["Denumire"] =  title
            newobj["Timp"] =  wait_time
            newobj["Info"] =  info
            # element["Latitude"] =  vehicle
            newobj["Status"] =  element['marker_color']
            # element["Status"] =  element['status']
            newobj["Sens"] =  source['sens']
            newobj["Tip vehicul"] =  source['tip_vehicul']
            newobj["Denumire"] = element['title']
            newobj["Latitude"] = element['lat']
            newobj["Longitude"] = element['lng']
            combined_data.append(newobj)

         
    else:
        print(
            f'Failed to fetch the URL for source: {source}. '
        )
        allnice = 0
        # continue # continue the loop, advance to next item
        break #exit the loop
        # TODO: logging


if allnice:
    csv_obj = pd.DataFrame(combined_data, columns=zicolumns)
    sorted_df = csv_obj.sort_values(by=['Denumire', 'Tip vehicul', 'Sens'])

    sorted_df.to_json(filename + '.json',
                    orient="records",
                    force_ascii=False,
                    indent=2)
    sorted_df.to_csv(filename + '.csv', encoding='utf-8', index=False)

    print(f'Scraped & saved to {filename}.csv/json')
else:
    print('all not nice')
