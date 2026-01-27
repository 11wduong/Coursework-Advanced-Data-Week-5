import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os


def create_db_engine():
    """Create database engine from environment variables"""
    load_dotenv()

    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')

    connection_string = f"mssql+pyodbc://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?driver=ODBC+Driver+17+for+SQL+Server"
    return create_engine(connection_string)


def load_country(df, engine, schema):
    """Load Country data"""
    df.to_sql('Country', engine, schema=schema,
              if_exists='append', index=False)
    print(f"✓ Loaded {len(df)} rows into Country table")


def load_location(df, engine, schema):
    """Load Location data"""
    df.to_sql('Location', engine, schema=schema,
              if_exists='append', index=False)
    print(f"✓ Loaded {len(df)} rows into Location table")


def load_plant(df, engine, schema):
    """Load Plant data"""
    df.to_sql('Plant', engine, schema=schema, if_exists='append', index=False)
    print(f"✓ Loaded {len(df)} rows into Plant table")


def load_botanist(df, engine, schema):
    """Load Botanist data"""
    df.to_sql('Botanist', engine, schema=schema,
              if_exists='append', index=False)
    print(f"✓ Loaded {len(df)} rows into Botanist table")


def load_record(df, engine, schema):
    """Load Record data"""
    df.to_sql('Record', engine, schema=schema, if_exists='append', index=False)
    print(f"✓ Loaded {len(df)} rows into Record table")


def load_all(country_df, location_df, plant_df, botanist_df, record_df):
    """Load all data in the correct order"""
    engine = create_db_engine()
    schema = os.getenv('DB_SCHEMA')

    try:
        # Load in correct order due to foreign key constraints
        load_country(country_df, engine, schema)
        load_location(location_df, engine, schema)
        load_plant(plant_df, engine, schema)
        load_botanist(botanist_df, engine, schema)
        load_record(record_df, engine, schema)
        print("\n✓ All data loaded successfully!")
    except Exception as e:
        print(f"\n✗ Error loading data: {e}")
        raise
