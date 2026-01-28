"""Unit tests for transform.py"""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from transform import (
    combine_tables,
    clean_outliers,
    calculate_averages
)


@pytest.fixture
def sample_dataframes():
    """Fixture providing sample DataFrames for testing."""
    country_df = pd.DataFrame({
        'country_id': [1, 2],
        'country_name': ['USA', 'Canada']
    })

    botanist_df = pd.DataFrame({
        'botanist_id': [1, 2],
        'botanist_name': ['Alice', 'Bob']
    })

    location_df = pd.DataFrame({
        'location_id': [1, 2],
        'location_name': ['Garden A', 'Garden B'],
        'country_id': [1, 2]
    })

    plant_df = pd.DataFrame({
        'plant_id': [1, 2],
        'common_name': ['Rose', 'Tulip'],
        'scientific_name': ['Rosa', 'Tulipa']
    })

    record_df = pd.DataFrame({
        'record_id': [1, 2, 3, 4],
        'plant_id': [1, 1, 2, 2],
        'location_id': [1, 1, 2, 2],
        'botanist_id': [1, 2, 1, 2],
        'temperature': [20.5, 21.0, 18.0, 19.5],
        'moisture': [60.0, 65.0, 55.0, 58.0]
    })

    return {
        'country_df': country_df,
        'botanist_df': botanist_df,
        'location_df': location_df,
        'plant_df': plant_df,
        'record_df': record_df
    }


class TestCombineTables:
    """Tests for combine_tables function."""

    def test_combine_tables_basic(self, sample_dataframes):
        """Test that combine_tables merges all dataframes correctly."""
        result = combine_tables(
            sample_dataframes['country_df'],
            sample_dataframes['botanist_df'],
            sample_dataframes['location_df'],
            sample_dataframes['plant_df'],
            sample_dataframes['record_df']
        )

        assert len(result) == 4
        assert 'common_name' in result.columns
        assert 'botanist_name' in result.columns
        assert 'country_name' in result.columns

    def test_combine_tables_preserves_records(self, sample_dataframes):
        """Test that combining tables preserves all records."""
        result = combine_tables(
            sample_dataframes['country_df'],
            sample_dataframes['botanist_df'],
            sample_dataframes['location_df'],
            sample_dataframes['plant_df'],
            sample_dataframes['record_df']
        )

        assert len(result) == len(sample_dataframes['record_df'])

    def test_combine_tables_handles_left_join(self, sample_dataframes):
        """Test that left join handles missing values gracefully."""
        # Add a plant_id that doesn't exist in plant_df
        sample_dataframes['record_df'].loc[len(sample_dataframes['record_df'])] = {
            'record_id': 5, 'plant_id': 999, 'location_id': 1,
            'botanist_id': 1, 'temperature': 20.0, 'moisture': 60.0
        }

        result = combine_tables(
            sample_dataframes['country_df'],
            sample_dataframes['botanist_df'],
            sample_dataframes['location_df'],
            sample_dataframes['plant_df'],
            sample_dataframes['record_df']
        )

        assert len(result) == 5
        assert pd.isna(result[result['plant_id'] == 999]
                       ['common_name'].iloc[0])


