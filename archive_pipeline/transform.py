"""Transform script"""

import pandas as pd

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


def clean_table(df: pd.DataFrame) -> pd.DataFrame:
    """Drops rows that are outliers from IQR method and handles missing values."""
    df = df.dropna(subset=['temperature', 'moisture'])

    Q1_temp = df['temperature'].quantile(0.25)
    Q3_temp = df['temperature'].quantile(0.75)
    IQR_temp = Q3_temp - Q1_temp

    Q1_moisture = df['moisture'].quantile(0.25)
    Q3_moisture = df['moisture'].quantile(0.75)
    IQR_moisture = Q3_moisture - Q1_moisture

    filtered_df = df[
        (df['temperature'] >= (Q1_temp - 1.5 * IQR_temp)) &
        (df['temperature'] <= (Q3_temp + 1.5 * IQR_temp)) &
        (df['moisture'] >= (Q1_moisture - 1.5 * IQR_moisture)) &
        (df['moisture'] <= (Q3_moisture + 1.5 * IQR_moisture))
    ]

    return filtered_df.reset_index(drop=True)


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
    Q1_temp = df['temperature'].quantile(0.25)
    Q3_temp = df['temperature'].quantile(0.75)
    IQR_temp = Q3_temp - Q1_temp

    Q1_moisture = df['moisture'].quantile(0.25)
    Q3_moisture = df['moisture'].quantile(0.75)
    IQR_moisture = Q3_moisture - Q1_moisture

    temp_outliers = df[(df['temperature'] < (Q1_temp - 1.5 * IQR_temp))
                       | (df['temperature'] > (Q3_temp + 1.5 * IQR_temp))]
    moisture_outliers = df[(df['moisture'] < (Q1_moisture - 1.5 * IQR_moisture))
                           | (df['moisture'] > (Q3_moisture + 1.5 * IQR_moisture))]

    outlier_df = pd.concat([temp_outliers, moisture_outliers]
                           ).drop_duplicates().reset_index(drop=True)

    return outlier_df


def transform_to_csv(df: pd.DataFrame, file_path: str) -> None:
    """Transforms the given DataFrame to a CSV file at the specified file path."""
    df.to_csv(file_path, index=False)


if __name__ == "__main__":
    data = main()
    country_df = data['Country']
    location_df = data['Location']
    botanist_df = data['Botanist']
    plant_df = data['Plant']
    record_df = data['Record']

    final_avg_df = calculate_averages(clean_table(combine_tables(country_df, botanist_df,
                                                                 location_df, plant_df, record_df)))
    outlier_df = create_outlier_df(combine_tables(country_df, botanist_df,
                                                  location_df, plant_df, record_df)).columns

    transform_to_csv(final_avg_df, 'transformed_average_data.csv')
    transform_to_csv(outlier_df, 'outlier_data.csv')
