import requests, json
import pandas as pd

# Define the URL and headers
url = 'https://opendata.oras.digital/api/proxy/'
targetRoot = 'data/local/IS/calitate-aer-is'
headers = {
    'authority': 'opendata.oras.digital',
    'accept': 'application/json',
    'accept-language': 'en-GB,en;q=0.5',
    'cache-control': 'max-age=0',
    'content-type': 'application/json',
    'cookie': 'od=g91uc0d89fckttho2skj64apu9; od=g91uc0d89fckttho2skj64apu9',
    'origin': 'https://opendata.oras.digital',
    'referer': 'https://opendata.oras.digital/dataset/cf3f-2309-44d1-8e0c-1137/',
    'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Brave";v="116"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sec-gpc': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
}

# Define the payload as a Python dictionary
payload = {
    "action": "fetch",
    "type": "api",
    "value": "cf3f-2309-44d1-8e0c-1137"
}

# Send the POST request with JSON payload
response = requests.post(url, headers=headers, json=payload)

# Check the response
if response.status_code == 200:
    # Parse the JSON response
    response_json = response.json()

    # Save the JSON data to a file
    with open(targetRoot + '.json', 'w', encoding='utf-8') as json_file:
        json.dump(response_json, json_file, ensure_ascii=False, indent=4)
    
    df = pd.DataFrame(response_json)
    df.to_csv(targetRoot + '.csv', index=False)

    print(str(len(response_json)) + " rows saved to " + targetRoot)
 
else:
    print(f"Request failed with status code {response.status_code}")
