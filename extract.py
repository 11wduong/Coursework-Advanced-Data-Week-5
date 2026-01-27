"""Plant Data Extraction Script this script extracts plant data from the LNHM plant API."""

import requests
import pandas as pd


def fetch_plant_data(plant_id):
    """Fetch plant data from the API for a given plant ID."""
    url = f"https://tools.sigmalabs.co.uk/api/plants/{plant_id}"

    response = requests.get(url)
    data = response.json()

    if 'error' in data:
        print(f"Error fetching plant ID {plant_id}: {data['error']}")
        return None

    return data


def flatten_plant_data(plant_data):
    """Flatten nested dictionary structure for DataFrame."""
    if not plant_data:
        return None

    botanist = plant_data.get('botanist', {})
    origin = plant_data.get('origin_location', {})

    return {
        'plant_id': plant_data.get('plant_id'),
        'common_name': plant_data.get('name'),
        'scientific_name': plant_data.get('scientific_name', []),
        'soil_moisture': plant_data.get('soil_moisture'),
        'temperature': plant_data.get('temperature'),
        'last_watered': plant_data.get('last_watered'),
        'recording_taken': plant_data.get('recording_taken'),
        'botanist_name': botanist.get('name'),
        'botanist_email': botanist.get('email'),
        'botanist_phone': botanist.get('phone'),
        'origin_city': origin.get('city'),
        'origin_country': origin.get('country'),
        'origin_latitude': origin.get('latitude'),
        'origin_longitude': origin.get('longitude'),
    }


def extract_all_plants(start_id=1, end_id=50):
    """Extract plant data for a range of plant IDs and return as DataFrame."""
    all_plants = []

    for plant_id in range(start_id, end_id + 1):
        plant_data = fetch_plant_data(plant_id)
        if plant_data:
            flat_data = flatten_plant_data(plant_data)
            if flat_data:
                all_plants.append(flat_data)

    return pd.DataFrame(all_plants)


if __name__ == "__main__":
    df = extract_all_plants(1, 50)
    print(f"Extracted {len(df)} plants")
    print(df.head())
