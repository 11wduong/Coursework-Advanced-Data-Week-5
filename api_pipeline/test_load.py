"""Test suite for the load script."""

from unittest.mock import patch, MagicMock
import pandas as pd
import pytest
from load import (
    _build_insert_query,
    _dataframe_to_tuples,
    load_master_table,
    load_country_table,
    load_botanist_table,
    load_location_table,
    load_plant_table,
    load_record_table,
    check_master_data_exists,
    get_country_lookup,
    get_location_lookup,
    get_botanist_lookup
)


class TestBuildInsertQuery:
    """Tests for the _build_insert_query function."""

    def test_build_insert_query_single_column(self):
        """Test building query with single column."""
        result = _build_insert_query('Country', ['country'])
        assert result == "INSERT INTO Country (country) VALUES (?)"

    def test_build_insert_query_multiple_columns(self):
        """Test building query with multiple columns."""
        result = _build_insert_query('Botanist', ['name', 'email', 'phone'])
        assert result == "INSERT INTO Botanist (name, email, phone) VALUES (?, ?, ?)"

    def test_build_insert_query_empty_columns(self):
        """Test building query with empty column list."""
        result = _build_insert_query('Test', [])
        assert result == "INSERT INTO Test () VALUES ()"


class TestDataframeToTuples:
    """Tests for the _dataframe_to_tuples function."""

    def test_dataframe_to_tuples_single_row(self):
        """Test converting single row dataframe to tuples."""
        df = pd.DataFrame({'col1': [1], 'col2': ['a']})
        result = _dataframe_to_tuples(df)
        assert result == [(1, 'a')]

    def test_dataframe_to_tuples_multiple_rows(self):
        """Test converting multiple row dataframe to tuples."""
        df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
        result = _dataframe_to_tuples(df)
        assert result == [(1, 'a'), (2, 'b'), (3, 'c')]

    def test_dataframe_to_tuples_empty_dataframe(self):
        """Test converting empty dataframe to tuples."""
        df = pd.DataFrame({'col1': [], 'col2': []})
        result = _dataframe_to_tuples(df)
        assert result == []


class TestLoadMasterTable:
    """Tests for the load_master_table function."""

    def test_load_master_table_calls_executemany(self):
        """Test that load_master_table calls executemany with correct args."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        df = pd.DataFrame({'country_id': [1, 2], 'country': ['UK', 'USA']})
        load_master_table(df, 'Country', mock_conn)

        mock_cursor.executemany.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_load_master_table_correct_query(self):
        """Test that load_master_table builds correct query."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        df = pd.DataFrame({'id': [1], 'name': ['Test']})
        load_master_table(df, 'TestTable', mock_conn)

        call_args = mock_cursor.executemany.call_args
        query = call_args[0][0]
        assert "INSERT INTO TestTable" in query
        assert "(id, name)" in query


class TestLoadCountryTable:
    """Tests for the load_country_table function."""

    @patch('load.load_master_table')
    def test_load_country_table_calls_master(self, mock_load_master):
        """Test that load_country_table calls load_master_table correctly."""
        mock_conn = MagicMock()
        df = pd.DataFrame({'country': ['UK']})

        load_country_table(df, mock_conn)

        mock_load_master.assert_called_once_with(df, 'Country', mock_conn)


class TestLoadBotanistTable:
    """Tests for the load_botanist_table function."""

    @patch('load.load_master_table')
    def test_load_botanist_table_calls_master(self, mock_load_master):
        """Test that load_botanist_table calls load_master_table correctly."""
        mock_conn = MagicMock()
        df = pd.DataFrame({
            'botanist_name': ['John'],
            'email': ['john@test.com'],
            'phone': ['123456']
        })

        load_botanist_table(df, mock_conn)

        mock_load_master.assert_called_once_with(df, 'Botanist', mock_conn)


class TestLoadLocationTable:
    """Tests for the load_location_table function."""

    @patch('load.get_country_lookup')
    @patch('load.load_master_table')
    def test_load_location_table_calls_master(self, mock_load_master, mock_lookup):
        """Test that load_location_table calls load_master_table with FK resolved."""
        mock_conn = MagicMock()
        mock_lookup.return_value = pd.DataFrame({
            'country_id': [1],
            'country': ['UK']
        })
        df = pd.DataFrame({
            'city': ['London'],
            'lat': [51.5],
            'long': [-0.1],
            'country': ['UK']
        })

        load_location_table(df, mock_conn)

        mock_load_master.assert_called_once()
        call_df = mock_load_master.call_args[0][0]
        assert list(call_df.columns) == ['city', 'lat', 'long', 'country_id']


class TestLoadPlantTable:
    """Tests for the load_plant_table function."""

    @patch('load.get_location_lookup')
    @patch('load.load_master_table')
    def test_load_plant_table_calls_master(self, mock_load_master, mock_lookup):
        """Test that load_plant_table calls load_master_table with FK resolved."""
        mock_conn = MagicMock()
        mock_lookup.return_value = pd.DataFrame({
            'location_id': [1],
            'city': ['London']
        })
        df = pd.DataFrame({
            'plant_id': [1],
            'scientific_name': ['Rosa'],
            'common_name': ['Rose'],
            'city': ['London']
        })

        load_plant_table(df, mock_conn)

        mock_load_master.assert_called_once()
        call_df = mock_load_master.call_args[0][0]
        assert list(call_df.columns) == [
            'plant_id', 'scientific_name', 'common_name', 'location_id']


