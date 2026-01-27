"""
Test suite for the plant data extraction script.

Tests the fetch_plant_data, flatten_plant_data, and extract_all_plants 
functions using mock data and responses.
"""

from unittest.mock import patch, Mock
import pandas as pd
from extract import fetch_plant_data, flatten_plant_data, extract_all_plants


@patch('extract.requests.get')
def test_fetch_valid_plant(mock_get):
    """Test fetching a valid plant returns correct data."""
    mock_response = Mock()
    mock_response.json.return_value = {
        'plant_id': 1,
        'name': 'Rose',
        'scientific_name': ['Rosa'],
    }
    mock_get.return_value = mock_response

    result = fetch_plant_data(1)

    assert result is not None
    assert result['plant_id'] == 1
    assert result['name'] == 'Rose'


@patch('extract.requests.get')
def test_fetch_plant_with_error(mock_get):
    """Test fetching a plant that returns an error."""
    mock_response = Mock()
    mock_response.json.return_value = {
        'error': 'plant not found',
        'plant_id': 7
    }
    mock_get.return_value = mock_response

    result = fetch_plant_data(7)

    assert result is None


@patch('extract.requests.get')
def test_fetch_plant_on_loan(mock_get):
    """Test fetching a plant on loan returns None."""
    mock_response = Mock()
    mock_response.json.return_value = {
        'error': 'plant on loan to another museum',
        'plant_id': 43
    }
    mock_get.return_value = mock_response

    result = fetch_plant_data(43)

    assert result is None


def test_flatten_complete_plant_data():
    """Test flattening plant data with all fields."""
    plant_data = {
        'plant_id': 8,
        'name': 'Bird of paradise',
        'scientific_name': ['Heliconia schiedeana'],
        'soil_moisture': 32.35,
        'temperature': 16.61,
        'last_watered': '2026-01-26T14:47:07',
        'recording_taken': '2026-01-27T10:33:08',
        'botanist': {
            'name': 'Anna Davis',
            'email': 'anna.davis@lnhm.co.uk',
            'phone': '(601)561-8163'
        },
        'origin_location': {
            'city': 'South Tina',
            'country': 'United Arab Emirates',
            'latitude': '-60.9363685',
            'longitude': '-152.763324'
        }
    }

    result = flatten_plant_data(plant_data)

    assert result['plant_id'] == 8
    assert result['common_name'] == 'Bird of paradise'
    assert result['botanist_name'] == 'Anna Davis'
    assert result['city'] == 'South Tina'
    assert result['lat'] == '-60.9363685'


def test_flatten_plant_data_with_missing_fields():
    """Test flattening plant data with missing nested fields."""
    plant_data = {
        'plant_id': 5,
        'name': 'Cactus',
        'soil_moisture': 10.5,
        'temperature': 25.0
    }

    result = flatten_plant_data(plant_data)

    assert result['plant_id'] == 5
    assert result['common_name'] == 'Cactus'
    assert result['botanist_name'] is None
    assert result['city'] is None


def test_flatten_none_plant_data():
    """Test flattening None returns None."""
    result = flatten_plant_data(None)
    assert result is None


@patch('extract.fetch_plant_data')
def test_extract_multiple_plants(mock_fetch):
    """Test extracting multiple plants returns DataFrame."""
    mock_fetch.side_effect = [
        {
            'plant_id': 1,
            'name': 'Rose',
            'scientific_name': ['Rosa'],
            'soil_moisture': 30.0,
            'temperature': 20.0,
            'botanist': {'name': 'John Doe'},
            'origin_location': {'city': 'London'}
        },
        {
            'plant_id': 2,
            'name': 'Tulip',
            'scientific_name': ['Tulipa'],
            'soil_moisture': 35.0,
            'temperature': 18.0,
            'botanist': {'name': 'Jane Smith'},
            'origin_location': {'city': 'Amsterdam'}
        }
    ]

    result = extract_all_plants(1, 2)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert result.iloc[0]['common_name'] == 'Rose'
    assert result.iloc[1]['common_name'] == 'Tulip'


@patch('extract.fetch_plant_data')
def test_extract_with_errors(mock_fetch):
    """Test extracting plants with some errors."""
    mock_fetch.side_effect = [
        {
            'plant_id': 1,
            'name': 'Rose',
            'scientific_name': ['Rosa'],
            'botanist': {},
            'origin_location': {}
        },
        None,
        {
            'plant_id': 3,
            'name': 'Daisy',
            'scientific_name': ['Bellis'],
            'botanist': {},
            'origin_location': {}
        }
    ]

    result = extract_all_plants(1, 3)

    assert len(result) == 2
    assert result.iloc[0]['plant_id'] == 1
    assert result.iloc[1]['plant_id'] == 3


@patch('extract.fetch_plant_data')
def test_extract_all_errors(mock_fetch):
    """Test extracting when all requests fail."""
    mock_fetch.return_value = None

    result = extract_all_plants(1, 5)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0
