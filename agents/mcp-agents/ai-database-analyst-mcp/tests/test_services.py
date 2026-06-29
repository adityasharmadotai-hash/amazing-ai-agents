"""Tests for chart, export and optimisation services."""

from __future__ import annotations

from core.models import ChartType, QueryResult
from services.chart_service import ChartService
from services.export_service import ExportService
from services.optimization_service import OptimizationService


def _sample_result() -> QueryResult:
    return QueryResult(
        sql="SELECT country, total FROM t",
        columns=["country", "total"],
        rows=[["USA", 150.0], ["UK", 75.0]],
        row_count=2,
    )


def test_chart_recommendation_bar_or_pie():
    svc = ChartService(theme="plotly")
    spec = svc.recommend(_sample_result())
    assert spec.chart_type in (ChartType.PIE, ChartType.BAR)


def test_chart_build_figure():
    svc = ChartService(theme="plotly")
    fig = svc.build_figure(_sample_result())
    assert fig is not None


def test_export_csv_and_json():
    svc = ExportService(export_dir="exports")
    csv_bytes = svc.to_csv(_sample_result(), persist=False)
    assert b"country" in csv_bytes
    json_bytes = svc.to_json(_sample_result(), persist=False)
    assert b"rows" in json_bytes


def test_export_excel():
    svc = ExportService(export_dir="exports")
    data = svc.to_excel(_sample_result(), persist=False)
    assert data[:2] == b"PK"  # xlsx is a zip archive


def test_export_pdf():
    svc = ExportService(export_dir="exports")
    data = svc.to_pdf("Report", "## Executive Summary\nHello.", result=_sample_result(), persist=False)
    assert data[:4] == b"%PDF"


def test_optimization_select_star(repository):
    svc = OptimizationService(repository)
    schema = repository.get_schema(include_row_counts=False)
    report = svc.analyze("SELECT * FROM customers WHERE country = 'USA'", schema)
    assert any("SELECT *" in s for s in report.suggestions)


def test_optimization_missing_index(repository):
    svc = OptimizationService(repository)
    schema = repository.get_schema(include_row_counts=False)
    report = svc.analyze("SELECT * FROM customers WHERE country = 'USA'", schema)
    assert any("country" in idx for idx in report.missing_indexes)
