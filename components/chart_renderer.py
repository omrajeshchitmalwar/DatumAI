"""
components/chart_renderer.py
Generates Plotly figures from query results based on LLM chart hints.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional

PLOTLY_TEMPLATE = "plotly_white"
COLOR_SEQUENCE = px.colors.qualitative.Set2


def render_chart(
    df: Optional[pd.DataFrame],
    chart_hint: str,
    question: str = "",
    x: Optional[str] = None,
    y: Optional[str] = None,
    color: Optional[str] = None,
) -> Optional[go.Figure]:
    """
    Route to the correct chart type based on the LLM's hint.
    Falls back to a sensible default if columns are ambiguous.
    """
    if df is None or df.empty:
        return None

    # Auto-detect columns if not provided
    x, y = _resolve_columns(df, x, y, chart_hint)
    if x is None:
        return None

    chart_hint = (chart_hint or "bar").lower()

    try:
        if chart_hint == "bar":
            fig = px.bar(
                df, x=x, y=y, color=color,
                template=PLOTLY_TEMPLATE,
                color_discrete_sequence=COLOR_SEQUENCE,
                title=_title(question),
            )
        elif chart_hint == "line":
            fig = px.line(
                df, x=x, y=y, color=color,
                template=PLOTLY_TEMPLATE,
                markers=True,
                title=_title(question),
            )
        elif chart_hint == "scatter":
            fig = px.scatter(
                df, x=x, y=y, color=color,
                template=PLOTLY_TEMPLATE,
                color_discrete_sequence=COLOR_SEQUENCE,
                title=_title(question),
            )
        elif chart_hint == "pie":
            fig = px.pie(
                df, names=x, values=y,
                template=PLOTLY_TEMPLATE,
                color_discrete_sequence=COLOR_SEQUENCE,
                title=_title(question),
            )
        elif chart_hint == "histogram":
            fig = px.histogram(
                df, x=x, color=color,
                template=PLOTLY_TEMPLATE,
                color_discrete_sequence=COLOR_SEQUENCE,
                title=_title(question),
            )
        elif chart_hint == "box":
            fig = px.box(
                df, x=color or x, y=y,
                template=PLOTLY_TEMPLATE,
                color_discrete_sequence=COLOR_SEQUENCE,
                title=_title(question),
            )
        elif chart_hint == "heatmap":
            numeric_df = df.select_dtypes(include="number")
            corr = numeric_df.corr()
            fig = px.imshow(
                corr,
                text_auto=".2f",
                template=PLOTLY_TEMPLATE,
                color_continuous_scale="RdBu_r",
                title=_title(question) or "Correlation heatmap",
            )
        else:
            # Default fallback
            fig = px.bar(df, x=x, y=y, template=PLOTLY_TEMPLATE, title=_title(question))

        fig.update_layout(
            margin=dict(t=50, l=30, r=10, b=30),
            font_family="sans-serif",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        return fig

    except Exception:
        return None


def _resolve_columns(
    df: pd.DataFrame,
    x: Optional[str],
    y: Optional[str],
    chart_hint: str,
) -> tuple[Optional[str], Optional[str]]:
    """Infer sensible x/y columns when LLM didn't specify them."""
    cols = df.columns.tolist()
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(exclude="number").columns.tolist()

    # Validate provided columns exist in df
    if x and x not in cols:
        x = None
    if y and y not in cols:
        y = None

    if chart_hint == "histogram":
        x = x or (numeric_cols[0] if numeric_cols else cols[0])
        return x, y

    if chart_hint == "heatmap":
        return numeric_cols[0] if numeric_cols else cols[0], None

    if x is None:
        x = cat_cols[0] if cat_cols else cols[0]
    if y is None and numeric_cols:
        y = numeric_cols[0] if numeric_cols[0] != x else (numeric_cols[1] if len(numeric_cols) > 1 else None)

    return x, y


def _title(question: str) -> str:
    """Trim question to a reasonable chart title length."""
    if not question:
        return ""
    return question[:80] + ("…" if len(question) > 80 else "")
