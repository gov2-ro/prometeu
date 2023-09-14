import requests
import pandas as pd

 
 
url = 'https://infoaer.pmb.ro/api/infosensors'
headers = {
    'Accept': '*/*',
    'Accept-Language': 'en-GB,en;q=0.9',
    'Cache-Control': 'max-age=0',
    'Content-Type': 'application/json',
    'Cookie': '_pk_id.12.966e=83108e0438fdfc70.1694698128.; _pk_ref.12.966e=%5B%22%22%2C%22%22%2C1694706379%2C%22https%3A%2F%2Fwww.google.com%2F%22%5D; _pk_ses.12.966e=1; XSRF-TOKEN=eyJpdiI6IkllcWVaRWU1bG1JUytpbUlCYjlOaGc9PSIsInZhbHVlIjoiZlQyRDBkWThCQWk0RnNxUGVPS3lrNmFDMVpsNkhQTW9YblFSUDVFeTkwZHovZnN3M3NRR3gvTDRZVE0rOTFxWUp5Z2RGN0VadHYySERlOXVqNDFxbFFFQTN4Snp5Umc0bzB2TW1acjE3V0RTTExuTjBoZWxJcjk5dGgxVXFoTHEiLCJtYWMiOiI0MTViMzZkN2FmZjg0Mzg3YzA4NzYyZmQzOGM3MDI0ZjBkNzA2MjI0ZGEwNjRkMzRkMDlmOTU3ZmE1NTcyN2RmMjIzNGYwNzg0YTU1NzYxODkxOWViNiIsInRhZyI6IiJ9; pmbprimaria_municipiului_bucuresti_session=eyJpdiI6Ik9XZkFqT0FwZXRKd3VQSTRmcjkxRnc9PSIsInZhbHVlIjoiMDY2R1JpQ1ZxdEsyeG1ZYXFLTW5Gdmx1T3lvM2o0M09LbHdscDhvUmJCV09iKzU1T2UwMmN2dGpEYXAyOXF4ZS84eHhDMWpZS0tCMG8veXY0STg0TzVrWjl5SlRndnQyKzVTbEZDbDcwMWthYzVGNEw4dHYzNkw0eVl3aGhWOHIiLCJtYWMiOiI5YWU4MmE0NWE5NzgzYjU0OGFhYjEyZTQ5NjIyZTVlZjEyYmE2OWRjMzc0ZGY0ODUwMzFmMDFlZmMxY2FlZjkxIiwidGFnIjoiIn0%3D',
    'Origin': 'https://infoaer.pmb.ro',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-GPC': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Brave";v="116"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': 'macOS',
}

# Define the request payload
payload = {
    'sensor_node': None,
}

# Send the POST request
response = requests.post(url, headers=headers, json=payload)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Parse the JSON response
    response_json = response.json()
    
    # Do something with the JSON data
    # print(response_json)
else:
    print(f"Request failed with status code {response.status_code}")
    exit()

data_list = []
for item in response_json["data"]:
    desc = item["Desc"][0]  # Extract the first element of the "Desc" list
    item_dict = {
        "Lon": item["Lon"],
        "Lat": item["Lat"],
        "Icon": item["Icon"],
        "name": desc["name"],
        "link": desc["link"],
        "code": desc["code"],
        "indice": desc["indice"],
        "hum": desc["hum"],
        "temp": desc["temp"],
    }
    data_list.append(item_dict)

df = pd.DataFrame(data_list)

# Save the DataFrame as a CSV file
df.to_csv("flattened_data.csv", index=False)