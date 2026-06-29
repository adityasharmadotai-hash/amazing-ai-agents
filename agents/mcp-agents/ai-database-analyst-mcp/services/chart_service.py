"""Chart service.

Automatically determines the best chart for a result set and builds an
interactive Plotly figure. Supports bar, line, pie, scatter, area, histogram
and heatmap charts.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from core.logging_config import get_logger
from core.models import ChartSpec, ChartType, QueryResult

logger = get_logger(__name__)


class ChartService:
    """Builds Plotly charts and recommends chart types heuristically."""

    def __init__(self, theme: str = "plotly_dark") -> None:
        self.theme = theme

    def set_theme(self, theme: str) -> None:
        self.theme = theme

    # --- DataFrame helpers ------------------------------------------------
    @staticmethod
    def to_dataframe(result: QueryResult) -> pd.DataFrame:
        return pd.DataFrame(result.rows, columns=result.columns)

    @staticmethod
    def _numeric_columns(df: pd.DataFrame) -> list[str]:
        return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    @staticmethod
    def _datetime_columns(df: pd.DataFrame) -> list[str]:
        cols = []
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]):
                cols.append(c)
            elif df[c].dtype == object:
                # Try to detect date-like strings.
                sample = df[c].dropna().head(5)
                if len(sample) and all(_looks_like_date(str(v)) for v in sample):
                    cols.append(c)
        return cols

    @staticmethod
    def _categorical_columns(df: pd.DataFrame, numeric: list[str]) -> list[str]:
        return [c for c in df.columns if c not in numeric]

    # --- Recommendation ---------------------------------------------------
    def recommend(self, result: QueryResult) -> ChartSpec:
        """Heuristically choose the most suitable chart for a result set."""
        df = self.to_dataframe(result)
        if df.empty or len(df.columns) < 1:
            return ChartSpec(chart_type=ChartType.TABLE, title="Results", reason="No data to plot.")

        numeric = self._numeric_columns(df)
        datetimes = self._datetime_columns(df)
        categorical = self._categorical_columns(df, numeric)

        n_rows = len(df)

        # Time series -> line chart.
        if datetimes and numeric:
            return ChartSpec(
                chart_type=ChartType.LINE,
                x=datetimes[0],
                y=numeric[: min(3, len(numeric))],
                title="Trend over time",
                reason="A datetime column with numeric measures suggests a time series.",
            )

        # Single numeric column -> histogram.
        if len(df.columns) == 1 and numeric:
            return ChartSpec(
                chart_type=ChartType.HISTOGRAM,
                x=numeric[0],
                title=f"Distribution of {numeric[0]}",
                reason="A single numeric column is best shown as a distribution.",
            )

        # Two numeric columns -> scatter.
        if len(numeric) >= 2 and not categorical:
            return ChartSpec(
                chart_type=ChartType.SCATTER,
                x=numeric[0],
                y=[numeric[1]],
                title=f"{numeric[1]} vs {numeric[0]}",
                reason="Two numeric columns are well suited to a scatter plot.",
            )

        # One category + one numeric -> pie (few rows) or bar.
        if categorical and numeric:
            cat = categorical[0]
            if n_rows <= 8:
                return ChartSpec(
                    chart_type=ChartType.PIE,
                    x=cat,
                    y=[numeric[0]],
                    title=f"{numeric[0]} by {cat}",
                    reason="A small number of categories is readable as a pie chart.",
                )
            return ChartSpec(
                chart_type=ChartType.BAR,
                x=cat,
                y=numeric[: min(3, len(numeric))],
                color=categorical[1] if len(categorical) > 1 else None,
                title=f"{numeric[0]} by {cat}",
                reason="A categorical dimension with numeric measures fits a bar chart.",
            )

        return ChartSpec(chart_type=ChartType.TABLE, title="Results", reason="No obvious chart; showing table.")

    # --- Figure construction ---------------------------------------------
    def build_figure(self, result: QueryResult, spec: Optional[ChartSpec] = None) -> Optional[go.Figure]:
        """Construct a Plotly figure for the given result and spec."""
        df = self.to_dataframe(result)
        if df.empty:
            return None

        spec = spec or self.recommend(result)
        # Coerce detected datetime columns.
        for c in self._datetime_columns(df):
            try:
                df[c] = pd.to_datetime(df[c], errors="coerce")
            except (ValueError, TypeError):
                pass

        try:
            fig = self._dispatch(df, spec)
        except (ValueError, KeyError, TypeError) as exc:
            logger.warning("Chart build failed (%s); falling back to bar", exc)
            fig = self._fallback_bar(df)

        if fig is not None:
            fig.update_layout(
                template=self.theme,
                title=spec.title,
                margin=dict(l=40, r=20, t=50, b=40),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
        return fig

    def _dispatch(self, df: pd.DataFrame, spec: ChartSpec) -> Optional[go.Figure]:
        ct = spec.chart_type
        x = spec.x or (df.columns[0] if len(df.columns) else None)
        y = spec.y or [c for c in df.columns if c != x][:1]

        if ct == ChartType.BAR:
            return px.bar(df, x=x, y=y, color=spec.color, barmode="group")
        if ct == ChartType.LINE:
            return px.line(df, x=x, y=y, color=spec.color, markers=True)
        if ct == ChartType.AREA:
            return px.area(df, x=x, y=y, color=spec.color)
        if ct == ChartType.PIE:
            values = y[0] if y else None
            return px.pie(df, names=x, values=values)
        if ct == ChartType.SCATTER:
            return px.scatter(df, x=x, y=y[0] if y else None, color=spec.color)
        if ct == ChartType.HISTOGRAM:
            return px.histogram(df, x=x or (y[0] if y else None))
        if ct == ChartType.HEATMAP:
            numeric = self._numeric_columns(df)
            if len(numeric) >= 2:
                corr = df[numeric].corr()
                return px.imshow(corr, text_auto=True, aspect="auto", title="Correlation")
            return self._fallback_bar(df)
        # TABLE or anything else -> no figure.
        return None

    def _fallback_bar(self, df: pd.DataFrame) -> Optional[go.Figure]:
        numeric = self._numeric_columns(df)
        if not numeric:
            return None
        x = next((c for c in df.columns if c not in numeric), df.columns[0])
        return px.bar(df, x=x, y=numeric[: min(3, len(numeric))], barmode="group")


def _looks_like_date(value: str) -> bool:
    """Cheap heuristic for date-like strings (avoids heavy parsing)."""
    if not value or len(value) < 6:
        return False
    digits = sum(ch.isdigit() for ch in value)
    seps = sum(ch in "-/:" for ch in value)
    return digits >= 4 and seps >= 1
