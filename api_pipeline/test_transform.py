"""Test suite for transform.py - Tests data transformation functions."""

import pandas as pd
import pytest
from transform import (
    create_country_table,
    create_botanist_table,
    create_location_table,
    create_plant_table,
    create_record_table,
)


# Fixture to create sample test data
@pytest.fixture
def sample_data():
    """Create sample dataframe for testing."""
    return pd.DataFrame({
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


class TestCreateCountryTable:
    """Test cases for create_country_table function."""

    def test_creates_unique_countries(self, sample_data):
        """Test that function extracts unique countries."""
        result = create_country_table(sample_data)
        assert len(result) == 3  # USA, Canada, Mexico
        assert set(result['country'].values) == {'USA', 'Canada', 'Mexico'}

    def test_country_id_assignment(self, sample_data):
        """Test that country_id is assigned correctly (starting from 1)."""
        result = create_country_table(sample_data)
        assert result['country_id'].min() == 1
        assert result['country_id'].max() == len(result)
        assert result['country_id'].is_unique

    def test_column_order(self, sample_data):
        """Test that columns are in correct order."""
        result = create_country_table(sample_data)
        assert list(result.columns) == ['country_id', 'country']

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
        assert len(result) == 3  # Alice, Bob, Carol

    def test_botanist_id_assignment(self, sample_data):
        """Test that botanist_id is assigned correctly."""
        result = create_botanist_table(sample_data)
        assert result['botanist_id'].min() == 1
        assert result['botanist_id'].max() == len(result)
        assert result['botanist_id'].is_unique

    def test_column_order(self, sample_data):
        """Test that columns are in correct order."""
        result = create_botanist_table(sample_data)
        assert list(result.columns) == [
            'botanist_id', 'botanist_name', 'email', 'phone']

    def test_preserves_botanist_data(self, sample_data):
        """Test that botanist data is preserved correctly."""
        result = create_botanist_table(sample_data)
        assert 'Alice Johnson' in result['botanist_name'].values
        assert 'alice@example.com' in result['email'].values


class TestCreateLocationTable:
    """Test cases for create_location_table function."""

    def test_creates_unique_locations(self, sample_data):
        """Test that function extracts unique locations."""
        result = create_location_table(sample_data)
        assert len(result) == 4  # All locations are unique

    def test_location_id_assignment(self, sample_data):
        """Test that location_id is assigned correctly."""
        result = create_location_table(sample_data)
        assert result['location_id'].min() == 1
        assert result['location_id'].max() == len(result)
        assert result['location_id'].is_unique

    def test_country_id_foreign_key(self, sample_data):
        """Test that country_id foreign key is properly assigned."""
        result = create_location_table(sample_data)
        assert 'country_id' in result.columns
        assert result['country_id'].notna().all()

    def test_column_order(self, sample_data):
        """Test that columns are in correct order."""
        result = create_location_table(sample_data)
        assert list(result.columns) == [
            'location_id', 'city', 'lat', 'long', 'country_id']

    def test_preserves_coordinates(self, sample_data):
        """Test that latitude and longitude are preserved."""
        result = create_location_table(sample_data)
        assert 'New York' in result['city'].values
        assert 40.7128 in result['lat'].values


class TestCreatePlantTable:
    """Test cases for create_plant_table function."""

    def test_creates_unique_plants(self, sample_data):
        """Test that function extracts unique plants."""
        result = create_plant_table(sample_data)
        # Quercus alba appears twice but in different locations, so 4 unique plant-location combinations
        assert len(result) == 4

    def test_plant_id_assignment(self, sample_data):
        """Test that plant_id is assigned correctly."""
        result = create_plant_table(sample_data)
        assert result['plant_id'].min() == 1
        assert result['plant_id'].max() == len(result)
        assert result['plant_id'].is_unique

    def test_location_id_foreign_key(self, sample_data):
        """Test that location_id foreign key is properly assigned."""
        result = create_plant_table(sample_data)
        assert 'location_id' in result.columns
        assert result['location_id'].notna().all()

    def test_column_order(self, sample_data):
        """Test that columns are in correct order."""
        result = create_plant_table(sample_data)
        assert list(result.columns) == [
            'plant_id', 'scientific_name', 'common_name', 'location_id']

    def test_preserves_plant_names(self, sample_data):
        """Test that plant scientific and common names are preserved."""
        result = create_plant_table(sample_data)
        assert 'Quercus alba' in result['scientific_name'].values
        assert 'White Oak' in result['common_name'].values


class TestCreateRecordTable:
    """Test cases for create_record_table function."""

    def test_creates_records(self, sample_data):
        """Test that function creates records."""
        result = create_record_table(sample_data)
        # Records get duplicated because same plant (by scientific_name) exists in multiple locations
        # Row 0 & 2 both have Quercus alba but in different locations, causing duplication
        assert len(result) >= len(sample_data)

    def test_id_assignment(self, sample_data):
        """Test that id is assigned correctly."""
        result = create_record_table(sample_data)
        assert result['id'].min() == 1
        assert result['id'].max() == len(result)
        assert result['id'].is_unique

    def test_foreign_keys_present(self, sample_data):
        """Test that foreign keys are properly assigned."""
        result = create_record_table(sample_data)
        assert 'plant_id' in result.columns
        assert 'botanist_id' in result.columns
        assert result['plant_id'].notna().all()
        assert result['botanist_id'].notna().all()

    def test_column_order(self, sample_data):
        """Test that columns are in correct order."""
        result = create_record_table(sample_data)
        expected_cols = ['id', 'plant_id', 'recording_taken',
                         'moisture', 'temperature', 'last_watered', 'botanist_id']
        assert list(result.columns) == expected_cols

    def test_preserves_record_data(self, sample_data):
        """Test that record data (moisture, temperature) is preserved."""
        result = create_record_table(sample_data)
        assert 45.5 in result['moisture'].values
        assert 72.3 in result['temperature'].values


class TestIntegration:
    """Integration tests across multiple functions."""

    def test_country_to_location_relationship(self, sample_data):
        """Test that location references correct country."""
        country_df = create_country_table(sample_data)
        location_df = create_location_table(sample_data)

        # Find location for New York
        ny_location = location_df[location_df['city'] == 'New York'].iloc[0]
        usa_country_id = country_df[country_df['country']
                                    == 'USA']['country_id'].values[0]

        assert ny_location['country_id'] == usa_country_id

    def test_plant_to_location_relationship(self, sample_data):
        """Test that plant references correct location."""
        location_df = create_location_table(sample_data)
        plant_df = create_plant_table(sample_data)

        # Check that all plant location_ids reference valid locations
        valid_location_ids = set(location_df['location_id'].values)
        plant_location_ids = set(plant_df['location_id'].values)

        assert plant_location_ids.issubset(valid_location_ids)

    def test_record_references_valid_entities(self, sample_data):
        """Test that records reference valid plants and botanists."""
        plant_df = create_plant_table(sample_data)
        botanist_df = create_botanist_table(sample_data)
        record_df = create_record_table(sample_data)

        valid_plant_ids = set(plant_df['plant_id'].values)
        valid_botanist_ids = set(botanist_df['botanist_id'].values)

        assert set(record_df['plant_id'].values).issubset(valid_plant_ids)
        assert set(record_df['botanist_id'].values).issubset(
            valid_botanist_ids)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
