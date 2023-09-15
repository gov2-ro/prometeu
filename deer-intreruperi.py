""" 
for each regiune
- [ ] întreruperi accidentale: `incidente.aspx` 
- [ ] întreruperi programate:  `intreruperi<zonă>.aspx` 
    - [ ] today
    - [ ] next 15 days
    - [ ] archive

 """

targets= {
    "MN": ["Prahova", "Brăila", "Buzău"]
    # "MN": ["Prahova", "Brăila", "Buzău", "Dâmbovița", "Galați", "Vrancea"],
    # "TS": ["Brașov", "Alba", "Covasna", "Harghita", "Mureș", "Sibiu"],
    # "TN": ["Cluj", "Bihor", "Bistrița-Năsăud", "Maramureș", "Satu Mare", "Sălaj"]
}

cols_incidente = ['NUMAR LUCRARE', 'JUDEȚ', 'ADRESA', 'DATA ÎNCEPERE', 'DATA FINALIZARE', 'zona']
cols_intreruperi = ['NUMAR LUCRARE', 'SUCURSALA', 'ADRESA', 'DATA ÎNCEPERE', 'DATA FINALIZARE', 'DURATA', 'zona', 'judet']

file_root_incidente = 'data/distributie-energie/deer-incidente'
file_root_intreruperi = 'data/distributie-energie/deer-intreruperi'

import requests
from bs4 import BeautifulSoup
import pandas as pd

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.7',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Cookie': 'cookiesession1=56CBB03A3N3S4Z0IZ3SMSQDGTLJM1261',
    'Origin': 'https://intreruperi.edmn.ro',
    'Referer': 'https://intreruperi.edmn.ro/intreruperiMN.aspx',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Sec-GPC': '1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Brave";v="116"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"'
}


def deer_incidente(zona):
    url = "https://intreruperi.edmn.ro/incidente.aspx?zona=" + zona
    response = requests.get(url, verify=True)

    # Check if the request was successful
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'id': 'tabNeprogramate'})
        data = []

        for row in table.find_all('tr'):
            cols = row.find_all('td')
            cols = [col.text.strip() for col in cols]
            cols.append(zona)
            data.append(cols)

        data = data[1:]
        df = pd.DataFrame(data, columns = cols_incidente)
        return df


        print(f"Data has been extracted and saved to {csv_file}")
    else:
        print(f"3 73 Failed to retrieve data from {url}")    

def deer_intreruperi(zona, judet):
    url = 'https://intreruperi.edmn.ro/intreruperi' + zona + '.aspx'
    response = requests.get(url, verify=True)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        viewstate_input = soup.find('input', {'name': '__VIEWSTATE'})
        viewstategenerator_input = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
        eventvalidation_input = soup.find('input', {'name': '__EVENTVALIDATION'})
        viewstate_value = viewstate_input['value'] if viewstate_input else None
        viewstategenerator_value = viewstategenerator_input['value'] if viewstategenerator_input else None
        eventvalidation_value = eventvalidation_input['value'] if eventvalidation_input else None

        data = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
            '__VIEWSTATE': viewstate_value,
            '__VIEWSTATEGENERATOR': viewstategenerator_value,
            '__EVENTVALIDATION': eventvalidation_value,
            'ddlSucursale': judet,
            'radioCriterii': 'radioAzi15',
            'cmdIntreruperi': 'Afișează+întreruperi+...'
        }

        response = requests.post(url, headers=headers, data=data, verify=True)
        if response.status_code == 200:
            # print(response.text)
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'id': 'tabIntreruperi'})
            datax = []

            for row in table.find_all('tr'):
                cols = row.find_all('td')
                cols = [col.text.strip() for col in cols]
                cols.append(zona)
                cols.append(judet)
                datax.append(cols)

            datax = datax[1:]
            df = pd.DataFrame(datax, columns= cols_intreruperi)
                 
            return df
                
            breakpoint()
        else:
            print(f"1 120 Request failed with status code: {response.status_code}")
            print(viewstate_value)
            print(viewstategenerator_value)
            print(eventvalidation_value)
            # exit()

    else:
        print("2 124 Failed to fetch the URL. Status code:", response.status_code)


incidente = pd.DataFrame(columns= cols_incidente)
intreruperi = pd.DataFrame(columns= cols_intreruperi)

for key, regiune in targets.items():
    urlincidente = 'https://intreruperi.edmn.ro/incidente.aspx?zona=' + key
    kk = deer_incidente(key)
    incidente = pd.concat([incidente, kk], ignore_index=True)

    for judet in regiune:
        print(key + ' - ' +judet)
        try:
            zz = deer_intreruperi(key, judet)
            intreruperi = pd.concat([intreruperi, zz], ignore_index=True)
        except:
            continue



incidente.to_csv(file_root_incidente + '.csv', encoding='utf-8', index=False)
incidente.to_json(file_root_incidente + '.json', orient='records', lines=True)
intreruperi.to_csv(file_root_intreruperi + '.csv', encoding='utf-8', index=False)
intreruperi.to_json(file_root_intreruperi + '.json', orient='records', lines=True)

print('saved ' + str(len(incidente)) + ' incidents')
print('saved ' + str(len(intreruperi)) + ' intreruperi')
 

 
 

 




