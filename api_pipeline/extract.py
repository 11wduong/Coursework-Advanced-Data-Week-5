"""Plant Data Extraction Script this script extracts plant data from the LNHM plant API."""

import requests
import pandas as pd


def fetch_plant_data(plant_id) -> dict:
    """Fetch plant data from the API for a given plant ID."""
    url = f"https://tools.sigmalabs.co.uk/api/plants/{plant_id}"

    response = requests.get(url)
    data = response.json()

    if 'error' in data:
        print(f"Error fetching plant ID {plant_id}: {data['error']}")
        raise ValueError(f"API error for plant ID {plant_id}")

    return data


def flatten_plant_data(plant_data) -> dict:
    """Flatten nested dictionary structure for DataFrame."""
    if not plant_data:
        print("No plant data to flatten")
        raise ValueError("No plant data provided")

    botanist = plant_data.get('botanist', {})
    origin = plant_data.get('origin_location', {})

    return {
        'plant_id': plant_data.get('plant_id'),
        'common_name': plant_data.get('name'),
        'scientific_name': plant_data.get('scientific_name', []),
        'moisture': plant_data.get('soil_moisture'),
        'temperature': plant_data.get('temperature'),
        'last_watered': plant_data.get('last_watered'),
        'recording_taken': plant_data.get('recording_taken'),
        'botanist_name': botanist.get('name'),
        'email': botanist.get('email'),
        'phone': botanist.get('phone'),
        'city': origin.get('city'),
        'country': origin.get('country'),
        'lat': origin.get('latitude'),
        'long': origin.get('longitude'),
    }


def extract_all_plants(start_id=1, max_consecutive_errors=5) -> pd.DataFrame:
    """Extract plant data starting from start_id until max_consecutive_errors reached."""
    all_plants = []
    consecutive_errors = 0
    plant_id = start_id

    while consecutive_errors < max_consecutive_errors:
        try:
            plant_data = fetch_plant_data(plant_id)
            flat_data = flatten_plant_data(plant_data)
            all_plants.append(flat_data)
            consecutive_errors = 0
        except ValueError:
            consecutive_errors += 1

        plant_id += 1

    print(
        f"Stopped after {consecutive_errors} consecutive errors at plant_id {plant_id - consecutive_errors}")
    return pd.DataFrame(all_plants)


if __name__ == "__main__":
    df = extract_all_plants(start_id=1)
    print(f"Extracted {len(df)} plants")
    print(df.head())
