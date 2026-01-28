"""This script loads transformed data into the Microsoft SQL Server database."""

import json
import os
from typing import List, Tuple

import pandas as pd
import pyodbc


def _get_credentials_from_secrets_manager() -> dict:
    """Fetch database credentials from AWS Secrets Manager."""
    import boto3
    secret_name = os.getenv('SECRET_NAME')
    region = os.getenv('AWS_REGION', 'eu-west-2')

    client = boto3.client('secretsmanager', region_name=region)
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])


def get_db_connection() -> pyodbc.Connection:
    """Create and return a pyodbc connection for Microsoft SQL Server."""
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    name = os.getenv('DB_NAME')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')

    connection_string = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={host};PORT={port};DATABASE={name};UID={user};PWD={password};TrustServerCertificate=yes;"
        f"SERVER={host},{port};"
        f"DATABASE={name};"
        f"UID={user};"
        f"PWD={password}"
    )
    return pyodbc.connect(connection_string)


def _build_insert_query(table_name: str, columns: List[str]) -> str:
    """Build a parameterized INSERT query for the given table and columns."""
    placeholders = ', '.join(['?' for _ in columns])
    column_names = ', '.join(columns)
    return f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"


def _dataframe_to_tuples(df: pd.DataFrame) -> List[Tuple]:
    """Convert a DataFrame to a list of tuples for bulk insert."""
    return [tuple(row) for row in df.itertuples(index=False, name=None)]


def load_master_table(df: pd.DataFrame, table_name: str, conn: pyodbc.Connection) -> None:
    """Load a master data table to the database (one-time load)."""
    cursor = conn.cursor()
    columns = df.columns.tolist()
    query = _build_insert_query(table_name, columns)
    data = _dataframe_to_tuples(df)

    cursor.executemany(query, data)
    conn.commit()
    cursor.close()
    print(f"Loaded {len(df)} rows to {table_name}")


def load_country_table(df: pd.DataFrame, conn: pyodbc.Connection) -> int:
    """Load new country master data to the Country table."""
    existing = get_country_lookup(conn)
    if not existing.empty:
        df = df[~df['country'].isin(existing['country'])]
    if df.empty:
        print("No new countries to load")
        return 0
    load_master_table(df, 'Country', conn)
    return len(df)


def load_botanist_table(df: pd.DataFrame, conn: pyodbc.Connection) -> int:
    """Load new botanist master data to the Botanist table."""
    existing = get_botanist_lookup(conn)
    if not existing.empty:
        df = df[~df['botanist_name'].isin(existing['botanist_name'])]
    if df.empty:
        print("No new botanists to load")
        return 0
    load_master_table(df, 'Botanist', conn)
    return len(df)


def load_location_table(df: pd.DataFrame, conn: pyodbc.Connection) -> int:
    """Load new location master data to the Location table with FK lookup."""
    existing = get_location_lookup(conn)
    if not existing.empty:
        df = df[~df['city'].isin(existing['city'])]
    if df.empty:
        print("No new locations to load")
        return 0
    country_lookup = get_country_lookup(conn)
    df = df.merge(country_lookup, on='country', how='left')
    df = df[['city', 'lat', 'long', 'country_id']]
    load_master_table(df, 'Location', conn)
    return len(df)


def load_plant_table(df: pd.DataFrame, conn: pyodbc.Connection) -> int:
    """Load new plant master data to the Plant table with FK lookup."""
    existing = _get_existing_plant_ids(conn)
    if existing:
        df = df[~df['plant_id'].isin(existing)]
    if df.empty:
        print("No new plants to load")
        return 0
    location_lookup = get_location_lookup(conn)
    df = df.merge(location_lookup, on='city', how='left')
    df = df[['plant_id', 'scientific_name', 'common_name', 'location_id']]
    load_master_table(df, 'Plant', conn)
    return len(df)


def _get_existing_plant_ids(conn: pyodbc.Connection) -> set:
    """Fetch existing plant_ids from database."""
    cursor = conn.cursor()
    cursor.execute("SELECT plant_id FROM Plant")
    rows = cursor.fetchall()
    cursor.close()
    return {row[0] for row in rows}


def load_all_master_data(country_df: pd.DataFrame, botanist_df: pd.DataFrame, location_df: pd.DataFrame, plant_df: pd.DataFrame, conn: pyodbc.Connection) -> dict:
    """Load all master data tables, only inserting new records."""
    # Load in FK dependency order
    countries = load_country_table(country_df, conn)
    locations = load_location_table(location_df, conn)
    plants = load_plant_table(plant_df, conn)
    botanists = load_botanist_table(botanist_df, conn)
    print(
        f"Master data sync complete: {countries} countries, {locations} locations, {plants} plants, {botanists} botanists added.")
    return {'countries': countries, 'locations': locations, 'plants': plants, 'botanists': botanists}


def load_record_table(df: pd.DataFrame, conn: pyodbc.Connection) -> int:
    """Load new records to the Record table with FK lookup for botanist_id only."""
    if df.empty:
        print("No records to load")
        return 0

    botanist_lookup = get_botanist_lookup(conn)

    df = df.merge(botanist_lookup, on='botanist_name', how='left')
    df = df.dropna(subset=['plant_id', 'botanist_id'])
    df['plant_id'] = df['plant_id'].astype(int)
    df['botanist_id'] = df['botanist_id'].astype(int)
    df = df[['plant_id', 'recording_taken', 'moisture',
             'temperature', 'last_watered', 'botanist_id']]

    if df.empty:
        print("No valid records after FK lookup")
        return 0

    cursor = conn.cursor()
    columns = df.columns.tolist()
    query = _build_insert_query('Record', columns)
    data = _dataframe_to_tuples(df)

    cursor.executemany(query, data)
    conn.commit()
    cursor.close()
    print(f"Loaded {len(df)} new records")
    return len(df)


def check_master_data_exists(conn: pyodbc.Connection) -> bool:
    """Check if all master data tables already have data."""
    cursor = conn.cursor()
    tables = ['Country', 'Location', 'Plant', 'Botanist']

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.close()
            return False

    cursor.close()
    return True


def get_country_lookup(conn: pyodbc.Connection) -> pd.DataFrame:
    """Fetch country_id and country mapping from database."""
    cursor = conn.cursor()
    cursor.execute("SELECT country_id, country FROM Country")
    rows = [tuple(row) for row in cursor.fetchall()]
    cursor.close()
    return pd.DataFrame(rows, columns=['country_id', 'country'])


def get_location_lookup(conn: pyodbc.Connection) -> pd.DataFrame:
    """Fetch location_id and city mapping from database."""
    cursor = conn.cursor()
    cursor.execute("SELECT location_id, city FROM Location")
    rows = [tuple(row) for row in cursor.fetchall()]
    cursor.close()
    return pd.DataFrame(rows, columns=['location_id', 'city'])


def get_botanist_lookup(conn: pyodbc.Connection) -> pd.DataFrame:
    """Fetch botanist_id and botanist_name mapping from database."""
    cursor = conn.cursor()
    cursor.execute("SELECT botanist_id, botanist_name FROM Botanist")
    rows = [tuple(row) for row in cursor.fetchall()]
    cursor.close()
    return pd.DataFrame(rows, columns=['botanist_id', 'botanist_name'])
