import requests, json
import pandas as pd

url = 'https://ineuportalgis.enel.com/server/rest/services/Hosted/ROM_Outages_Map_Layer_view/FeatureServer/0/query?where=0%3D0&outFields=%2A&f=json' 
data_folder = 'data/distributie-energie/'
legend = {'verde': 'functionale', 'galben': 'deficiente', 'rosu': 'avarii'}
outputFileRoot = 'intreruperi-enel'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Referer': 'https://www.e-distributie.com/ro/intreruperi-curent.html',
}

try:  
    response = requests.get(url, headers=headers)
    if response.status_code == 200:      
        data = response.json() 
        if 'features' in data:
            features = data['features']
            niceObj =[]
            for feature in data['features']:
                attr = feature.get('attributes', {})
                # Rename coordinate fields if present
                if 'longitudin' in attr:
                    attr['Long'] = attr.pop('longitudin')
                if 'latitudine' in attr:
                    attr['Lat'] = attr.pop('latitudine')
                # Remove Descriere (Italian duplicate of description)
                attr.pop('Descriere', None)
                attr.pop('descrizion', None)
                niceObj.append(attr)
 
            with open(data_folder + outputFileRoot + '.json', 'w') as outfile:
                json.dump(niceObj, outfile, indent=4)
            count = len(niceObj)
            df = pd.read_json(json.dumps(niceObj))
            df.to_csv(data_folder + outputFileRoot + '.csv', encoding='utf-8', index=False)
            print('enel: ' + str(count) + " incident saved to: " +  data_folder + outputFileRoot + '.json/csv')
        else:
            print("No 'features' key found in the JSON response.")
    else:
        print(f"Request failed with status code: {response.status_code}")
except Exception as e:
    print(f"An error occurred: {str(e)}")
