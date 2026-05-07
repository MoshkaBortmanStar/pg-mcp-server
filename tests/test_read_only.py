import pytest
from unittest.mock import MagicMock, patch

from pg_mcp_server.config import ConnectionConfig
from pg_mcp_server.executor import _assert_read_only, run_query


@pytest.fixture
def conn():
    return ConnectionConfig(host="localhost", port=5432, dbname="test", user="test", password="test")


class TestAssertReadOnly:
    def test_begin_read_only(self):
        _assert_read_only("BEGIN READ ONLY; SELECT 1; ROLLBACK;")

    def test_begin_transaction_read_only(self):
        _assert_read_only("BEGIN TRANSACTION READ ONLY; SELECT 1; ROLLBACK;")

    def test_start_transaction_read_only(self):
        _assert_read_only("START TRANSACTION READ ONLY; SELECT 1; ROLLBACK;")

    def test_case_insensitive(self):
        _assert_read_only("begin read only; select 1; rollback;")

    def test_leading_whitespace(self):
        _assert_read_only("  \n  BEGIN READ ONLY; SELECT 1; ROLLBACK;")

    def test_bare_select_raises(self):
        with pytest.raises(ValueError, match="READ ONLY"):
            _assert_read_only("SELECT * FROM users;")

    def test_insert_raises(self):
        with pytest.raises(ValueError, match="READ ONLY"):
            _assert_read_only("INSERT INTO users VALUES (1);")

    def test_update_raises(self):
        with pytest.raises(ValueError, match="READ ONLY"):
            _assert_read_only("UPDATE users SET name = 'foo';")

    def test_delete_raises(self):
        with pytest.raises(ValueError, match="READ ONLY"):
            _assert_read_only("DELETE FROM users;")

    def test_begin_without_read_only_raises(self):
        with pytest.raises(ValueError, match="READ ONLY"):
            _assert_read_only("BEGIN; SELECT 1; COMMIT;")


class TestRunQueryReadOnlyEnforcement:
    def test_raises_without_read_only(self, conn):
        with pytest.raises(ValueError, match="READ ONLY"):
            run_query("psql", conn, "SELECT * FROM users;")

    def test_subprocess_not_called_when_validation_fails(self, conn):
        with patch("pg_mcp_server.executor.subprocess.run") as mock_run:
            with pytest.raises(ValueError):
                run_query("psql", conn, "SELECT 1;")
            mock_run.assert_not_called()

    def test_passes_with_read_only(self, conn):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "col\n1\n"
        with patch("pg_mcp_server.executor.subprocess.run", return_value=mock_result):
            result = run_query("psql", conn, "BEGIN READ ONLY; SELECT 1 AS col; ROLLBACK;")
        assert result == "col\n1"
