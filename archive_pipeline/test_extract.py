"""
Tests for extract.py script.
"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import pymssql
from extract import get_db_connection, extract_table_data, extract_all_data, main


class TestGetDbConnection:
    """Tests for get_db_connection function."""

    @patch('extract.load_dotenv')
    @patch('extract.os.getenv')
    @patch('extract.pymssql.connect')
    def test_get_db_connection_success(self, mock_connect, mock_getenv, mock_load_dotenv):
        """Test successful database connection with environment variables."""
        mock_getenv.side_effect = lambda key, default=None: {
            'DB_HOST': 'localhost',
            'DB_PORT': '1433',
            'DB_NAME': 'test_db',
            'DB_USER': 'test_user',
            'DB_PASSWORD': 'test_password'
        }.get(key, default)

        mock_conn = Mock(spec=pymssql.Connection)
        mock_connect.return_value = mock_conn

        result = get_db_connection()

        mock_load_dotenv.assert_called_once()
        mock_connect.assert_called_once_with(
            server='localhost',
            port='1433',
            user='test_user',
            password='test_password',
            database='test_db'
        )
        assert result == mock_conn

    @patch('extract.load_dotenv')
    @patch('extract.os.getenv')
    @patch('extract.pymssql.connect')
    def test_get_db_connection_with_default_port(self, mock_connect, mock_getenv, mock_load_dotenv):
        """Test connection uses default port when not specified."""
        mock_getenv.side_effect = lambda key, default=None: {
            'DB_HOST': 'localhost',
            'DB_NAME': 'test_db',
            'DB_USER': 'test_user',
            'DB_PASSWORD': 'test_password'
        }.get(key, default)

        mock_conn = Mock(spec=pymssql.Connection)
        mock_connect.return_value = mock_conn

        result = get_db_connection()

        assert mock_connect.call_args[1]['port'] == '1433'

    @patch('extract.load_dotenv')
    @patch('extract.os.getenv')
    @patch('extract.pymssql.connect')
    def test_get_db_connection_failure(self, mock_connect, mock_getenv, mock_load_dotenv):
        """Test database connection failure raises exception."""
        mock_getenv.side_effect = lambda key, default=None: {
            'DB_HOST': 'localhost',
            'DB_PORT': '1433',
            'DB_NAME': 'test_db',
            'DB_USER': 'test_user',
            'DB_PASSWORD': 'test_password'
        }.get(key, default)

        mock_connect.side_effect = pymssql.OperationalError(
            "Connection failed")

        with pytest.raises(pymssql.OperationalError):
            get_db_connection()


class TestExtractTableData:
    """Tests for extract_table_data function."""

    def test_extract_table_data_success(self):
        """Test successful extraction of table data."""
        mock_conn = Mock(spec=pymssql.Connection)
        expected_df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Plant A', 'Plant B', 'Plant C']
        })

        with patch('extract.pd.read_sql', return_value=expected_df) as mock_read_sql:
            result = extract_table_data(mock_conn, 'Plant')

            mock_read_sql.assert_called_once_with(
                "SELECT * FROM Plant", mock_conn)
            pd.testing.assert_frame_equal(result, expected_df)

    def test_extract_table_data_empty_table(self):
        """Test extraction from empty table returns empty DataFrame."""
        mock_conn = Mock(spec=pymssql.Connection)
        empty_df = pd.DataFrame()

        with patch('extract.pd.read_sql', return_value=empty_df):
            result = extract_table_data(mock_conn, 'EmptyTable')

            assert result.empty
            assert isinstance(result, pd.DataFrame)

    def test_extract_table_data_sql_error(self):
        """Test extraction handles SQL errors."""
        mock_conn = Mock(spec=pymssql.Connection)

        with patch('extract.pd.read_sql', side_effect=pymssql.ProgrammingError("Invalid table")):
            with pytest.raises(pymssql.ProgrammingError):
                extract_table_data(mock_conn, 'InvalidTable')


class TestExtractAllData:
    """Tests for extract_all_data function."""

    @patch('extract.extract_table_data')
    def test_extract_all_data_success(self, mock_extract_table):
        """Test successful extraction of all tables."""
        mock_conn = Mock(spec=pymssql.Connection)

        mock_dfs = {
            'Country': pd.DataFrame({'country_id': [1], 'country': ['UK']}),
            'Location': pd.DataFrame({'location_id': [1], 'city': ['Liverpool']}),
            'Plant': pd.DataFrame({'plant_id': [1], 'common_name': ['Rose']}),
            'Botanist': pd.DataFrame({'botanist_id': [1], 'botanist_name': ['John']}),
            'Record': pd.DataFrame({'record_id': [1], 'moisture': [50.0]})
        }

        mock_extract_table.side_effect = lambda conn, table: mock_dfs[table]

        result = extract_all_data(mock_conn)

        assert len(result) == 5
        assert set(result.keys()) == {
            'Country', 'Location', 'Plant', 'Botanist', 'Record'}
        assert mock_extract_table.call_count == 5

        for table_name, df in result.items():
            pd.testing.assert_frame_equal(df, mock_dfs[table_name])

    @patch('extract.extract_table_data')
    @patch('builtins.print')
    def test_extract_all_data_prints_progress(self, mock_print, mock_extract_table):
        """Test that progress is printed during extraction."""
        mock_conn = Mock(spec=pymssql.Connection)
        mock_df = pd.DataFrame({'id': [1, 2, 3]})
        mock_extract_table.return_value = mock_df

        extract_all_data(mock_conn)

        assert mock_print.call_count >= 10
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any('Extracting data from' in str(call) for call in print_calls)
        assert any('Extracted' in str(call) and 'rows' in str(call)
                   for call in print_calls)


class TestMain:
    """Tests for main function."""

    @patch('extract.get_db_connection')
    @patch('extract.extract_all_data')
    @patch('builtins.print')
    def test_main_success(self, mock_print, mock_extract_all, mock_get_conn):
        """Test successful execution of main function."""
        mock_conn = MagicMock(spec=pymssql.Connection)
        mock_get_conn.return_value = mock_conn

        expected_data = {
            'Country': pd.DataFrame({'country_id': [1], 'country': ['UK']}),
            'Plant': pd.DataFrame({'plant_id': [1], 'common_name': ['Rose']})
        }
        mock_extract_all.return_value = expected_data

        result = main()

        mock_get_conn.assert_called_once()
        mock_extract_all.assert_called_once_with(mock_conn)
        mock_conn.close.assert_called_once()
        assert result == expected_data

    @patch('extract.get_db_connection')
    @patch('extract.extract_all_data')
    def test_main_closes_connection_on_error(self, mock_extract_all, mock_get_conn):
        """Test that connection is closed even when extraction fails."""
        mock_conn = MagicMock(spec=pymssql.Connection)
        mock_get_conn.return_value = mock_conn
        mock_extract_all.side_effect = Exception("Extraction error")

        with pytest.raises(Exception):
            main()

        mock_conn.close.assert_called_once()

    @patch('extract.get_db_connection')
    @patch('extract.extract_all_data')
    @patch('builtins.print')
    def test_main_prints_summary(self, mock_print, mock_extract_all, mock_get_conn):
        """Test that main prints extraction summary."""
        mock_conn = MagicMock(spec=pymssql.Connection)
        mock_get_conn.return_value = mock_conn

        test_data = {
            'Country': pd.DataFrame({'id': [1, 2], 'name': ['A', 'B']}),
            'Plant': pd.DataFrame({'id': [1, 2, 3], 'name': ['X', 'Y', 'Z']})
        }
        mock_extract_all.return_value = test_data

        main()

        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any('Connecting to database' in str(call)
                   for call in print_calls)
        assert any('Extraction Summary' in str(call) for call in print_calls)
        assert any('Country' in str(call) and '2 rows' in str(call)
                   for call in print_calls)
        assert any('Plant' in str(call) and '3 rows' in str(call)
                   for call in print_calls)


class TestIntegration:
    """Integration tests for the extract module."""

    @patch('extract.load_dotenv')
    @patch('extract.os.getenv')
    @patch('extract.pymssql.connect')
    @patch('extract.pd.read_sql')
    def test_full_extraction_workflow(self, mock_read_sql, mock_connect, mock_getenv, mock_load_dotenv):
        """Test complete extraction workflow from connection to data retrieval."""
        mock_getenv.side_effect = lambda key, default=None: {
            'DB_HOST': 'localhost',
            'DB_PORT': '1433',
            'DB_NAME': 'test_db',
            'DB_USER': 'test_user',
            'DB_PASSWORD': 'test_password'
        }.get(key, default)

        mock_conn = MagicMock(spec=pymssql.Connection)
        mock_connect.return_value = mock_conn

        test_dfs = [
            pd.DataFrame({'country_id': [1], 'country': ['UK']}),
            pd.DataFrame({'location_id': [1], 'city': ['Liverpool']}),
            pd.DataFrame({'plant_id': [1], 'common_name': ['Rose']}),
            pd.DataFrame({'botanist_id': [1], 'botanist_name': ['John']}),
            pd.DataFrame({'record_id': [1], 'moisture': [50.0]})
        ]
        mock_read_sql.side_effect = test_dfs

        result = main()

        assert len(result) == 5
        assert 'Country' in result
        assert 'Plant' in result
        assert len(result['Country']) == 1
        assert len(result['Plant']) == 1
        mock_conn.close.assert_called_once()
