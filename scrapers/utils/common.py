import json, re, requests

data_root = '../data/'
# owner = "gov2-ro"
# repo = "gh-scraping-data"

def fetch_html(url):
    # current_date_time = datetime.datetime.now().strftime('%y-%m-%d %H:%M')
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch data from the website. HTTP Error {response.status_code}")
        return None

    return response.text
# Define a custom sorting key function

def order_bylatlong(item):
    # TODO: add parameter to select, NW, SE , order?
    return (item["longitudine"], item["latitudine"])

""" def extract_json_from_html(html_content):
    #    verde  --> functionale   #
	#    galben --> deficiente    #
	#    rosu   --> avarii	      #
    alldata = []
    nicedata = stats = {}

    for color in ['verde', 'rosu', 'galben']:
        pattern = r'var passedFeatures_{} = (.+?);'.format(color)
        data = re.search(pattern, html_content)
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
    return sorted_data """

def save_json_to_file(data, target_file_path, inline_keys = []):
    # TODO: compact some keys
    # current_date_time = datetime.datetime.now().strftime('%y-%m-%d %H:%M')
    
    json_file = target_file_path
    with open(json_file, 'w') as file:
        json.dump(data, file, indent=4)
    # return data

def compact_coords_json(input_json):
    input_json_str = json.dumps(input_json)

    # Define a regular expression pattern to match coordinates
    pattern = r'\[\s*(\d+\.\d+)\s*,\s*(\d+\.\d+)\s*\]'

    # Replace coordinates with compacted format
    output_json_str = re.sub(pattern, r'[\1,\2]', input_json_str)

    return output_json_str