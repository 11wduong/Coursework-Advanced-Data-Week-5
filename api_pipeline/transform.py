"""This script transforms data pulled from the external API into normalised tables."""

import pandas as pd


def _clean_list_columns(df: pd.DataFrame, columns: list = None) -> pd.DataFrame:
    """Clean specified columns by converting lists to their first element."""
    df = df.copy()
    cols_to_clean = columns if columns else [
        col for col in df.columns if df[col].dtype == 'object']

    for col in cols_to_clean:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: (x[0] if isinstance(x, list) and len(
                    x) > 0 else ('' if isinstance(x, list) else x))
            )
    return df


def create_country_table(df: pd.DataFrame) -> pd.DataFrame:
    """Pulls unique country data from extracted dataframe."""
    country_df = df[['country']].drop_duplicates().reset_index(drop=True)
    return country_df


def create_botanist_table(df: pd.DataFrame) -> pd.DataFrame:
    """Pull unique botanist data from extracted dataframe."""
    botanist_df = df[['botanist_name', 'email', 'phone']
                     ].drop_duplicates().reset_index(drop=True)
    botanist_df['phone'] = botanist_df['phone'].str[:20]
    return botanist_df


def create_location_table(df: pd.DataFrame) -> pd.DataFrame:
    """Pulls unique location data with natural key country from extracted dataframe."""
    location_df = df[['city', 'lat', 'long', 'country']
                     ].drop_duplicates().reset_index(drop=True)
    return location_df


def create_plant_table(df: pd.DataFrame) -> pd.DataFrame:
    """Pull unique plant data with plant_id from API."""
    plant_df = df[['plant_id', 'scientific_name', 'common_name', 'city']
                  ].reset_index(drop=True)
    plant_df = _clean_list_columns(plant_df, columns=['scientific_name'])
    plant_df = plant_df.drop_duplicates().reset_index(drop=True)
    return plant_df


def create_record_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create record table with plant_id from API and botanist_name for lookup."""
    record_df = df[['plant_id', 'botanist_name', 'recording_taken',
                    'moisture', 'temperature', 'last_watered']].reset_index(drop=True)
    record_df = _clean_list_columns(record_df, columns=['botanist_name'])
    return record_df