class TestCleanOutliers:
    """Tests for clean_outliers function."""

    def test_clean_outliers_removes_outliers(self):
        """Test that clean_outliers removes extreme values."""
        df = pd.DataFrame({
            'plant_id': [1, 1, 1, 1, 1],
            'temperature': [20.0, 21.0, 22.0, 50.0, 19.0],
            'moisture': [60.0, 61.0, 59.0, 62.0, 58.0]
        })

        cleaned_df, outlier_counts = clean_outliers(df)

        assert len(cleaned_df) < len(df)
        assert outlier_counts[1]['temperature'] > 0

    def test_clean_outliers_returns_tuple(self):
        """Test that clean_outliers returns a tuple with dataframe and counts."""
        df = pd.DataFrame({
            'plant_id': [1, 1, 1],
            'temperature': [20.0, 21.0, 22.0],
            'moisture': [60.0, 61.0, 59.0]
        })

        result, counts = clean_outliers(df)

        assert isinstance(result, pd.DataFrame)
        assert isinstance(counts, dict)

    def test_clean_outliers_tracks_separate_counts(self):
        """Test that temperature and moisture outliers are tracked separately."""
        df = pd.DataFrame({
            'plant_id': [1, 1, 1, 1, 1],
            'temperature': [20.0, 21.0, 22.0, 100.0, 19.0],
            'moisture': [60.0, 61.0, 59.0, 62.0, -100.0]
        })

        cleaned_df, outlier_counts = clean_outliers(df)

        assert 'temperature' in outlier_counts[1]
        assert 'moisture' in outlier_counts[1]

    def test_clean_outliers_handles_multiple_plants(self):
        """Test clean_outliers processes multiple plant groups."""
        df = pd.DataFrame({
            'plant_id': [1, 1, 1, 2, 2, 2],
            'temperature': [20.0, 21.0, 22.0, 15.0, 16.0, 17.0],
            'moisture': [60.0, 61.0, 59.0, 50.0, 51.0, 49.0]
        })

        cleaned_df, outlier_counts = clean_outliers(df)

        assert 1 in outlier_counts
        assert 2 in outlier_counts


class TestCalculateAverages:
    """Tests for calculate_averages function."""

    def test_calculate_averages_computes_means(self, sample_dataframes):
        """Test that averages are computed correctly."""
        record_df = sample_dataframes['record_df']
        cleaned_df = record_df.merge(
            sample_dataframes['plant_df'], on='plant_id', how='left'
        )
        outlier_counts = {1: {'temperature': 0, 'moisture': 0},
                          2: {'temperature': 0, 'moisture': 0}}

        result = calculate_averages(cleaned_df, outlier_counts)

        assert len(result) == 2
        assert 'avg_temperature' in result.columns
        assert 'avg_moisture' in result.columns

    def test_calculate_averages_rounds_to_two_decimals(self, sample_dataframes):
        """Test that averages are rounded to 2 decimal places."""
        record_df = sample_dataframes['record_df']
        cleaned_df = record_df.merge(
            sample_dataframes['plant_df'], on='plant_id', how='left'
        )
        outlier_counts = {1: {'temperature': 0, 'moisture': 0},
                          2: {'temperature': 0, 'moisture': 0}}

        result = calculate_averages(cleaned_df, outlier_counts)

        # Check that values have at most 2 decimal places
        for temp in result['avg_temperature']:
            assert len(str(temp).split('.')[-1]) <= 2
        for moisture in result['avg_moisture']:
            assert len(str(moisture).split('.')[-1]) <= 2

    def test_calculate_averages_includes_outlier_columns(self, sample_dataframes):
        """Test that outlier count columns are included."""
        record_df = sample_dataframes['record_df']
        cleaned_df = record_df.merge(
            sample_dataframes['plant_df'], on='plant_id', how='left'
        )
        outlier_counts = {1: {'temperature': 1, 'moisture': 0},
                          2: {'temperature': 0, 'moisture': 1}}

        result = calculate_averages(cleaned_df, outlier_counts)

        assert 'temperature_outliers' in result.columns
        assert 'moisture_outliers' in result.columns

    def test_calculate_averages_includes_plant_info(self, sample_dataframes):
        """Test that plant information is preserved in output."""
        record_df = sample_dataframes['record_df']
        cleaned_df = record_df.merge(
            sample_dataframes['plant_df'], on='plant_id', how='left'
        )
        outlier_counts = {1: {'temperature': 0, 'moisture': 0},
                          2: {'temperature': 0, 'moisture': 0}}

        result = calculate_averages(cleaned_df, outlier_counts)

        assert 'plant_id' in result.columns
        assert 'common_name' in result.columns
        assert 'scientific_name' in result.columns
