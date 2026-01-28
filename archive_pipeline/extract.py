"""
Extract script to retrieve all data from the LMNH plant database.
"""
import os
import pymssql
from dotenv import load_dotenv
import pandas as pd


def get_db_connection():
    """Create and return a database connection using environment variables."""
    load_dotenv()

    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "1433")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    conn = pymssql.connect(
        server=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name
    )

    return conn


def extract_table_data(conn, table_name):
    """Extract all data from a specified table."""
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql(query, conn)
    return df


def extract_all_data(conn):
    """Extract data from all tables in the database."""
    tables = ['Country', 'Location', 'Plant', 'Botanist', 'Record']

    data = {}
    for table in tables:
        print(f"Extracting data from {table}...")
        data[table] = extract_table_data(conn, table)
        print(f"  - Extracted {len(data[table])} rows from {table}")

    return data


def main():
    """Main function to extract all database data."""
    print("Connecting to database...")
    conn = get_db_connection()

    try:
        print("\nExtracting data from all tables...")
        all_data = extract_all_data(conn)

        print("\n=== Extraction Summary ===")
        for table_name, df in all_data.items():
            print(f"{table_name}: {len(df)} rows, {len(df.columns)} columns")

        return all_data

    finally:
        conn.close()


if __name__ == "__main__":
    data = main()
