import json, re, requests
# from bs4 import BeautifulSoup

ziurl = 'https://www.cmteb.ro/harta_stare_sistem_termoficare_bucuresti.php'
data_root = 'data/cmteb/'

def fetch_and_save_html(url):
    # current_date_time = datetime.datetime.now().strftime('%y-%m-%d %H:%M')

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch data from the website. HTTP Error {response.status_code}")
        return None

    return response.text

def extract_json_from_html(html_content):

    passed_features = {}
    for color in ['verde', 'rosu', 'galben']:
        pattern = r'var passedFeatures_{} = (.+?);'.format(color)
        data = re.search(pattern, html_content)
        if data:
            data_str = data.group(1)
            passed_features[color] = json.loads(data_str)
        # else:
            # print(f"Data for '{color}' not found in the HTML.")

    return passed_features

def save_json_to_file(data):
    # current_date_time = datetime.datetime.now().strftime('%y-%m-%d %H:%M')
    
    json_file = f'{data_root}/latest.json'
    with open(json_file, 'w') as file:
        json.dump(data, file, indent=4)

    return data


if __name__ == "__main__":
    url = ziurl

    cached_html = fetch_and_save_html(url)

    data = extract_json_from_html(cached_html)

    print(json.dumps(data, indent=4))
    save_json_to_file(data)