class TestLoadRecordTable:
    """Tests for the load_record_table function."""

    @patch('load.get_botanist_lookup')
    def test_load_record_table_returns_count(self, mock_botanist):
        """Test that load_record_table returns correct row count."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_botanist.return_value = pd.DataFrame({
            'botanist_id': [1],
            'botanist_name': ['Alice']
        })

        df = pd.DataFrame({
            'plant_id': [1, 2, 3],
            'botanist_name': ['Alice', 'Alice', 'Alice'],
            'recording_taken': ['2024-01-01', '2024-01-01', '2024-01-01'],
            'moisture': [10.0, 20.0, 30.0],
            'temperature': [20.0, 21.0, 22.0],
            'last_watered': ['2024-01-01', '2024-01-01', '2024-01-01']
        })

        result = load_record_table(df, mock_conn)

        assert result == 3

    @patch('load.get_botanist_lookup')
    def test_load_record_table_commits_data(self, mock_botanist):
        """Test that load_record_table commits transaction."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_botanist.return_value = pd.DataFrame({
            'botanist_id': [1],
            'botanist_name': ['Alice']
        })

        df = pd.DataFrame({
            'plant_id': [1],
            'botanist_name': ['Alice'],
            'recording_taken': ['2024-01-01'],
            'moisture': [10.0],
            'temperature': [20.0],
            'last_watered': ['2024-01-01']
        })

        load_record_table(df, mock_conn)

        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_load_record_table_empty_df_returns_zero(self):
        """Test that empty dataframe returns 0."""
        mock_conn = MagicMock()
        df = pd.DataFrame({
            'plant_id': [],
            'botanist_name': [],
            'recording_taken': [],
            'moisture': [],
            'temperature': [],
            'last_watered': []
        })

        result = load_record_table(df, mock_conn)

        assert result == 0

    @patch('load.get_botanist_lookup')
    def test_load_record_table_drops_unmatched_botanist(self, mock_botanist):
        """Test that rows without matching botanist are dropped."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_botanist.return_value = pd.DataFrame({
            'botanist_id': [1],
            'botanist_name': ['Alice']
        })

        df = pd.DataFrame({
            'plant_id': [1, 2],
            'botanist_name': ['Alice', 'Unknown'],
            'recording_taken': ['2024-01-01', '2024-01-01'],
            'moisture': [10.0, 20.0],
            'temperature': [20.0, 21.0],
            'last_watered': ['2024-01-01', '2024-01-01']
        })

        result = load_record_table(df, mock_conn)

        assert result == 1


class TestCheckMasterDataExists:
    """Tests for the check_master_data_exists function."""

    def test_check_master_data_exists_returns_true_when_all_have_data(self):
        """Test returns True when all tables have data."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [5]

        result = check_master_data_exists(mock_conn)

        assert result is True
        assert mock_cursor.execute.call_count == 4

    def test_check_master_data_exists_returns_false_when_any_empty(self):
        """Test returns False when any table is empty."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.side_effect = [[5], [5], [0], [5]]

        result = check_master_data_exists(mock_conn)

        assert result is False

    def test_check_master_data_exists_closes_cursor(self):
        """Test that cursor is closed after check."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [5]

        check_master_data_exists(mock_conn)

        mock_cursor.close.assert_called_once()


class TestGetCountryLookup:
    """Tests for get_country_lookup function."""

    def test_returns_dataframe_with_correct_columns(self):
        """Test that lookup returns correct columns."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [(1, 'UK'), (2, 'USA')]

        result = get_country_lookup(mock_conn)

        assert list(result.columns) == ['country_id', 'country']
        assert len(result) == 2


class TestGetLocationLookup:
    """Tests for get_location_lookup function."""

    def test_returns_dataframe_with_correct_columns(self):
        """Test that lookup returns correct columns."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [(1, 'London'), (2, 'Paris')]

        result = get_location_lookup(mock_conn)

        assert list(result.columns) == ['location_id', 'city']
        assert len(result) == 2


class TestGetBotanistLookup:
    """Tests for get_botanist_lookup function."""

    def test_returns_dataframe_with_correct_columns(self):
        """Test that lookup returns correct columns."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [(1, 'Alice'), (2, 'Bob')]

        result = get_botanist_lookup(mock_conn)

        assert list(result.columns) == ['botanist_id', 'botanist_name']
        assert len(result) == 2


class TestGetDbConnection:
    """Tests for the get_db_connection function."""

    @patch('load.pyodbc.connect')
    @patch.dict('os.environ', {
        'DB_HOST': 'localhost',
        'DB_PORT': '1433',
        'DB_NAME': 'testdb',
        'DB_USER': 'user',
        'DB_PASSWORD': 'pass'
    }, clear=False)
    def test_get_db_connection_builds_correct_string(self, mock_connect):
        """Test that connection string is built correctly."""
        from load import get_db_connection

        get_db_connection()

        mock_connect.assert_called_once()
        call_args = mock_connect.call_args[0][0]
        assert 'DRIVER={ODBC Driver 18 for SQL Server}' in call_args
        assert 'SERVER=localhost' in call_args
        assert 'PORT=1433' in call_args
        assert 'DATABASE=testdb' in call_args
        assert 'UID=user' in call_args
        assert 'PWD=pass' in call_args
