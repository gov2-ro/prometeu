"""
Scraper for bear intervention incidents in Romania
Source: https://interventiiurs.mmap.ro/centralizator/

This scraper extracts data about bear interventions including:
- Location details (county, locality)
- Intervention team composition  
- GPS coordinates
- Incident details and outcomes
- Bear characteristics (gender, age estimates)
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
from datetime import datetime
from utils.common import save_json_to_file, data_root

# Configuration
url = 'https://interventiiurs.mmap.ro/centralizator/'
data_folder = data_root + 'interventii-urs/'
output_file_root = 'interventii-urs'

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def clean_text(text):
    """Clean and normalize text data"""
    if text is None or text == '' or str(text).strip() == '':
        return None
    try:
        return str(text).strip().replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    except Exception as e:
        # print(f"Error cleaning text: {e}")  # Suppress error messages
        return None

def parse_coordinates(coord_text):
    """Parse coordinate text to float, handle various formats"""
    if not coord_text:
        return None
    
    # Clean the text
    coord_text = str(coord_text).strip()
    if coord_text == '' or coord_text == 'None':
        return None
        
    try:
        # Handle comma as decimal separator
        coord_text = coord_text.replace(',', '.')
        return float(coord_text)
    except (ValueError, TypeError):
        return None

def parse_date(date_text):
    """Parse date text to standardized format"""
    if not date_text:
        return None
        
    date_text = str(date_text).strip()
    if date_text == '' or date_text == 'None':
        return None
        
    try:
        # Try parsing DD-MM-YYYY format
        if '-' in date_text:
            parts = date_text.split('-')
            if len(parts) == 3:
                day, month, year = parts
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        return date_text
    except:
        return date_text

def infer_county_from_uat(uat_name):
    """Infer county from UAT (locality) name using common mappings"""
    if not uat_name:
        return None
        
    uat = uat_name.upper().strip()
    
    # Common UAT to county mappings for bear intervention areas
    uat_county_map = {
        # Harghita county
        'VOŞLĂBENI': 'Harghita', 'VOSLOBENI': 'Harghita', 'BĂLAN': 'Harghita', 'BALAN': 'Harghita',
        'BILBOR': 'Harghita', 'SÂNDOMINIC': 'Harghita', 'SANDOMINIC': 'Harghita', 'CORBU': 'Harghita',
        'BORSEC': 'Harghita', 'COZMENI': 'Harghita', 'ZETEA': 'Harghita', 'GHEORGHENI': 'Harghita',
        'TOPLIŢA': 'Harghita', 'TOPLITA': 'Harghita', 'PRAID': 'Harghita',
        
        # Prahova county  
        'COMARNIC': 'Prahova', 'CERAŞU': 'Prahova', 'CERASU': 'Prahova', 'DRAJNA': 'Prahova',
        'POSEŞTI': 'Prahova', 'POSESTI': 'Prahova', 'SINAIA': 'Prahova', 'BUŞTENI': 'Prahova',
        'BUSTENI': 'Prahova', 'BREAZA': 'Prahova', 'CÂMPINA': 'Prahova', 'CAMPINA': 'Prahova',
        'MĂNECIU': 'Prahova', 'MANECIU': 'Prahova', 'ŞTEFEŞTI': 'Prahova', 'STEFESTI': 'Prahova',
        'AZUGA': 'Prahova', 'IZVOARELE': 'Prahova', 'SLĂNIC': 'Prahova', 'SLANIC': 'Prahova',
        'PĂULEŞTI': 'Prahova', 'PAULESTI': 'Prahova', 'BĂTRÂNI': 'Prahova', 'BATRANI': 'Prahova',
        'VĂLENII DE MUNTE': 'Prahova', 'PROVIŢA DE SUS': 'Prahova', 'PROVITA DE SUS': 'Prahova',
        'ARICEŞTII ZELETIN': 'Prahova', 'ARICESTII ZELETIN': 'Prahova', 'CĂRBUNEŞTI': 'Prahova',
        'CARBUNESTI': 'Prahova', 'SURANI': 'Prahova', 'ALUNIŞ': 'Prahova', 'ALUNIS': 'Prahova',
        'DUMBRĂVEŞTI': 'Prahova', 'DUMBRAVESTI': 'Prahova', 'TEIŞANI': 'Prahova', 'TEISANI': 'Prahova',
        'BĂNEŞTI': 'Prahova', 'BANESTI': 'Prahova', 'VÂLCĂNEŞTI': 'Prahova', 'VALCANESTI': 'Prahova',
        'PLOIEŞTI': 'Prahova', 'PLOIESTI': 'Prahova',
        
        # Brașov county
        'BRAŞOV': 'Brașov', 'BRASOV': 'Brașov', 'PREDEAL': 'Brașov', 'RÂŞNOV': 'Brașov', 'RASNOV': 'Brașov',
        'ZĂRNEŞTI': 'Brașov', 'ZARNESTI': 'Brașov', 'SĂCELE': 'Brașov', 'SACELE': 'Brașov',
        'BRAN': 'Brașov', 'FUNDATA': 'Brașov',
        
        # Mureș county
        'SOVATA': 'Mureș', 'BEICA DE JOS': 'Mureș', 'SOLOVĂSTRU': 'Mureș', 'SOLOVASTRU': 'Mureș',
        'CORUNCA': 'Mureș', 'LIVEZENI': 'Mureș', 'ACĂŢARI': 'Mureș', 'ACATARI': 'Mureș',
        'COROISÂNMĂRTIN': 'Mureș', 'COROISANMARTIN': 'Mureș', 'PETELEA': 'Mureș',
        'IBĂNEŞTI': 'Mureș', 'IBANESTI': 'Mureș', 'STÂNCENI': 'Mureș', 'STANCENI': 'Mureș',
        'SÂNPAUL': 'Mureș', 'SANPAUL': 'Mureș', 'TÂRGU MUREŞ': 'Mureș', 'TARGU MURES': 'Mureș',
        'RĂSTOLIŢA': 'Mureș', 'RASTOLITA': 'Mureș', 'SIGHIŞOARA': 'Mureș', 'SIGHISOARA': 'Mureș',
        
        # Covasna county
        'BARCANI': 'Covasna', 'MICFALĂU': 'Covasna', 'MICFALAU': 'Covasna', 'ZĂBALA': 'Covasna', 'ZABALA': 'Covasna',
        
        # Vrancea county
        'CÂMPURI': 'Vrancea', 'CAMPURI': 'Vrancea', 'REGHIU': 'Vrancea', 'NEREJU': 'Vrancea',
        'BORDEŞTI': 'Vrancea', 'BORDESTI': 'Vrancea', 'SOVEJA': 'Vrancea', 'JITIA': 'Vrancea',
        
        # Other counties
        'MOROENI': 'Dâmbovița', 'PIETROŞIŢA': 'Dâmbovița', 'PIETROSITA': 'Dâmbovița',
        'BIXAD': 'Covasna', 'BROŞTENI': 'Suceava', 'BROSTENI': 'Suceava', 'VATRA DORNEI': 'Suceava',
        'LEREŞTI': 'Argeș', 'LERESTI': 'Argeș', 'AREFU': 'Argeș', 'NUCŞOARA': 'Argeș', 'NUCSOARA': 'Argeș',
        'CORBENI': 'Argeș', 'RUCĂR': 'Argeș', 'RUCAR': 'Argeș',
        'PORUMBACU DE JOS': 'Sibiu', 'DUMBRĂVENI': 'Sibiu', 'DUMBRAVENI': 'Sibiu',
        'SEBEŞ': 'Alba', 'SEBES': 'Alba', 'CÂMPENI': 'Alba', 'CAMPENI': 'Alba', 'VALEA LUNGĂ': 'Alba', 'VALEA LUNGA': 'Alba',
        'ŞIEU': 'Bistrița-Năsăud', 'SIEU': 'Bistrița-Năsăud',
        'PUI': 'Hunedoara', 'BUMBEŞTI-JIU': 'Gorj', 'BUMBESTI-JIU': 'Gorj',
        'PIETROASA': 'Bihor', 'PALANCA': 'Bacău', 'AGĂŞ': 'Bacău', 'AGAS': 'Bacău',
        'RĂCĂCIUNI': 'Bacău', 'RACACIUNI': 'Bacău', 'SLĂNIC-MOLDOVA': 'Bacău', 'SLANIC-MOLDOVA': 'Bacău',
        'CĂIUŢI': 'Bacău', 'CAIUTI': 'Bacău', 'ASĂU': 'Bacău', 'ASAU': 'Bacău', 'GURA VĂII': 'Bacău', 'GURA VAII': 'Bacău',
        'MEREI': 'Buzău', 'PĂTÂRLAGELE': 'Buzău', 'PATARLAGELE': 'Buzău', 'NEHOIU': 'Buzău',
        'BECENI': 'Buzău', 'TOPLICENI': 'Buzău',
    }
    
    return uat_county_map.get(uat)

def standardize_intervention_type(intervention_text):
    """Standardize intervention type categories"""
    if not intervention_text:
        return None
        
    intervention_text = intervention_text.strip().lower()
    
    # Map various Romanian terms to standard categories
    if 'alungat' in intervention_text:
        return 'Alungat'
    elif 'relocat' in intervention_text:
        return 'Relocat'  
    elif 'împușcare' in intervention_text or 'impuscare' in intervention_text:
        return 'Împușcare'
    elif 'eutanasiat' in intervention_text:
        return 'Eutanasiat'
    elif 'capturat' in intervention_text:
        return 'Capturat'
    elif 'altele' in intervention_text:
        return 'Altele'
    else:
        return intervention_text.title()

def scrape_bear_interventions():
    """Main scraping function"""
    print(f"Fetching data from {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        if response.status_code != 200:
            print(f"Failed to fetch data. HTTP Error {response.status_code}")
            return None
            
        print(f"Successfully fetched data. Content length: {len(response.text)}")
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the main data table - look for table with intervention data
        tables = soup.find_all('table')
        
        if not tables:
            print("No tables found on the page")
            return None
            
        print(f"Found {len(tables)} table(s)")
        
        # Look for the main data table (usually the largest one)
        main_table = None
        max_rows = 0
        
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) > max_rows:
                max_rows = len(rows)
                main_table = table
                
        if not main_table:
            print("Could not identify main data table")
            return None
            
        print(f"Using table with {max_rows} rows")
        
        # Extract headers from the first row
        header_row = main_table.find('tr')
        if not header_row:
            print("Could not find header row")
            return None
            
        headers_cells = header_row.find_all(['th', 'td'])
        table_headers = [clean_text(cell.get_text()) for cell in headers_cells]
        
        print(f"Found headers: {table_headers[:5]}...")  # Print first 5 headers
        
        # Extract data rows
        data_rows = main_table.find_all('tr')[1:]  # Skip header row
        interventions = []
        
        print(f"Processing {len(data_rows)} data rows...")
        
        for i, row in enumerate(data_rows):
            cells = row.find_all(['td', 'th'])
            
            if len(cells) < len(table_headers):
                continue  # Skip incomplete rows
                
            row_data = {}
            
            for j, cell in enumerate(cells[:len(table_headers)]):
                if j < len(table_headers):
                    cell_text = clean_text(cell.get_text())
                    header = table_headers[j] if j < len(table_headers) else f"col_{j}"
                    row_data[header] = cell_text
            
            # Process and clean the data
            processed_row = process_intervention_row(row_data)
            if processed_row:
                interventions.append(processed_row)
                
            if (i + 1) % 100 == 0:
                print(f"Processed {i + 1} rows...")
        
        print(f"Successfully processed {len(interventions)} intervention records")
        return interventions
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def process_intervention_row(row_data):
    """Process and clean a single intervention row"""
    try:
        # Create a clean row with standardized field names
        cleaned_row = {}
        
        # Map the fields based on typical column structure
        for key, value in row_data.items():
            if not key:
                continue
                
            key_lower = key.lower() if key else ''
            
            # Map common field names
            if 'județ' in key_lower or 'judet' in key_lower or key_lower == 'judet':
                cleaned_row['judet'] = clean_text(value)
            elif key == 'UAT':
                cleaned_row['uat'] = clean_text(value)
            elif 'echip' in key_lower or 'membru' in key_lower:
                cleaned_row['echipa_interventie'] = clean_text(value)
            elif 'fc interventie alungare' in key_lower:
                cleaned_row['fond_cinegetic_alungare'] = clean_text(value)
            elif 'data' in key_lower and 'interven' in key_lower:
                cleaned_row['data_interventie'] = parse_date(value)
            elif 'coordonate interventie alungare x' in key_lower:
                cleaned_row['longitudine_alungare'] = parse_coordinates(value)
            elif 'coordonate interventie alungare y' in key_lower:
                cleaned_row['latitudine_alungare'] = parse_coordinates(value)
            elif 'coordonate relocare x' in key_lower:
                cleaned_row['longitudine_relocare'] = parse_coordinates(value)
            elif 'coordonate relocare y' in key_lower:
                cleaned_row['latitudine_relocare'] = parse_coordinates(value)
            elif 'coordonate impuscare x' in key_lower:
                cleaned_row['longitudine_impuscare'] = parse_coordinates(value)
            elif 'coordonate impuscare y' in key_lower:
                cleaned_row['latitudine_impuscare'] = parse_coordinates(value)
            elif 'coordonate eutanasiere x' in key_lower:
                cleaned_row['longitudine_eutanasiere'] = parse_coordinates(value)
            elif 'coordonate eutanasiere y' in key_lower:
                cleaned_row['latitudine_eutanasiere'] = parse_coordinates(value)
            elif 'raport' in key_lower and 'alungare' in key_lower:
                cleaned_row['numar_raport_alungare'] = clean_text(value)
            elif 'raport' in key_lower and 'relocare' in key_lower:
                cleaned_row['numar_raport_relocare'] = clean_text(value)
            elif 'sex' in key_lower or 'gen' in key_lower:
                cleaned_row['sex_urs'] = clean_text(value)
            elif 'detalii' in key_lower or 'eveniment' in key_lower:
                cleaned_row['descriere_eveniment'] = clean_text(value)
            elif 'metoda' in key_lower and 'interv' in key_lower:
                cleaned_row['metoda_interventie'] = standardize_intervention_type(value)
            elif 'adaugat' in key_lower or 'responsabil' in key_lower:
                cleaned_row['adaugat_de'] = clean_text(value)
            elif 'identificare relocare' in key_lower:
                cleaned_row['identificare_relocare'] = clean_text(value)
            elif 'identificare impuscare' in key_lower:
                cleaned_row['identificare_impuscare'] = clean_text(value)
            elif 'identificare eutanasiere' in key_lower:
                cleaned_row['identificare_eutanasiere'] = clean_text(value)
            elif 'fc interventie relocare' in key_lower:
                cleaned_row['fond_cinegetic_relocare'] = clean_text(value)
            elif 'fc interventie impuscare' in key_lower:
                cleaned_row['fond_cinegetic_impuscare'] = clean_text(value)
            elif 'fc interventie eutanasiere' in key_lower:
                cleaned_row['fond_cinegetic_eutanasiere'] = clean_text(value)
            else:
                # Keep original field name if we can't map it
                cleaned_key = key.replace(' ', '_').replace('(', '').replace(')', '').replace(',', '').lower()
                cleaned_row[cleaned_key] = clean_text(value)
        
        # Ensure we have at least basic required fields
        if not cleaned_row.get('judet') and not cleaned_row.get('uat'):
            return None
            
        # Try to infer missing county from UAT if county is empty but UAT exists
        if not cleaned_row.get('judet') and cleaned_row.get('uat'):
            inferred_county = infer_county_from_uat(cleaned_row['uat'])
            if inferred_county:
                cleaned_row['judet'] = inferred_county
                
        return cleaned_row
        
    except Exception as e:
        print(f"Error processing row: {e}")
        return None

def save_data(interventions):
    """Save data to JSON and CSV files"""
    import os
    
    # Create data directory if it doesn't exist
    os.makedirs(data_folder, exist_ok=True)
    
    if not interventions:
        print("No data to save")
        return
    
    # Save as JSON
    json_file = f"{data_folder}{output_file_root}.json"
    save_json_to_file(interventions, json_file, 'compact')
    
    # Save as CSV
    csv_file = f"{data_folder}{output_file_root}.csv"
    df = pd.DataFrame(interventions)
    df.to_csv(csv_file, encoding='utf-8', index=False)
    
    print(f"Data saved to:")
    print(f"  JSON: {json_file}")
    print(f"  CSV: {csv_file}")
    print(f"  Records: {len(interventions)}")

def main():
    """Main execution function"""
    print("Starting bear interventions scraper...")
    print(f"Source: {url}")
    print(f"Output folder: {data_folder}")
    
    # Scrape the data
    interventions = scrape_bear_interventions()
    
    if interventions:
        # Save the data
        save_data(interventions)
        
        # Print summary statistics
        print("\n--- Summary ---")
        df = pd.DataFrame(interventions)
        
        if 'judet' in df.columns:
            print(f"Counties covered: {df['judet'].nunique()}")
            top_counties = df['judet'].value_counts().head(5)
            print("Top 5 counties by interventions:")
            for county, count in top_counties.items():
                print(f"  {county}: {count}")
        
        if 'metoda_interventie' in df.columns:
            print("\nIntervention methods:")
            intervention_types = df['metoda_interventie'].value_counts()
            for int_type, count in intervention_types.items():
                print(f"  {int_type}: {count}")
        
        # Check coordinate data quality for different intervention types
        alungare_coords = 0
        relocare_coords = 0
        impuscare_coords = 0
        
        if 'latitudine_alungare' in df.columns and 'longitudine_alungare' in df.columns:
            alungare_coords = (df['latitudine_alungare'].notna() & df['longitudine_alungare'].notna()).sum()
            
        if 'latitudine_relocare' in df.columns and 'longitudine_relocare' in df.columns:
            relocare_coords = (df['latitudine_relocare'].notna() & df['longitudine_relocare'].notna()).sum()
            
        if 'latitudine_impuscare' in df.columns and 'longitudine_impuscare' in df.columns:
            impuscare_coords = (df['latitudine_impuscare'].notna() & df['longitudine_impuscare'].notna()).sum()
        
        print(f"\nCoordinate data:")
        print(f"  Alungare interventions with coordinates: {alungare_coords}")
        print(f"  Relocare interventions with coordinates: {relocare_coords}")
        print(f"  Impușcare interventions with coordinates: {impuscare_coords}")
        
    else:
        print("Failed to scrape data")

if __name__ == "__main__":
    main()
