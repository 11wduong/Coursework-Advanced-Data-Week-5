"""Transform script"""

import pandas as pd


def combine_tables(country_df: pd.DataFrame, botanist_df: pd.DataFrame,
                   location_df: pd.DataFrame, plant_df: pd.DataFrame,
                   record_df: pd.DataFrame) -> pd.DataFrame:
    """Combines all the tables into a single dataframe for easier export or analysis."""
    df = record_df.merge(plant_df, on='plant_id', how='left')
    df = df.merge(location_df, on='location_id', how='left')
    df = df.merge(country_df, on='country_id', how='left')
    df = df.merge(botanist_df, on='botanist_id', how='left')
    return df


def clean_table(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans the combined dataframe by removing duplicates and handling missing values."""
    df = df.drop_duplicates()
    df = df.dropna(subset=['temperature', 'moisture', 'recording_taken'])
    return df


def calculate_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates average temperature and moisture for each plant for the 24 hours and has day column to record date."""
    df['recording_taken'] = pd.to_datetime(df['recording_taken'])
    df['day'] = df['recording_taken'].dt.date

    avg_df = df.groupby(['plant_id', 'day']).agg(
        avg_temperature=('temperature', 'mean'),
        avg_moisture=('moisture', 'mean')
    ).reset_index()

    return avg_df


def create_outlier_df(df: pd.DataFrame) -> pd.DataFrame:
    """Creates a dataframe containing outlier records based on temperature and moisture thresholds based on IQR method."""


def transform_to_csv(df: pd.DataFrame, file_path: str) -> None:
    """Transforms the given DataFrame to a CSV file at the specified file path."""
    df.to_csv(file_path, index=False)
