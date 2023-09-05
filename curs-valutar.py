import requests
import xml.etree.ElementTree as ET
import csv

outfile = 'data/financiar/curs-valutar.csv'

# Define the URL of the XML data
xml_url = 'https://www.bnr.ro/nbrfxrates.xml'

# Send a GET request to the URL and get the response
response = requests.get(xml_url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the XML content with namespace
    xml_data = response.content
    root = ET.fromstring(xml_data)

    # Define the namespace
    ns = {'ns': 'http://www.bnr.ro/xsd'}

    # Extract data from the XML
    date = root.find(".//ns:Cube", namespaces=ns).attrib['date']
    rates = root.findall(".//ns:Rate", namespaces=ns)

    # Create a CSV file and write header
    csv_filename = outfile
    with open(csv_filename, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["Currency", "Rate"])

        # Write exchange rates to CSV
        for rate in rates:
            currency = rate.attrib['currency']
            rate_value = rate.text
            csv_writer.writerow([currency, rate_value])

    print(f"Exchange rates saved to {csv_filename}")
else:
    print("Failed to fetch XML data")
