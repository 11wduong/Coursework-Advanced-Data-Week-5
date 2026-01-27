"""The full ETL pipeline implementation for AWS Lambda."""

from datetime import datetime
from extract import extract_all_plants
from transform import (
    create_country_table,
    create_botanist_table,
    create_location_table,
    create_plant_table,
    create_record_table
)
from load import (
    get_db_connection,
    load_country_table,
    load_botanist_table,
    load_location_table,
    load_plant_table,
    load_record_table,
    load_all_master_data
)


def run_master_data_sync(df: 'pd.DataFrame', conn) -> dict:
    """Sync master data tables, adding any new records."""
    print("Syncing master data...")

    country_df = create_country_table(df)
    botanist_df = create_botanist_table(df)
    location_df = create_location_table(df)
    plant_df = create_plant_table(df)

    return load_all_master_data(country_df, botanist_df, location_df, plant_df, conn)


def run_record_pipeline(df: 'pd.DataFrame', conn) -> int:
    """Run the ETL pipeline to load new sensor records."""
    print(f"[{datetime.now()}] Running record pipeline...")

    record_df = create_record_table(df)
    records_loaded = load_record_table(record_df, conn)

    return records_loaded


def handler(event, context) -> dict:
    """AWS Lambda handler function triggered by EventBridge."""
    try:
        conn = get_db_connection()

        # Extract data once
        df = extract_all_plants(1, 50)
        print(f"Extracted {len(df)} plant records")

        # Always sync master data (only inserts new records)
        run_master_data_sync(df, conn)

        # Load sensor records
        records_loaded = run_record_pipeline(df, conn)

        conn.close()
        print(
            f"[{datetime.now()}] Pipeline complete. Loaded {records_loaded} records.")

        return {
            'statusCode': 200,
            'body': f'Successfully loaded {records_loaded} records'
        }
    except Exception as e:
        print(f"Error in pipeline: {e}")
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }


if __name__ == "__main__":
    handler(None, None)
