"""
utils/query_engine.py
Executes LLM-generated SQL via DuckDB and optional Python snippets via Pandas.
"""
import io
import re
import traceback
import duckdb
import pandas as pd
from typing import Any


def run_sql(llm_response: dict, df: pd.DataFrame, user_question: str = "") -> dict[str, Any]:
    """
    Execute SQL from the LLM response against the in-memory DataFrame.
    Returns a unified result dict for the UI to display.

    Important:
    - SQL output is treated as the source of truth.
    - Natural-language insight is regenerated from the actual query result
      so it cannot contradict the returned table.
    """
    result = {
        "sql": llm_response.get("sql"),
        "python": llm_response.get("python"),
        "chart_hint": llm_response.get("chart_hint"),
        "chart_x": llm_response.get("chart_x"),
        "chart_y": llm_response.get("chart_y"),
        "chart_color": llm_response.get("chart_color"),
        "insight": "",
        "follow_ups": llm_response.get("follow_ups", []),
        "result_df": None,
        "error": None,
        "error_note": None,
        "chart": None,
        "type": "result",
    }

    sql = llm_response.get("sql")

    if not sql:
        result["insight"] = llm_response.get("insight", "")
        return result

    try:
        con = duckdb.connect()
        con.register("df", df)
        result_df = con.execute(sql).df()
        con.close()

        result["result_df"] = result_df
        result["insight"] = generate_grounded_insight(
            result_df=result_df,
            user_question=user_question,
            fallback_insight=llm_response.get("insight", ""),
        )

    except Exception as e:
        result["error"] = f"SQL execution failed:\n{e}"

        fixed_sql = _attempt_sql_fix(sql, str(e))
        if fixed_sql and fixed_sql != sql:
            try:
                con = duckdb.connect()
                con.register("df", df)
                result_df = con.execute(fixed_sql).df()
                con.close()

                result["result_df"] = result_df
                result["sql"] = fixed_sql
                result["error"] = None
                result["error_note"] = "Original SQL had an error; auto-corrected and re-ran."
                result["insight"] = generate_grounded_insight(
                    result_df=result_df,
                    user_question=user_question,
                    fallback_insight=llm_response.get("insight", ""),
                )
            except Exception:
                pass

    return result


