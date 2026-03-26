import pandas as pd
import numpy as np

source_file='../data/interventii-urs/Interventii Urs.csv'
target_file='../data/interventii-urs/normalized_interventii_urs.csv'
summary_file='../data/interventii-urs/summary_by_county_event.csv'


# Load the CSV file
df = pd.read_csv(source_file, encoding='utf-8', low_memory=False)

# Define Romania's approximate bounding box (min_lat, max_lat, min_long, max_long)
ROMANIA_BOUNDS = (43.6, 48.3, 20.2, 29.7)

def clean_and_convert_coordinate(coord_str):
    """
    Cleans coordinate string by replacing comma with dot and converts to float.
    Returns None if conversion fails.
    """
    if pd.isna(coord_str) or coord_str == "" or coord_str == "-":
        return None
    try:
        # Convert to string to ensure .replace() works, then replace comma with dot
        cleaned_coord = str(coord_str).replace(',', '.').strip()
        # Handle empty strings after cleaning
        if cleaned_coord == "" or cleaned_coord == "-":
            return None
        return float(cleaned_coord)
    except (ValueError, TypeError):
        return None

def validate_and_correct_coordinates(lat, long):
    """
    Validates coordinates against Romania bounds and corrects if inverted.
    Returns corrected (lat, long) and a status string.
    """
    log_messages = []

    # Check if lat or long are None
    if lat is None and long is None:
        return None, None, "No coordinates found"
    if lat is None or long is None:
        return None, None, "Invalid coordinate format"

    # Check for obvious projection coordinates (too large values)
    if abs(lat) > 90 or abs(long) > 180:
        if lat > 1000 or long > 1000:
            log_messages.append("Projection coordinates detected")
            return lat, long, "; ".join(log_messages)

    # Check if coordinates need swapping - more robust logic
    lat_in_romania = ROMANIA_BOUNDS[0] <= lat <= ROMANIA_BOUNDS[1]
    long_in_romania = ROMANIA_BOUNDS[2] <= long <= ROMANIA_BOUNDS[3]
    
    # If current assignment is wrong but swapping would fix it
    if not lat_in_romania and not long_in_romania:
        # Try swapping
        lat_swap_valid = ROMANIA_BOUNDS[0] <= long <= ROMANIA_BOUNDS[1]
        long_swap_valid = ROMANIA_BOUNDS[2] <= lat <= ROMANIA_BOUNDS[3]
        
        if lat_swap_valid and long_swap_valid:
            lat, long = long, lat
            log_messages.append("Coordinates swapped")
            lat_in_romania = True
            long_in_romania = True

    # Final validation
    if not (lat_in_romania and long_in_romania):
        log_messages.append("Coordinates outside Romania")

    return lat, long, "; ".join(log_messages) if log_messages else "OK"

def clean_string_field(value):
    """Clean string fields, handle NaN and empty values"""
    if pd.isna(value) or value == "" or value == "-":
        return None
    return str(value).strip()

# Initialize a list to store normalized records
normalized_records = []

# Define event types and their corresponding column prefixes
event_types = {
    'alungare': {
        'lat_col': 'Coordonate interventie alungare Y (WGS84, grade zecimale)',
        'long_col': 'Coordonate interventie alungare X (WGS84, grade zecimale)',
        'fc_col': 'FC interventie alungare',
        'data_col': 'Data interventie alungare',
        'raport_col': 'Nr. raport interventie alungare'
    },
    'relocare': {
        'lat_col': 'Coordonate relocare Y (WGS84, grade zecimale)',
        'long_col': 'Coordonate relocare X (WGS84, grade zecimale)',
        'fc_col': 'FC interventie relocare',
        'data_col': 'Data relocare',
        'raport_col': 'Nr. raport interventie relocare'
    },
    'eutanasiere': {
        'lat_col': 'Coordonate eutanasiere Y (WGS84, grade zecimale)',
        'long_col': 'Coordonate eutanasiere X (WGS84, grade zecimale)',
        'fc_col': 'FC interventie eutanasiere',
        'data_col': 'Data interventie eutanasiere',
        'raport_col': 'Nr. raport interventie eutanasiere'
    },
    'impuscare': {
        'lat_col': 'Coordonate impuscare Y (WGS84, grade zecimale)',
        'long_col': 'Coordonate impuscare X (WGS84, grade zecimale)',
        'fc_col': 'FC interventie impuscare',
        'data_col': 'Data interventie impuscare',
        'raport_col': 'Nr. raport interventie impuscare'
    }
}

# Columns to preserve as-is (non-intervention specific)
preserve_columns = [
    'Judet', 'UAT', 'Echipa de interventie', 'Sex', 
    'Detalii referitoare la eveniment', 'Metoda de interventie', 'Adaugat de'
]

