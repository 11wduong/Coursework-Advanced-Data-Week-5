"""Transform script"""

import pandas as pd
from pathlib import Path
from extract import main


def combine_tables(country_df: pd.DataFrame, botanist_df: pd.DataFrame,
                   location_df: pd.DataFrame, plant_df: pd.DataFrame,
                   record_df: pd.DataFrame) -> pd.DataFrame:
    """Combines all the tables into a single dataframe for easier export or analysis."""
    df = record_df.merge(plant_df, on='plant_id', how='left')
    df = df.merge(location_df, on='location_id', how='left')
    df = df.merge(country_df, on='country_id', how='left')
    df = df.merge(botanist_df, on='botanist_id', how='left')
    return df


def clean_outliers(df: pd.DataFrame) -> tuple:
    """Removes outliers from moisture and temperature columns based on plant id using IQR method.
    Returns a tuple of (cleaned_df, outlier_counts_dict) where outlier_counts_dict tracks
    temperature and moisture outliers separately per plant_id."""
    cleaned_dfs = []
    outlier_counts = {}

    for plant_id, group in df.groupby('plant_id'):
        original_size = len(group)
        temp_outliers = 0
        moisture_outliers = 0

        # Track temperature outliers
        Q1_temp = group['temperature'].quantile(0.25)
        Q3_temp = group['temperature'].quantile(0.75)
        IQR_temp = Q3_temp - Q1_temp
        lower_bound_temp = Q1_temp - 1.5 * IQR_temp
        upper_bound_temp = Q3_temp + 1.5 * IQR_temp
        temp_mask = (group['temperature'] >= lower_bound_temp) & (
            group['temperature'] <= upper_bound_temp)
        temp_outliers = len(group) - len(group[temp_mask])
        group = group[temp_mask]

        # Track moisture outliers
        Q1_moist = group['moisture'].quantile(0.25)
        Q3_moist = group['moisture'].quantile(0.75)
        IQR_moist = Q3_moist - Q1_moist
        lower_bound_moist = Q1_moist - 1.5 * IQR_moist
        upper_bound_moist = Q3_moist + 1.5 * IQR_moist
        moist_mask = (group['moisture'] >= lower_bound_moist) & (
            group['moisture'] <= upper_bound_moist)
        moisture_outliers = len(group) - len(group[moist_mask])
        group = group[moist_mask]

        outlier_counts[plant_id] = {
            'temperature': temp_outliers, 'moisture': moisture_outliers}
        cleaned_dfs.append(group)

    return pd.concat(cleaned_dfs, ignore_index=True), outlier_counts


def calculate_averages(original_df: pd.DataFrame, cleaned_df: pd.DataFrame, outlier_counts: dict) -> pd.DataFrame:
    """Calculates average temperature and moisture for each plant.
    Averages are rounded to 2 decimal places.
    Includes separate columns for temperature_outliers and moisture_outliers."""
    cleaned_df = cleaned_df.copy()

    avg_df = cleaned_df.groupby(['plant_id', 'common_name', 'scientific_name']).agg(
        avg_temperature=('temperature', 'mean'),
        avg_moisture=('moisture', 'mean')
    ).reset_index()

    # Add temperature and moisture outlier counts
    avg_df['temperature_outliers'] = avg_df['plant_id'].map(
        lambda pid: outlier_counts.get(pid, {}).get('temperature', 0)
    )
    avg_df['moisture_outliers'] = avg_df['plant_id'].map(
        lambda pid: outlier_counts.get(pid, {}).get('moisture', 0)
    )

    avg_df['avg_temperature'] = avg_df['avg_temperature'].round(2)
    avg_df['avg_moisture'] = avg_df['avg_moisture'].round(2)

    return avg_df


def transform_to_csv(df: pd.DataFrame, file_path: str) -> None:
    """Transforms the given DataFrame to a CSV file at the specified file path."""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(file_path, index=False)


if __name__ == "__main__":
    data = main()
    country_df = data['Country']
    location_df = data['Location']
    botanist_df = data['Botanist']
    plant_df = data['Plant']
    record_df = data['Record']

    combined_df = combine_tables(country_df, botanist_df,
                                 location_df, plant_df, record_df)
    cleaned_df, outlier_counts = clean_outliers(combined_df)
    final_avg_df = calculate_averages(combined_df, cleaned_df, outlier_counts)

    transform_to_csv(
        final_avg_df, f'output/summary.csv')
