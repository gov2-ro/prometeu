targetFile = 'data/local/B/avarii-B'

import requests, json, pyproj
import pandas as pd


# Define the URL and headers
url = 'https://hip.pmb.ro/hip/proxy.aspx?MapGuid=72d6f523-5edb-427f-9b0e-3e03b6ba177f&SiteGuid=76c2a7a5-9eab-4a3f-9b04-fd89109b19e4&_layerGuid=61a90ddf-d218-401a-a765-dc972563b7fc'
headers = {
    'Accept': '*/*',
    'Accept-Language': 'en-GB,en;q=0.9',
    'Connection': 'keep-alive',
    'Content-Type': 'application/xml',
    'Cookie': 'ASP.NET_SessionId=bzko2zpjoqkbbcnvo03zvfmh',
    'Origin': 'https://hip.pmb.ro',
    'Referer': 'https://hip.pmb.ro/hip/?SiteGuid=76c2a7a5-9eab-4a3f-9b04-fd89109b19e4&MapGuid=72d6f523-5edb-427f-9b0e-3e03b6ba177f',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-GPC': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Brave";v="116"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
}
source_crs = pyproj.CRS.from_epsg(3844)
target_crs = pyproj.CRS.from_epsg(4326)
# Define the XML payload
data = '''
<wfs:GetFeature xmlns:wfs="http://www.opengis.net/wfs" service="WFS" version="1.1.0" outputFormat="JSON" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.1.0/wfs.xsd">
    <wfs:Query typeName="pca:v_hip_avarii" srsName="EPSG:3844" xmlns:pca="pca"/>
</wfs:GetFeature>
'''

# Send the POST request
response = requests.post(url, headers=headers, data=data)
flattened_data = []
transformer = pyproj.Transformer.from_crs(source_crs, target_crs, always_xy=True)


# Check the response
if response.status_code == 200:
    response_json = response.json()
    for entry in response_json['features']:
        flat_entry = {}
        flat_entry.update(entry['properties'])
        flat_entry['type'] = entry['type']
        flat_entry['id'] = entry['id']
        flat_entry['geometry_type'] = entry['geometry']['type']
        lon, lat = transformer.transform(entry['geometry']['coordinates'][0], entry['geometry']['coordinates'][1])
        flat_entry['Lat'] = lat
        flat_entry['Long'] = lon
        flattened_data.append(flat_entry)

    with open(targetFile + '.json', 'w', encoding='utf-8') as json_file:
        json.dump(flattened_data, json_file, ensure_ascii=False, indent=4)

    df = pd.DataFrame(flattened_data)
    df.to_csv(targetFile + '.csv', index=False)

    print(str(len(response_json['features'])) + " rows saved to " + targetFile)

else:
    print(f"Request failed with status code {response.status_code}")