# Iterate over each row of the original DataFrame
for index, row in df.iterrows():
    row_has_data = False  # Track if this row has any intervention data
    
    for event_type, cols in event_types.items():
        # Get the raw coordinate values (note: X=longitude, Y=latitude in the source)
        original_lat_val = row.get(cols['lat_col'])  # Y column = latitude
        original_long_val = row.get(cols['long_col'])  # X column = longitude

        # Clean and convert coordinates
        lat = clean_and_convert_coordinate(original_lat_val)
        long = clean_and_convert_coordinate(original_long_val)

        # Check if this event type has any meaningful data
        has_event_specific_data = any([
            lat is not None, 
            long is not None, 
            clean_string_field(row.get(cols['fc_col'])) is not None,
            row.get(cols['data_col']) is not None and str(row.get(cols['data_col'])).strip() not in ["", "-"],
            clean_string_field(row.get(cols['raport_col'])) is not None
        ])

        if has_event_specific_data:
            row_has_data = True
            lat, long, status_log = validate_and_correct_coordinates(lat, long)
            
            # Handle Data column
            original_data_val = row.get(cols['data_col'])
            parsed_date = pd.to_datetime(original_data_val, errors='coerce', dayfirst=True)
            date_str = parsed_date.strftime('%Y-%m-%d') if pd.notna(parsed_date) else None
            if pd.isna(parsed_date) and pd.notna(original_data_val) and str(original_data_val).strip() not in ["", "-"]:
                status_log = status_log + "; Invalid Date Format" if status_log else "Invalid Date Format"

            # Handle FC and Nr. raport
            fc_val = clean_string_field(row.get(cols['fc_col']))
            raport_val = clean_string_field(row.get(cols['raport_col']))

            # Get identification number based on event type
            identificare_val = None
            if event_type == 'relocare':
                identificare_val = clean_string_field(row.get('Nr. identificare relocare (nr. colar sau crotaliu)'))
            elif event_type == 'eutanasiere':
                identificare_val = clean_string_field(row.get('Nr. identificare eutanasiere (nr. colar sau crotaliu)'))
            elif event_type == 'impuscare':
                identificare_val = clean_string_field(row.get('Nr. identificare impuscare (nr. colar sau crotaliu)'))

            # Create the normalized record
            record = {
                'original_row_index': index,
                'event_type': event_type,
                'lat': lat,
                'long': long,
                'FC': fc_val,
                'Data': date_str,
                'Nr_raport': raport_val,
                'Nr_identificare': identificare_val,
                'status_log': status_log
            }
            
            # Add preserved columns
            for col in preserve_columns:
                if col in row.index:
                    record[col] = clean_string_field(row[col])
            
            # Add relocation specific county field
            if event_type == 'relocare':
                record['Judet_relocare'] = clean_string_field(row.get('Judet relocare'))
            
            normalized_records.append(record)
    
    # If no specific event type had data, but the row has some general data, create an "altele" record
    if not row_has_data:
        # Check if row has any general information worth preserving
        has_general_data = any([
            clean_string_field(row.get('Judet')) is not None,
            clean_string_field(row.get('UAT')) is not None,
            clean_string_field(row.get('Echipa de interventie')) is not None,
            clean_string_field(row.get('Sex')) is not None,
            clean_string_field(row.get('Detalii referitoare la eveniment')) is not None,
            clean_string_field(row.get('Metoda de interventie')) is not None
        ])
        
        if has_general_data:
            # Create an "altele" record with available general information
            record = {
                'original_row_index': index,
                'event_type': 'altele',
                'lat': None,
                'long': None,
                'FC': None,
                'Data': None,
                'Nr_raport': None,
                'Nr_identificare': None,
                'status_log': 'No specific intervention data found'
            }
            
            # Add preserved columns
            for col in preserve_columns:
                if col in row.index:
                    record[col] = clean_string_field(row[col])
            
            normalized_records.append(record)

# Create the new normalized DataFrame
normalized_df = pd.DataFrame(normalized_records)

# Remove rows where all key fields are null (no useful data)
normalized_df = normalized_df.dropna(subset=['lat', 'long', 'FC', 'Data', 'Nr_raport'], how='all')

# Sort by original row index and event type for better readability
normalized_df = normalized_df.sort_values(['original_row_index', 'event_type']).reset_index(drop=True)

# Display statistics
print(f"Original rows: {len(df)}")
print(f"Normalized records: {len(normalized_df)}")
print(f"Records by event type:")
print(normalized_df['event_type'].value_counts())
print(f"\nStatus log summary:")
print(normalized_df['status_log'].value_counts())

# Display the first 10 rows of the normalized DataFrame
print(f"\nFirst 10 rows:")
print(normalized_df[['original_row_index', 'event_type', 'lat', 'long', 'FC', 'Data', 'Judet', 'UAT', 'status_log']].head(10).to_markdown(index=False, numalign="left", stralign="left"))

# Display info about the normalized DataFrame
print(f"\nDataFrame info:")
print(normalized_df.info())

# Save the normalized DataFrame to a new CSV file
normalized_df.to_csv(target_file, index=False)
print(f"\nSaved to: normalized_interventii_urs_improved.csv")

# Create a summary report
summary_df = normalized_df.groupby(['Judet', 'event_type']).size().unstack(fill_value=0)
summary_df.to_csv(summary_file)
print(f"Summary by county and event type saved to: summary_by_county_event.csv")