def run_python_analysis(code: str, df: pd.DataFrame) -> dict[str, Any]:
    """
    Execute a sandboxed Python snippet with access to the DataFrame.
    Returns stdout output and any generated figure.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    stdout_capture = io.StringIO()
    fig = None

    local_ns = {
        "df": df.copy(),
        "pd": pd,
        "plt": plt,
        "print": lambda *args, **kwargs: stdout_capture.write(" ".join(str(a) for a in args) + "\n"),
    }

    try:
        exec(code, {"__builtins__": {}}, local_ns)  # noqa: S102
        if plt.get_fignums():
            fig = plt.gcf()
    except Exception:
        return {
            "error": f"Python execution failed:\n{traceback.format_exc(limit=3)}",
            "fig": None,
            "output": "",
        }

    return {
        "error": None,
        "fig": fig,
        "output": stdout_capture.getvalue(),
    }


def generate_grounded_insight(
    result_df: pd.DataFrame,
    user_question: str = "",
    fallback_insight: str = "",
) -> str:
    """
    Build an insight from the ACTUAL query result, not from the model's guess.
    """
    if result_df is None:
        return fallback_insight or ""

    if result_df.empty:
        return "No rows matched your query."

    rows, cols = result_df.shape

    if rows == 1 and cols == 1:
        col_name = str(result_df.columns[0])
        value = result_df.iloc[0, 0]

        if pd.isna(value):
            return "The query returned a missing value."

        if _looks_like_count_question(user_question) or _looks_like_count_column(col_name):
            return f"There are {format_value(value)} matching records."

        if _looks_like_sum_question(user_question):
            return f"The total is {format_value(value)}."

        if _looks_like_avg_question(user_question):
            return f"The average is {format_value(value)}."

        if _looks_like_min_question(user_question):
            return f"The minimum value is {format_value(value)}."

        if _looks_like_max_question(user_question):
            return f"The maximum value is {format_value(value)}."

        return f"The result is {format_value(value)}."

    if rows == 1 and cols > 1:
        row = result_df.iloc[0].to_dict()
        parts = [f"{k} = {format_value(v)}" for k, v in row.items()]
        return "Returned one row: " + ", ".join(parts) + "."

    numeric_cols = result_df.select_dtypes(include="number").columns.tolist()
    non_numeric_cols = [c for c in result_df.columns if c not in numeric_cols]

    if rows > 1 and numeric_cols:
        metric_col = numeric_cols[0]
        group_col = non_numeric_cols[0] if non_numeric_cols else result_df.columns[0]

        if metric_col == group_col and len(result_df.columns) > 1:
            group_col = result_df.columns[1]

        top_row = result_df.iloc[0]
        try:
            return (
                f"The query returned {rows} rows. "
                f"The top result is {top_row[group_col]} with {format_value(top_row[metric_col])}."
            )
        except Exception:
            pass

    return f"The query returned {rows} rows and {cols} columns."


def format_value(value: Any) -> str:
    """Human-friendly formatting for scalar values."""
    if pd.isna(value):
        return "null"

    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, int):
        return f"{value:,}"

    if isinstance(value, float):
        if value.is_integer():
            return f"{int(value):,}"
        return f"{value:,.2f}"

    if isinstance(value, pd.Timestamp):
        if value.hour == 0 and value.minute == 0 and value.second == 0:
            return value.strftime("%Y-%m-%d")
        return value.strftime("%Y-%m-%d %H:%M:%S")

    return str(value)


def _looks_like_count_question(question: str) -> bool:
    q = (question or "").lower()
    return any(p in q for p in ["how many", "count", "number of"])


def _looks_like_sum_question(question: str) -> bool:
    q = (question or "").lower()
    return any(p in q for p in ["total", "sum", "gross", "revenue"])


def _looks_like_avg_question(question: str) -> bool:
    q = (question or "").lower()
    return any(p in q for p in ["average", "avg", "mean"])


def _looks_like_min_question(question: str) -> bool:
    q = (question or "").lower()
    return any(p in q for p in ["minimum", "lowest", "smallest", "min"])


def _looks_like_max_question(question: str) -> bool:
    q = (question or "").lower()
    return any(p in q for p in ["maximum", "highest", "largest", "max"])


def _looks_like_count_column(col_name: str) -> bool:
    c = (col_name or "").lower()
    return any(token in c for token in [
        "count", "count_star", "count(*)", "cnt", "n", "num", "total_count", "row_count"
    ])


def _attempt_sql_fix(sql: str, error_msg: str) -> str | None:
    """
    Apply simple heuristic fixes for common LLM SQL mistakes.
    Returns a corrected SQL string or None.
    """
    fixed = sql

    # Normalize wrong table names
    fixed = re.sub(r"\bfrom\s+data\b", "from df", fixed, flags=re.IGNORECASE)
    fixed = re.sub(r"\bfrom\s+dataset\b", "from df", fixed, flags=re.IGNORECASE)
    fixed = re.sub(r"\bfrom\s+table\b", "from df", fixed, flags=re.IGNORECASE)
    fixed = re.sub(r"\bfrom\s+my_table\b", "from df", fixed, flags=re.IGNORECASE)
    fixed = re.sub(r"\bfrom\s+your_table\b", "from df", fixed, flags=re.IGNORECASE)

    fixed = re.sub(r"\bjoin\s+data\b", "join df", fixed, flags=re.IGNORECASE)
    fixed = re.sub(r"\bjoin\s+dataset\b", "join df", fixed, flags=re.IGNORECASE)
    fixed = re.sub(r"\bjoin\s+table\b", "join df", fixed, flags=re.IGNORECASE)
    fixed = re.sub(r"\bjoin\s+my_table\b", "join df", fixed, flags=re.IGNORECASE)
    fixed = re.sub(r"\bjoin\s+your_table\b", "join df", fixed, flags=re.IGNORECASE)

    # If this is a scalar aggregate query, ORDER BY / LIMIT should not be present
    if _is_scalar_aggregate_query(fixed):
        fixed = re.sub(r"\s+ORDER\s+BY\s+.+?(?=(\s+LIMIT\b|$))", "", fixed, flags=re.IGNORECASE)
        fixed = re.sub(r"\s+LIMIT\s+\d+\s*$", "", fixed, flags=re.IGNORECASE)

    return fixed if fixed != sql else None

def _is_scalar_aggregate_query(sql: str) -> bool:
    """
    Detect simple overall aggregate queries like:
    SELECT COUNT(*) FROM df ...
    SELECT SUM(total_gross) FROM df ...
    """
    normalized = " ".join(sql.strip().split()).lower()

    has_aggregate = bool(re.search(r"select\s+(count|sum|avg|min|max)\s*\(", normalized))
    has_group_by = " group by " in normalized

    return has_aggregate and not has_group_by
