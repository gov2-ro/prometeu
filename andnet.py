ziurl = 'https://andnet.ro/dispecerat/api/java.php'
data_root = 'data/andnet'

import json, requests, re, json5

def fetch_data(url):
    # current_date_time = datetime.datetime.now().strftime('%y-%m-%d %H:%M')
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch data from the website. HTTP Error {response.status_code}")
        return None

    return response.text

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

def save_json_to_file(data):
    # current_date_time = datetime.datetime.now().strftime('%y-%m-%d %H:%M')
    
    json_file = f'{data_root}/latest.json'
    with open(json_file, 'w') as file:
        json.dump(data, file, indent=4)

    return data

if __name__ == "__main__":
    url = ziurl

    cached_html = fetch_data(url)

    data = extract_json(cached_html)

    # print(json.dumps(data, indent=4))
    save_json_to_file(data)