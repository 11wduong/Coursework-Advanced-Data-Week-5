"""Load script to upload summary CSV to S3."""

import os
from datetime import datetime
from io import StringIO
import boto3
import pandas as pd


def get_s3_client():
    """Create and return an S3 client."""
    return boto3.client('s3', region_name=os.getenv('REGION_NAME'))


def upload_to_s3(df: pd.DataFrame) -> str:
    """
    Upload DataFrame as CSV to S3 with dated folder structure.
    """
    bucket_name = os.getenv('S3_BUCKET_NAME')

    # Create dated path: 2026/01/28/summary.csv
    now = datetime.now()
    s3_key = f"{now.year}/{now.month:02d}/{now.day:02d}/summary.csv"

    # Convert DataFrame to CSV string
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_string = csv_buffer.getvalue()

    # Upload to S3
    s3_client = get_s3_client()
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=csv_string,
        ContentType='text/csv'
    )

    s3_uri = f"s3://{bucket_name}/{s3_key}"
    print(f"✓ Uploaded summary to {s3_uri}")

    return s3_uri
