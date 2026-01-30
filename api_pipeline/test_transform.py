"""Test suite for transform.py - Tests data transformation functions."""

import pandas as pd
import pytest
from transform import (
    _clean_list_columns,
    create_country_table,
    create_botanist_table,
    create_location_table,
    create_plant_table,
    create_record_table,
)


@pytest.fixture
def sample_data():
    """Create sample dataframe for testing."""
    return pd.DataFrame({
        'plant_id': [1, 2, 3, 4],
        'country': ['USA', 'Canada', 'USA', 'Mexico'],
        'city': ['New York', 'Toronto', 'Los Angeles', 'Mexico City'],
        'lat': [40.7128, 43.6629, 34.0522, 19.4326],
        'long': [-74.0060, -79.3957, -118.2437, -99.1332],
        'botanist_name': ['Alice Johnson', 'Bob Smith', 'Alice Johnson', 'Carol Davis'],
        'email': ['alice@example.com', 'bob@example.com', 'alice@example.com', 'carol@example.com'],
        'phone': ['555-0001', '555-0002', '555-0001', '555-0003'],
        'scientific_name': ['Quercus alba', 'Pinus strobus', 'Quercus alba', 'Psidium guajava'],
        'common_name': ['White Oak', 'Eastern White Pine', 'White Oak', 'Guava'],
        'recording_taken': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04']),
        'moisture': [45.5, 60.2, 50.1, 55.8],
        'temperature': [72.3, 68.5, 75.2, 70.1],
        'last_watered': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-01', '2024-01-03']),
    })


class TestCleanListColumns:
    """Test cases for _clean_list_columns function."""

    def test_converts_list_to_first_element(self):
        """Test that lists are converted to their first element."""
        df = pd.DataFrame({'col': [['a', 'b'], ['c']]})
        result = _clean_list_columns(df, columns=['col'])
        assert result['col'].tolist() == ['a', 'c']

    def test_empty_list_becomes_empty_string(self):
        """Test that empty lists become empty strings."""
        df = pd.DataFrame({'col': [[], ['a']]})
        result = _clean_list_columns(df, columns=['col'])
        assert result['col'].tolist() == ['', 'a']

    def test_non_list_values_unchanged(self):
        """Test that non-list values remain unchanged."""
        df = pd.DataFrame({'col': ['a', 'b', 'c']})
        result = _clean_list_columns(df, columns=['col'])
        assert result['col'].tolist() == ['a', 'b', 'c']

    def test_does_not_modify_original(self):
        """Test that original dataframe is not modified."""
        df = pd.DataFrame({'col': [['a', 'b']]})
        _clean_list_columns(df, columns=['col'])
        assert df['col'].tolist() == [['a', 'b']]


class TestCreateCountryTable:
    """Test cases for create_country_table function."""

    def test_creates_unique_countries(self, sample_data):
        """Test that function extracts unique countries."""
        result = create_country_table(sample_data)
        assert len(result) == 3
        assert set(result['country'].values) == {'USA', 'Canada', 'Mexico'}

    def test_returns_only_country_column(self, sample_data):
        """Test that only country column is returned."""
        result = create_country_table(sample_data)
        assert list(result.columns) == ['country']

    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        empty_df = pd.DataFrame({'country': []})
        result = create_country_table(empty_df)
        assert len(result) == 0


class TestCreateBotanistTable:
    """Test cases for create_botanist_table function."""

    def test_creates_unique_botanists(self, sample_data):
        """Test that function extracts unique botanists."""
        result = create_botanist_table(sample_data)
        assert len(result) == 3

    def test_returns_correct_columns(self, sample_data):
        """Test that correct columns are returned."""
        result = create_botanist_table(sample_data)
        assert list(result.columns) == ['botanist_name', 'email', 'phone']

    def test_preserves_botanist_data(self, sample_data):
        """Test that botanist data is preserved correctly."""
        result = create_botanist_table(sample_data)
        assert 'Alice Johnson' in result['botanist_name'].values
        assert 'alice@example.com' in result['email'].values

    def test_truncates_long_phone_numbers(self):
        """Test that phone numbers are truncated to 20 characters."""
        df = pd.DataFrame({
            'botanist_name': ['Test'],
            'email': ['test@test.com'],
            'phone': ['123456789012345678901234567890']
        })
        result = create_botanist_table(df)
        assert len(result['phone'].iloc[0]) == 20


