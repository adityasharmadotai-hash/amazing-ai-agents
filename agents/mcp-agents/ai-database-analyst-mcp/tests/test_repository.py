"""Tests for the repository, schema inspector and query service."""

from __future__ import annotations

import pytest

from core.exceptions import UnsafeSQLError
from services.query_service import QueryService


def test_execute_select(repository):
    result = repository.execute("SELECT name FROM customers ORDER BY id")
    assert result.success
    assert result.columns == ["name"]
    assert result.row_count == 3
    assert result.rows[0][0] == "Alice"


def test_execute_with_params(repository):
    result = repository.execute(
        "SELECT name FROM customers WHERE country = :c", {"c": "USA"}
    )
    assert result.row_count == 2


def test_write_blocked(repository):
    with pytest.raises(UnsafeSQLError):
        repository.execute("DELETE FROM customers")


def test_schema_inspection(repository):
    schema = repository.get_schema(include_row_counts=True)
    names = schema.table_names()
    assert "customers" in names and "orders" in names
    customers = schema.get_table("customers")
    assert customers.row_count == 3
    assert "email" in customers.column_names()


def test_find_tables_with_column(repository):
    schema = repository.get_schema(include_row_counts=False)
    matches = repository.find_tables_with_column(schema, "email")
    assert "customers.email" in matches


def test_relationships(repository):
    schema = repository.get_schema(include_row_counts=False)
    rels = QueryService(repository).relationships(schema)
    assert any(r["to_table"] == "customers" for r in rels)


def test_statistics(repository):
    stats = QueryService(repository).statistics("orders")
    assert stats["row_sample"] == 4
    assert "amount" in stats["columns"]
    assert stats["columns"]["amount"]["max"] == 100.0


def test_explain(repository):
    plan = repository.explain("SELECT * FROM customers")
    assert plan.success
