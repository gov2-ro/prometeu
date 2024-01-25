data_root = 'data/stare-partii/'

import requests
from bs4 import BeautifulSoup
import pandas as pd

def extract_table_data(soup, section_id, update_date):
    section = soup.find('section', id=section_id)
    if not section:
        return None

    table = section.find('table')
    if not table:
        return None

    headers = [th.get_text(strip=True) for th in table.find_all('th')]
    rows = []
    for tr in table.find_all('tr'):
        row = [td.get_text(strip=True) for td in tr.find_all('td')]
        if row:
            # Special handling for 'instalatii transport' table
            if section_id == 'instalatii-transport':
                img = tr.find('img')
                if img and img.has_attr('alt'):
                    row[1] = img['alt']  # Replace Funcțional data with ALT attribute
            rows.append(row + [update_date])  # Add update date to each row

    headers.append('Data actualizării')  # Add update date column header
    return pd.DataFrame(rows, columns=headers)

def scrape_slopes_status(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    update_date = soup.find(text='Data actualizării').find_next().get_text(strip=True) if soup.find(text='Data actualizării') else None

    zona_superioara_df = extract_table_data(soup, 'zona-superioara', update_date)
    zona_inferioara_df = extract_table_data(soup, 'zona-inferioara', update_date)
    instalatii_transport_df = extract_table_data(soup, 'instalatii-transport', update_date)

    if zona_superioara_df is not None:
        zona_superioara_df.to_csv(data_root + 'bv-zona_superioara.csv', index=False)
    if zona_inferioara_df is not None:
        zona_inferioara_df.to_csv(data_root + 'bv-zona_inferioara.csv', index=False)
    if instalatii_transport_df is not None:
        instalatii_transport_df.to_csv(data_root + 'bv-instalatii_transport.csv', index=False)

    return update_date

if __name__ == "__main__":
    url = "https://starepartii.brasovcity.ro/"
    update_date = scrape_slopes_status(url)
    print("Data actualizării:", update_date)
