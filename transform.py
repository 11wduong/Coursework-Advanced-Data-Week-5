"""This script transforms data pulled from the external API into data to be stored in the Microsoft SQL database."""

import pandas as pd


def create_country_table(df: pd.DataFrame) -> pd.DataFrame:
    """Pulls unique country data from extracted dataframe to a country table dataframe with country_id and country."""
    country_df = df[['country']].drop_duplicates().reset_index(drop=True)
    country_df['country_id'] = country_df.index + 1
    country_df = country_df[['country_id', 'country']]
    return country_df


def create_botanist_table(df: pd.DataFrame) -> pd.DataFrame:
    """Pull unique botanist data from extracted dataframe to a botanist table dataframe with botanist_id, botanist_name, email and phone."""
    botanist_df = df[['botanist_name', 'email', 'phone']
                     ].drop_duplicates().reset_index(drop=True)
    botanist_df['botanist_id'] = botanist_df.index + 1
    botanist_df = botanist_df[['botanist_id',
                               'botanist_name', 'email', 'phone']]
    return botanist_df


def create_location_table(df: pd.DataFrame) -> pd.DataFrame:
    """Pulls unique location data from extracted dataframe to a location table dataframe with location_id, city, lat, long, and country_id. Country_id is a foreign key referencing the country table."""
    country_df = create_country_table(df)
    location_df = df[['city', 'lat', 'long', 'country']
                     ].drop_duplicates().reset_index(drop=True)
    location_df = location_df.merge(country_df, on='country', how='left')
    location_df['location_id'] = location_df.index + 1
    location_df = location_df[['location_id',
                               'city', 'lat', 'long', 'country_id']]
    return location_df


def create_plant_table(df: pd.DataFrame) -> pd.DataFrame:
    """Pull unique plant data from extracted dataframe to a plant table dataframe with plant_id, scientific_name, common_name and location_id. Location_id is a foreign key referencing the location table."""
    # Get location data with city and country for merging
    location_df = create_location_table(df)
    location_merge = df[['city', 'country']
                        ].drop_duplicates().reset_index(drop=True)
    location_merge = location_merge.merge(
        location_df[['location_id', 'city']], on='city', how='left')

    plant_df = df[['scientific_name', 'common_name', 'city',
                   'country']].drop_duplicates().reset_index(drop=True)
    plant_df = plant_df.merge(location_merge[['city', 'country', 'location_id']], on=[
                              'city', 'country'], how='left')
    plant_df['plant_id'] = plant_df.index + 1
    plant_df = plant_df[['plant_id', 'scientific_name',
                         'common_name', 'location_id']]
    return plant_df


def create_record_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create record table dataframe with id, plant_id, recording_taken, moisture, temperature, last_watered, and botanist_id. Plant_id and botanist_id are foreign keys referencing the plant and botanist tables respectively."""
    plant_df = create_plant_table(df)
    botanist_df = create_botanist_table(df)
    record_df = df[['scientific_name', 'botanist_name', 'recording_taken',
                    'moisture', 'temperature', 'last_watered']].reset_index(drop=True)
    record_df = record_df.merge(plant_df, on='scientific_name', how='left')
    record_df = record_df.merge(botanist_df, on='botanist_name', how='left')
    record_df['id'] = record_df.index + 1
    record_df = record_df[['id', 'plant_id', 'recording_taken',
                           'moisture', 'temperature', 'last_watered', 'botanist_id']]
    return record_df
