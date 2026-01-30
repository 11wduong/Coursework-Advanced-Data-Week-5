"""Test suite for load.py (Pipeline 2 S3 upload)."""

import pandas as pd
from unittest.mock import patch, MagicMock
from load import upload_to_s3, get_s3_client


def test_upload_to_s3_creates_correct_path():
    """Test that upload_to_s3 creates the correct dated folder structure."""
    test_df = pd.DataFrame({
        'plant_id': [1],
        'common_name': ['Rose'],
        'avg_temperature': [22.5]
    })

    with patch('load.boto3.client') as mock_boto:
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        with patch('load.datetime') as mock_datetime:
            mock_datetime.now.return_value = MagicMock(
                year=2026, month=1, day=28
            )

            with patch.dict('os.environ', {'S3_BUCKET_NAME': 'test-bucket'}):
                result = upload_to_s3(test_df)

            # Check put_object was called with correct path
            mock_s3.put_object.assert_called_once()
            call_kwargs = mock_s3.put_object.call_args[1]
            assert call_kwargs['Key'] == '2026/01/28/summary.csv'
            assert call_kwargs['Bucket'] == 'test-bucket'
            assert result == 's3://test-bucket/2026/01/28/summary.csv'


def test_get_s3_client_creates_client():
    """Test that get_s3_client returns a valid S3 client."""
    with patch('load.os.getenv', return_value='eu-west-2'):
        with patch('load.boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client

            result = get_s3_client()

            mock_boto.assert_called_once_with('s3', region_name='eu-west-2')
            assert result == mock_client
