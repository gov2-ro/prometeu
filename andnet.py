import json, requests, re, json5
from bs4 import BeautifulSoup
from utils.common import fetch_data, save_json_to_file, data_root

ziurl = 'https://andnet.ro/dispecerat/api/java.php'
data_folder = data_root +'andnet/'
outputFile='situatia-drumurilor.json'

""" 
# ANDNET.ro: Starea drumurilor din România

## Roadmap

- [x] decode json
- [x] split paths, points
- [x] extract data from 'Desc'
- [x] extract coords
- [x] compact coords
- [x] extract ranges: perioada, km

 """


def extract_json(carne):
    # Find and extract all JavaScript arrays into a list
    # array_matches = re.findall(r'var (\w+) = \[(.*?)\];', javascript_code, re.DOTALL)
    # Extract the JavaScript arrays from the code using regex (assuming each array is on a separate line)

    data_matches = re.findall(r'var data=\[(.*?)\];', carne, re.DOTALL)
    data2_matches = re.findall(r'var data2=\[(.*?)\];', carne, re.DOTALL)

    # Convert the matched JavaScript arrays to valid JSON strings
    data_json = f"[{data_matches[0]}]"
    data2_json = f"[{data2_matches[0]}]"
    
    # Parse the JSON strings as Python dictionaries
    data = {}
    data['paths'] = json5.loads(data_json)
    data['points'] = json5.loads(data2_json)
    
    return data


def extract_bold_text(input_string):
    # Define a regular expression pattern to match <b>bold:</b> text
    # get name - TODO: refactor
    
    result = {}
    
    soup = BeautifulSoup(input_string, 'html.parser')
    name = soup.find('b').text.strip()
    result['name'] = name

    name_tag = soup.find('b')
    if name_tag:
        name_tag.extract()
    input_string = str(soup)
    pattern = r'<b>(.+?):</b>\s*(.*?)\s*<'

    # Find all matches in the input string
    matches = re.findall(pattern, input_string)

    for match in matches:
        key = match[0].strip()  # Remove leading and trailing whitespace
        value = match[1].strip()  # Remove leading and trailing whitespace
        result[key] = value

    return result


def decode_html(zitem):
        # extracts entities from Desc, text, splits Perioada, km

        zitem.update(extract_bold_text(zitem["Desc"]))
        
        if len(item['coords']) == 2:
            zitem['lat'] = zitem['coords'][0]
            zitem['long'] = zitem['coords'][1]
        del zitem["Desc"]
        start_stop=zitem['Perioada'].split(' - ')
        zitem['date_start'] = start_stop[0]
        zitem['date_end'] = start_stop[1]
        del zitem["Perioada"]
        km_start_stop=zitem['Km'].split(' - ')
        zitem['km_start'] = km_start_stop[0]
        zitem['km_end'] = km_start_stop[1]
 

if __name__ == "__main__":
    url = ziurl
    cached_html = fetch_data(url)
    data = extract_json(cached_html)
    
    # - test w locally cached data 
    # f = open(data_folder + 'latest.json')
    # data = json.load(f)    

    for item in data["points"]:
        decode_html(item)

    for item in data["paths"]:
        decode_html(item)

    save_json_to_file(data['points'], data_folder + 'points.json', 'compact')
    save_json_to_file(data['paths'],  data_folder + 'paths.json',  'compact')
    