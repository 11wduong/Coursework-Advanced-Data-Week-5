"""Main pipeline script to orchestrate ETL process and database cleanup."""

import os
from datetime import datetime
import pymssql
from extract import get_db_connection, extract_all_data
from transform import combine_tables, clean_outliers, calculate_averages
from load import upload_to_s3


def cleanup_old_records(conn):
    """Delete all records from the Record table."""
    cursor = conn.cursor()

    query = "DELETE FROM Record"

    cursor.execute(query)
    conn.commit()

    rows_deleted = cursor.rowcount
    cursor.close()

    print(f"✓ Deleted {rows_deleted} records from Record table")
    return rows_deleted


def handler(event, context):
    """AWS Lambda handler function."""
    try:
        print(f"[{datetime.now()}] Starting archive pipeline...")

        # Connect to database
        conn = get_db_connection()

        # Extract
        print("\n--- EXTRACT ---")
        all_data = extract_all_data(conn)

        # Transform
        print("\n--- TRANSFORM ---")
        country_df = all_data['Country']
        location_df = all_data['Location']
        botanist_df = all_data['Botanist']
        plant_df = all_data['Plant']
        record_df = all_data['Record']

        print("Combining tables...")
        combined_df = combine_tables(
            country_df, botanist_df, location_df, plant_df, record_df)

        print("Cleaning outliers...")
        cleaned_df, outlier_counts = clean_outliers(combined_df)

        print("Calculating averages...")
        final_avg_df = calculate_averages(cleaned_df, outlier_counts)
        print(f"  - Created summary with {len(final_avg_df)} plants")

        # Load
        print("\n--- LOAD ---")
        s3_uri = upload_to_s3(final_avg_df)

        # Cleanup
        print("\n--- CLEANUP ---")
        rows_deleted = cleanup_old_records(conn)

        # Close connection
        conn.close()

        print(f"\n[{datetime.now()}] Pipeline complete!")
        print(
            f"Summary: {len(final_avg_df)} plants, {rows_deleted} records deleted")

        return {
            'statusCode': 200,
            'body': f'Success: Uploaded to {s3_uri}, deleted {rows_deleted} records'
        }

    except Exception as e:
        print(f"Error in pipeline: {e}")
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }


if __name__ == "__main__":
    handler(None, None)
