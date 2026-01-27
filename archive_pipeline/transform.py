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



def extract_data (df: pd.DataFrame) -> pd.DataFrame:
    """Extracts only rows that are have anomalous data or have outliers in the temperature and soil moisture columns.
    
    Uses IQR method to identify outliers.
    """
    Q1 = df[['temperature', 'moisture']].quantile(0.25)
    Q3 = df[['temperature', 'moisture']].quantile(0.75)
    IQR = Q3 - Q1

    condition = (
        (df['temperature'] < (Q1['temperature'] - 1.5 * IQR['temperature'])) |
        (df['temperature'] > (Q3['temperature'] + 1.5 * IQR['temperature'])) |
        (df['moisture'] < (Q1['moisture'] - 1.5 * IQR['moisture'])) |
        (df['moisture'] > (Q3['moisture'] + 1.5 * IQR['moisture'])) |
        (df['last_watered'].isnull()) |
        (df['botanist_name'].isnull()) |
        (df['email'].isnull())
    )

    df = df[condition].reset_index(drop=True)
    return df
    

def transform_to_parquet(df: pd.DataFrame, file_path: str) -> None:
    """Transforms the given DataFrame to a Parquet file at the specified file path."""
    df.to_parquet(file_path, index=False)

