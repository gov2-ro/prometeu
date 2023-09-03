import json, requests, re, json5
from bs4 import BeautifulSoup
import pandas as pd
from utils.common import fetch_data, save_json_to_file, data_root

ziurl = 'https://andnet.ro/dispecerat/api/java.php'
data_folder = data_root +'andnet/'
outputFileRoot='situatia-drumurilor-'

""" 
# ANDNET.ro: Starea drumurilor din România

## Roadmap

- [x] decode json
- [x] split paths, points
- [x] extract data from 'Desc'
- [x] extract coords
- [x] compact coords
- [x] extract ranges: perioada, km
- [ ] save as csv

 """

def extract_json(carne):
    # Find and extract all JavaScript arrays into a list
    # array_matches = re.findall(r'var (\w+) = \[(.*?)\];', javascript_code, re.DOTALL)

    data_matches = re.findall(r'var data=\[(.*?)\];', carne, re.DOTALL)
    data2_matches = re.findall(r'var data2=\[(.*?)\];', carne, re.DOTALL)

    # Convert the matched JavaScript arrays to valid JSON strings
    data_json = f"[{data_matches[0]}]"
    data2_json = f"[{data2_matches[0]}]"
    
    data = {}
    # print('- json5.loads paths')
    data['paths'] = json5.loads(data_json)
    # print('- json5.loads points')
    data['points'] = json5.loads(data2_json)
    
    return data

def adnet_decode_props(html_string):
    # decodes "<b>Lucrari  DN17D</b><br /><b>Judet:</b> BN;<br /><b>UAT:</b> Rodna, Șanț;<br /><b>Localitati:</b> RODNA (BN)<br /><b>Km:</b> 71+652 - 86+000<br /><b>Perioada:</b> 11-07-2023<b>Tip Lucrari:</b><br />Raforsare ...<br /><b>Variante de ocolire:</b><br />Se circula ..."
    # into json

    ll = html_string.replace('\n', ' ')

    ll = ll.split('<b>')
    ll.pop(0)
    name = ll.pop(0)
    name = name.replace('</b>', '').replace('<br />', '').replace('<br>', '').replace('<br/>', '').replace('\n', '').strip() 
    obj = {
        'name': name
    }
    for chunk in ll:
        bb = chunk.split('</b>')
        key = bb[0].strip().strip(':')
        key = key.replace('<br />', '').replace('<br>', '').replace('<br/>', '').replace('\n', '').strip()
        value = re.sub(' +', ' ', bb[1]).strip()
        value = value.replace('<br />', '\n').replace('<br>', '\n').replace('<br/>', '\n').strip()
        value = value.replace(' \n', '\n').strip()
        value=value.strip('\n')
        obj[key] = value

    return(obj)


def decode_html(zitem):
        # extracts entities from Desc, text, splits Perioada, km

        zitem.update(adnet_decode_props(zitem["Desc"]))
        
        if len(item['coords']) == 2:
            zitem['lat'] = zitem['coords'][0]
            zitem['long'] = zitem['coords'][1]
        del zitem["Desc"]
        start_stop=zitem['Perioada'].split(' - ')
        zitem['date_start'] = start_stop[0]
        zitem['date_end'] = start_stop[1]
        del zitem["Perioada"]
        km_start_stop=zitem['Km'].split(' - ')
        if len(km_start_stop) == 2:
            zitem['km_start'] = km_start_stop[0]
            zitem['km_end'] = km_start_stop[1]


if __name__ == "__main__":
    url = ziurl
    # cached_html = fetch_data(url)
    # print('-- data fetched from ' + url)
    # data = extract_json(cached_html)

    f = open(data_folder + '_obsolete/andnet-cached.html') 
    xx = f.read()  
    data = extract_json(xx)  
    # print('- extracted json')


    
    
    for item in data["points"]:
        decode_html(item)
    # print('- points loaded')
    
    for item in data["paths"]:
        decode_html(item)
    # print('- paths loaded')

    # save jsons
    save_json_to_file(data['points'], data_folder + outputFileRoot + 'points.json', 'compact', 'overwrite')
    save_json_to_file(data['paths'],  data_folder + outputFileRoot + 'paths.json',  'compact', 'overwrite')
    print('-- saved ' + str(len(data['points'])) + ' points and ' + str(len(data['paths'])) + ' paths.' )
    # save csvs
    df_points = pd.read_json(json.dumps(data['points']))
    df_points.to_csv(data_folder + outputFileRoot + 'points.csv', encoding='utf-8', index=False)
    df_paths = pd.read_json(json.dumps(data['paths']))
    df_paths.to_csv(data_folder + outputFileRoot + 'paths.csv', encoding='utf-8', index=False)
