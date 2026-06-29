"""Tests for the SQL safety guard."""

from __future__ import annotations

import pytest

from core.exceptions import UnsafeSQLError
from database.safe_sql import SafeSQLGuard, SQLStatementType


def test_select_allowed_in_read_only():
    guard = SafeSQLGuard(read_only=True)
    assert guard.validate("SELECT * FROM customers") == SQLStatementType.SELECT


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM customers",
        "DROP TABLE customers",
        "UPDATE customers SET name='x'",
        "TRUNCATE TABLE orders",
        "ALTER TABLE orders ADD COLUMN x INT",
        "INSERT INTO customers VALUES (9,'z','z@x.com','US')",
    ],
)
def test_write_blocked_in_read_only(sql):
    guard = SafeSQLGuard(read_only=True)
    with pytest.raises(UnsafeSQLError):
        guard.validate(sql)


def test_write_allowed_when_write_mode():
    guard = SafeSQLGuard(read_only=False)
    assert guard.validate("DELETE FROM customers WHERE id=1") == SQLStatementType.DELETE


def test_multi_statement_injection_blocked():
    guard = SafeSQLGuard(read_only=True)
    with pytest.raises(UnsafeSQLError):
        guard.validate("SELECT 1; DROP TABLE customers")


def test_comment_hidden_ddl_blocked():
    guard = SafeSQLGuard(read_only=True)
    with pytest.raises(UnsafeSQLError):
        guard.validate("SELECT 1 /* comment */; DROP TABLE x")


def test_is_write_detection():
    guard = SafeSQLGuard(read_only=True)
    assert guard.is_write("UPDATE t SET a=1") is True
    assert guard.is_write("SELECT a FROM t") is False


def test_empty_sql_rejected():
    guard = SafeSQLGuard(read_only=True)
    with pytest.raises(UnsafeSQLError):
        guard.validate("   ")
