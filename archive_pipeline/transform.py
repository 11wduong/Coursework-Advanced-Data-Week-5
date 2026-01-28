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


def _apply_iqr_filter(series: pd.Series) -> tuple:
    """Applies IQR method to filter outliers from a series.
    Returns a tuple of (filtered_series, outlier_count)."""
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    mask = (series >= lower_bound) & (series <= upper_bound)
    outlier_count = len(series) - len(series[mask])
    return series[mask], outlier_count


def clean_outliers(df: pd.DataFrame) -> tuple:
    """Removes outliers from moisture and temperature columns based on plant id using IQR method.
    Returns a tuple of (cleaned_df, outlier_counts_dict) where outlier_counts_dict tracks
    temperature and moisture outliers separately per plant_id."""
    cleaned_dfs = []
    outlier_counts = {}

    for plant_id, group in df.groupby('plant_id'):
        # Track temperature outliers
        temp_filtered, temp_outliers = _apply_iqr_filter(group['temperature'])
        group = group.loc[temp_filtered.index]

        # Track moisture outliers
        moist_filtered, moisture_outliers = _apply_iqr_filter(
            group['moisture'])
        group = group.loc[moist_filtered.index]

        outlier_counts[plant_id] = {
            'temperature': temp_outliers, 'moisture': moisture_outliers}
        cleaned_dfs.append(group)

    return pd.concat(cleaned_dfs, ignore_index=True), outlier_counts


def add_outlier_columns(avg_df: pd.DataFrame, outlier_counts: dict) -> pd.DataFrame:
    """Adds temperature_outliers and moisture_outliers columns to the average dataframe."""
    avg_df['temperature_outliers'] = avg_df['plant_id'].map(
        lambda pid: outlier_counts.get(pid, {}).get('temperature', 0)
    )
    avg_df['moisture_outliers'] = avg_df['plant_id'].map(
        lambda pid: outlier_counts.get(pid, {}).get('moisture', 0)
    )
    return avg_df


def calculate_averages(cleaned_df: pd.DataFrame, outlier_counts: dict) -> pd.DataFrame:
    """Calculates average temperature and moisture for each plant.
    Averages are rounded to 2 decimal places.
    Includes separate columns for temperature_outliers and moisture_outliers."""
    avg_df = cleaned_df.groupby(['plant_id', 'common_name', 'scientific_name']).agg(
        avg_temperature=('temperature', 'mean'),
        avg_moisture=('moisture', 'mean')
    ).reset_index()

    avg_df = add_outlier_columns(avg_df, outlier_counts)

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
    final_avg_df = calculate_averages(cleaned_df, outlier_counts)

    transform_to_csv(
        final_avg_df, f'output/summary.csv')
