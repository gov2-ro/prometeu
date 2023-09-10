""" 
frecvență?

for each regiune
- [x] întreruperi accidentale: `incidente.aspx` 
- [ ] întreruperi programate:  `intreruperi<zonă>.aspx` 
    - [ ] today
    - [ ] next 15 days
    - [ ] archive

 """

targets= {
    "MN": ["Prahova", "Brăila", "Buzău", "Dâmbovița", "Galați", "Vrancea"],
    "TS": ["Brașov", "Alba", "Covasna", "Harghita", "Mureș", "Sibiu"],
    "TN": ["Cluj", "Bihor", "Bistrița-Năsăud", "Maramureș", "Satu Mare", "Sălaj"]
}

cols_incidente = ['NUMAR LUCRARE', 'JUDEȚ', 'ADRESA', 'DATA ÎNCEPERE', 'DATA FINALIZARE', 'zona']
 
file_root_incidente = 'data/distributie-energie/deer-incidente'
 
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
    response = requests.get(url, headers=headers)

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
        print(f" E72 Failed to retrieve data from {url}")    


incidente = pd.DataFrame(columns= cols_incidente)

for key, regiune in targets.items():
    urlincidente = 'https://intreruperi.edmn.ro/incidente.aspx?zona=' + key
    kk = deer_incidente(key)
    incidente = pd.concat([incidente, kk], ignore_index=True)

    # for judet in regiune:
    #     print(key + ' - ' +judet)
    #     zz = deer_intreruperi(key, judet)
    #     intreruperi = pd.concat([intreruperi, zz], ignore_index=True)



incidente.to_csv(file_root_incidente + '.csv', encoding='utf-8', index=False)
incidente.to_json(file_root_incidente + '.json', orient='records', lines=True)
# intreruperi.to_csv(file_root_intreruperi + '.csv', encoding='utf-8', index=False)
# intreruperi.to_json(file_root_intreruperi + '.json', orient='records', lines=True)

print('saved ' + str(len(incidente)) + ' incidents')
# print('saved ' + str(len(intreruperi)) + ' intreruperi')
 

 
 

 