class TestCreateLocationTable:
    """Test cases for create_location_table function."""

    def test_creates_unique_locations(self, sample_data):
        """Test that function extracts unique locations."""
        result = create_location_table(sample_data)
        assert len(result) == 4

    def test_returns_correct_columns(self, sample_data):
        """Test that correct columns are returned."""
        result = create_location_table(sample_data)
        assert list(result.columns) == ['city', 'lat', 'long', 'country']

    def test_preserves_country_natural_key(self, sample_data):
        """Test that country natural key is preserved for FK lookup in load."""
        result = create_location_table(sample_data)
        assert 'country' in result.columns
        assert 'USA' in result['country'].values

    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        empty_df = pd.DataFrame(
            {'city': [], 'lat': [], 'long': [], 'country': []})
        result = create_location_table(empty_df)
        assert len(result) == 0


class TestCreatePlantTable:
    """Test cases for create_plant_table function."""

    def test_creates_unique_plants(self, sample_data):
        """Test that function extracts unique plants."""
        result = create_plant_table(sample_data)
        assert len(result) == 4

    def test_returns_correct_columns(self, sample_data):
        """Test that correct columns are returned."""
        result = create_plant_table(sample_data)
        assert list(result.columns) == [
            'plant_id', 'scientific_name', 'common_name', 'city']

    def test_handles_list_scientific_names(self):
        """Test that list scientific names are cleaned."""
        df = pd.DataFrame({
            'plant_id': [1],
            'scientific_name': [['Rosa', 'Rosa alba']],
            'common_name': ['Rose'],
            'city': ['London']
        })
        result = create_plant_table(df)
        assert result['scientific_name'].iloc[0] == 'Rosa'

    def test_preserves_city_natural_key(self, sample_data):
        """Test that city natural key is preserved for FK lookup in load."""
        result = create_plant_table(sample_data)
        assert 'city' in result.columns
        assert 'New York' in result['city'].values

    def test_preserves_plant_id_from_api(self, sample_data):
        """Test that plant_id from API is preserved."""
        result = create_plant_table(sample_data)
        assert 'plant_id' in result.columns
        assert 1 in result['plant_id'].values


class TestCreateRecordTable:
    """Test cases for create_record_table function."""

    def test_returns_correct_columns(self, sample_data):
        """Test that correct columns are returned."""
        result = create_record_table(sample_data)
        expected_cols = ['plant_id', 'botanist_name', 'recording_taken',
                         'moisture', 'temperature', 'last_watered']
        assert list(result.columns) == expected_cols

    def test_preserves_plant_id_and_botanist_name(self, sample_data):
        """Test that plant_id and botanist_name are preserved."""
        result = create_record_table(sample_data)
        assert 'plant_id' in result.columns
        assert 'botanist_name' in result.columns
        assert 1 in result['plant_id'].values
        assert 'Alice Johnson' in result['botanist_name'].values

    def test_preserves_record_data(self, sample_data):
        """Test that record data (moisture, temperature) is preserved."""
        result = create_record_table(sample_data)
        assert 45.5 in result['moisture'].values
        assert 72.3 in result['temperature'].values

    def test_handles_list_botanist_name(self):
        """Test that list values in botanist_name are cleaned."""
        df = pd.DataFrame({
            'plant_id': [1],
            'botanist_name': [['John', 'John Smith']],
            'recording_taken': [pd.Timestamp('2024-01-01')],
            'moisture': [50.0],
            'temperature': [70.0],
            'last_watered': [pd.Timestamp('2024-01-01')]
        })
        result = create_record_table(df)
        assert result['botanist_name'].iloc[0] == 'John'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
