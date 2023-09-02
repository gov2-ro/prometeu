""" 
# CMTEB.ro: Harta Stare Sistem Termoficare Bucuresti 
sorted by lat/long 

## coloane
- stare
- culoare
- denumire
- longitudine
- latitudine
- tip
- remediere
- status

## Roadmap
- [x] refactor json
- [x] order by lat long
- [ ] save stats to file
- [ ] save as csv
- [ ] meaningful commit msg
 """

import json, re
# from bs4 import BeautifulSoup
from utils.common import fetch_html, order_bylatlong, save_json_to_file,  data_root

ziurl = 'https://www.cmteb.ro/harta_stare_sistem_termoficare_bucuresti.php'
data_folder = data_root +'cmteb/'
legend = {'verde': 'functionale', 'galben': 'deficiente', 'rosu': 'avarii'}
outputFile = 'status-sistem-termoficare-bucuresti.json'
inline_keys = ['longitudine', 'latitudine']

def extract_json_from_html(html_content):
    alldata = []
    nicedata = stats = {}
    for color in ['verde', 'rosu', 'galben']:
        pattern = r'var passedFeatures_{} = (.+?);'.format(color)
        data = re.search(pattern, fetch_html(ziurl))
        if data:
            data_str = data.group(1)
            # nicedata[color] = json.loads(data_str)
            nicedata = json.loads(data_str)
            for d in nicedata:
                d['status'] = legend[color]
        # else:
            # TODO: log errors
            # print(f"Data for '{color}' not found in the HTML.")
        stats[legend[color]] = len(nicedata)
        alldata += nicedata
    
    sorted_data = sorted(alldata, key=order_bylatlong)

    print(stats)
 
    # print(json.dumps(sorted_data, indent=4))  
    # save_json_to_file(sorted_data, data_root+outputFile)
    # print('saved ' + str(len(data)) + ' records to ' + data_root + data_folder +  outputFile )
    # ll = json.dumps(sorted_data)
    return sorted_data
 
if __name__ == "__main__":
    zidata = extract_json_from_html(fetch_html(ziurl))
    
    save_json_to_file(zidata, data_folder+outputFile)
    print('saved ' + str(len(zidata)) + ' records to ' + data_folder +  outputFile )
