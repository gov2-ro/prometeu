import requests, json
import pandas as pd
from pandas import json_normalize


targetRoot = 'data/local/B/aerlive-bucuresti'
# Define the URL and headers
url = 'https://apps.roiot.ro/aerlive/api-v2/data.php'
headers = {
    'Accept': '*/*',
    'Accept-Language': 'en-GB,en;q=0.7',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'https://aerlive.ro',
    'Referer': 'https://aerlive.ro/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'Sec-GPC': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Brave";v="116"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
}

# Define the payload as a dictionary
payload = {
    'key': 'd09668ea-def5-44ea-8c77-ae32e9fa5572',
    'city': 'BUC'
}

# Send the POST request with URL-encoded payload
response = requests.post(url, headers=headers, data=payload)

# Check the response
if response.status_code == 200:
    # Parse the JSON response
    response_json = response.json()

    
else:
    print(f"Request failed with status code {response.status_code}")
    exit()

  

 
with open(targetRoot + '.json', 'w', encoding='utf-8') as json_file:
    json.dump(response_json['data'], json_file, ensure_ascii=False, indent=4)

print(str(len(response_json['data'])) + " rows saved to " + targetRoot)

# Create an empty list to store flattened data
flattened_data = []
data = response_json['data']
for entry in data:
    # Check if "dev" is present in the entry
    if 'dev' in entry and entry['dev']:
        # If "dev" is present and not empty, flatten it
        flattened_entry = {
            "id": entry["id"],
            "name": entry["name"],
            "citycode": entry["citycode"],
            "city": entry["city"],
            "type": entry["type"],
            "status": entry["status"],
            "main": entry["main"],
            "lat": entry["lat"],
            "long": entry["long"],
            "cluster_ica_data": entry["cluster_ica_data"],
            "highest": entry["highest"],
            "highest_ica": entry["highest_ica"],
            "ica": entry["ica"],
            "max_value": entry["max_value"],
            "lastReadingTime": entry["lastReadingTime"]
        }

        # Add flattened "dev" data
        flattened_entry.update(entry["dev"][0])
 
        # Flatten the "highest" field
        highest_data = entry.get("highest", {})
        flattened_entry.update({"highest_" + k: v for k, v in highest_data.items()})

        

        flattened_data.append(flattened_entry)
    else:
        # If "dev" is not present or empty, add the entry without flattening
        flattened_data.append(entry)

# Create a DataFrame from the flattened data
df = pd.DataFrame(flattened_data)

# Save the DataFrame to a CSV file

df.to_csv(targetRoot + '.csv', index=False)