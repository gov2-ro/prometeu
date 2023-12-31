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
- [x] save as csv
- [x] check if changed
- [ ] meaningful commit msg
 """

import json, re
# from bs4 import BeautifulSoup
import pandas as pd
from utils.common import fetch_data, order_bylatlong, order_by_denumire, save_json_to_file,  data_root

ziurl = 'https://www.cmteb.ro/harta_stare_sistem_termoficare_bucuresti.php'
data_folder = data_root +'cmteb/'
legend = {'verde': 'functionale', 'galben': 'deficiente', 'rosu': 'avarii'}
outputFileRoot = 'status-sistem-termoficare-bucuresti'

def extract_json_from_html(html_content):
    alldata = []
    nicedata = stats = {}
    for color in ['verde', 'rosu', 'galben']:
        pattern = r'var passedFeatures_{} = (.+?);'.format(color)
        data = re.search(pattern, fetch_data(ziurl))
        if data:
            data_str = data.group(1)
            # nicedata[color] = json.loads(data_str)
            nicedata = json.loads(data_str)
            for dx in nicedata:
                dx['status'] = legend[color]
                dx['Lat'] = dx['latitudine']
                dx['Long'] = dx['longitudine']
                del dx['latitudine']
                del dx['longitudine']
                # strip spaces from strings
                for key, val in dx.items():
                    if type(val) is str:
                        dx[key] = val.strip()
            
        stats[legend[color]] = len(nicedata)
        alldata += nicedata
    
    sorted_data = sorted(alldata, key=order_bylatlong)
    # sorted_data = sorted(alldata, key=order_by_denumire)
    
    print(stats)

    return sorted_data
 
if __name__ == "__main__":
    zidata = extract_json_from_html(fetch_data(ziurl))
    save_json_to_file(zidata, data_folder+outputFileRoot+'.json', 'pretty_ensure_ascii_false' )
    df = pd.read_json(json.dumps(zidata))
    df.to_csv(data_folder + outputFileRoot + '.csv', encoding='utf-8', index=False, columns = ['denumire','status','stare','tip','remediere','culoare','Lat','Long'])
    print('saved ' + str(len(zidata)) + ' records to ' + data_folder +  outputFileRoot + ' .csv/json' )

