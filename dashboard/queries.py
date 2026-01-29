import os
import awswrangler as wr
from dotenv import load_dotenv


def get_config():
    """Get database and S3 configuration."""
    load_dotenv()
    return {
        'database': os.getenv('ATHENA_DATABASE', 'c21-boxen-plants-db'),
        'bucket': os.getenv('S3_BUCKET_NAME', 'c21-boxen-botanical-archive'),
        's3_output': f"s3://{os.getenv('S3_BUCKET_NAME', 'c21-boxen-botanical-archive')}/athena-results/"
    }


def query_critical_plants(config):
    """Query plants with critical moisture levels (< 20%)."""
    query = """
    SELECT 
        plant_id,
        common_name,
        scientific_name,
        avg_moisture,
        avg_temperature,
        moisture_outliers
    FROM c21_boxen_botanical_archive
    WHERE avg_moisture < 20
    AND partition_0 = CAST(year(current_date - interval '1' day) AS VARCHAR)
    AND partition_1 = LPAD(CAST(month(current_date - interval '1' day) AS VARCHAR), 2, '0')
    AND partition_2 = LPAD(CAST(day(current_date - interval '1' day) AS VARCHAR), 2, '0')
    ORDER BY avg_moisture ASC
    """
    df = wr.athena.read_sql_query(
        query, database=config['database'], s3_output=config['s3_output'])
    return df


def query_moisture_trends(config, days=30):
    """Query moisture trends over time."""
    query = f"""
    SELECT 
        partition_0 || '-' || partition_1 || '-' || partition_2 as date,
        AVG(avg_moisture) as avg_moisture,
        MIN(avg_moisture) as min_moisture,
        MAX(avg_moisture) as max_moisture,
        COUNT(DISTINCT plant_id) as plants_monitored
    FROM c21_boxen_botanical_archive
    WHERE (partition_0 || '-' || partition_1 || '-' || partition_2) >= '2026-01-28'
    GROUP BY partition_0, partition_1, partition_2
    ORDER BY partition_0 DESC, partition_1 DESC, partition_2 DESC
    LIMIT {days}
    """
    df = wr.athena.read_sql_query(
        query, database=config['database'], s3_output=config['s3_output'])
    return df


def query_temperature_trends(config, days=30):
    """Query temperature trends over time."""
    query = f"""
    SELECT 
        partition_0 || '-' || partition_1 || '-' || partition_2 as date,
        AVG(avg_temperature) as avg_temperature,
        MIN(avg_temperature) as min_temperature,
        MAX(avg_temperature) as max_temperature,
        COUNT(DISTINCT plant_id) as plants_monitored
    FROM c21_boxen_botanical_archive
    WHERE (partition_0 || '-' || partition_1 || '-' || partition_2) >= '2026-01-28'
    GROUP BY partition_0, partition_1, partition_2
    ORDER BY partition_0 DESC, partition_1 DESC, partition_2 DESC
    LIMIT {days}
    """
    df = wr.athena.read_sql_query(
        query, database=config['database'], s3_output=config['s3_output'])
    return df


def query_outlier_analysis(config):
    """Query plants with the most outliers."""
    query = """
    SELECT 
        plant_id,
        common_name,
        scientific_name,
        SUM(temperature_outliers) as total_temp_outliers,
        SUM(moisture_outliers) as total_moisture_outliers,
        COUNT(*) as days_recorded
    FROM c21_boxen_botanical_archive
    GROUP BY plant_id, common_name, scientific_name
    HAVING SUM(temperature_outliers) > 0 OR SUM(moisture_outliers) > 0
    ORDER BY (SUM(temperature_outliers) + SUM(moisture_outliers)) DESC
    LIMIT 20
    """
    df = wr.athena.read_sql_query(
        query, database=config['database'], s3_output=config['s3_output'])
    return df
