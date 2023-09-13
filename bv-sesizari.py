
targetFile = 'data/local/BV/sesizari-BV'

import requests, json
import pandas as pd


url = 'https://extranet.brasovcity.ro/MapServer2/WebGis2/wgd/proxy.aspx?MapGuid=18f3da47-53c3-4032-8687-4d9cc7106552&SiteGuid=9be9fc0e-9a41-414a-ae46-88cf067994e6&_layerGuid=cdd70e0d-4e75-44e9-b906-49f902147992'
headers = {
    'Accept': '*/*',
    'Accept-Language': 'en-GB,en;q=0.9',
    'Connection': 'keep-alive',
    'Content-Type': 'application/xml',
    'Cookie': 'ASP.NET_SessionId=deesvexszbsubnonwalbkujm',
    'Origin': 'https://extranet.brasovcity.ro',
    'Referer': 'https://extranet.brasovcity.ro/MapServer2/WebGis2/wgd/',
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

data = '''
<wfs:GetFeature xmlns:wfs="http://www.opengis.net/wfs" service="WFS" version="1.1.0" outputFormat="JSON" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.1.0/wfs.xsd">
    <wfs:Query typeName="BvSPA:V_MAP_INCIDENTE_DISPECERAT" srsName="EPSG:3844" xmlns:BvSPA="BvSPA">
        <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
            <ogc:And>
                <ogc:PropertyIsEqualTo matchCase="true">
                    <ogc:PropertyName>IS_PUBLIC</ogc:PropertyName>
                    <ogc:Literal>T</ogc:Literal>
                </ogc:PropertyIsEqualTo>
                <ogc:BBOX>
                    <ogc:PropertyName>GEOMETRY</ogc:PropertyName>
                    <gml:Envelope xmlns:gml="http://www.opengis.net/gml" srsName="EPSG:3844">
                        <gml:lowerCorner>542677.87327895 460002.6975585</gml:lowerCorner>
                        <gml:upperCorner>552917.87327895 463162.6975585</gml:upperCorner>
                    </gml:Envelope>
                </ogc:BBOX>
            </ogc:And>
        </ogc:Filter>
    </wfs:Query>
</wfs:GetFeature>
'''

response = requests.post(url, headers=headers, data=data)

if response.status_code == 200:
    response_json = response.json()

    with open(targetFile + '.json', 'w', encoding='utf-8') as json_file:
        json.dump(response_json['features'], json_file, ensure_ascii=False, indent=4)
    # df = pd.read_json(response_json['features'])
    # df.to_csv(targetFile + '.csv', encoding='utf-8', index=False)

    print(str(len(response_json['features'])) + " rows saved to " + targetFile)
else:
    print(f"Request failed with status code {response.status_code}")
