"""
utils/data_loader.py
Handles file parsing and schema extraction for uploaded datasets.
"""
from __future__ import annotations

import pandas as pd
from typing import Optional


def normalize_column_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def clean_string_series(s: pd.Series) -> pd.Series:
    """
    Normalize whitespace for object/string columns without destroying nulls.
    """
    if not (pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s)):
        return s
    s = s.astype("string").str.strip()
    return s.replace({"": pd.NA, "null": pd.NA, "none": pd.NA, "nan": pd.NA, "na": pd.NA})


def try_parse_numeric(s: pd.Series) -> pd.Series:
    """
    Try converting a string-like series to numeric by removing common formatting.
    Examples:
      '4,337' -> 4337
      '$594,254,460' -> 594254460
      '12.5%' -> 12.5
    """
    if not (pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s)):
        return s

    cleaned = s.astype("string").str.strip()

    # Remove common numeric formatting
    cleaned = cleaned.str.replace(",", "", regex=False)
    cleaned = cleaned.str.replace("$", "", regex=False)
    cleaned = cleaned.str.replace("%", "", regex=False)

    numeric = pd.to_numeric(cleaned, errors="coerce")

    # Only adopt numeric conversion if most non-null values succeeded
    original_non_null = s.notna().sum()
    converted_non_null = numeric.notna().sum()

    if original_non_null > 0 and converted_non_null / original_non_null >= 0.85:
        # Prefer Int64 if all parsed numbers are whole numbers
        if (numeric.dropna() % 1 == 0).all():
            return numeric.astype("Int64")
        return numeric

    return s


def try_parse_datetime(s: pd.Series) -> pd.Series:
    """
    Try converting a string-like series to datetime.
    """
    if not (pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s)):
        return s

    parsed = pd.to_datetime(s, errors="coerce")

    original_non_null = s.notna().sum()
    converted_non_null = parsed.notna().sum()

    # Only adopt if most values look like valid dates
    if original_non_null > 0 and converted_non_null / original_non_null >= 0.85:
        return parsed

    return s


def try_parse_boolean(s: pd.Series) -> pd.Series:
    """
    Try converting common text booleans to boolean dtype.
    """
    if not (pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s)):
        return s

    lowered = s.astype("string").str.strip().str.lower()
    valid = {"true": True, "false": False, "yes": True, "no": False, "1": True, "0": False}

    non_null = lowered.dropna()
    if len(non_null) == 0:
        return s

    if non_null.isin(valid.keys()).mean() >= 0.95:
        return lowered.map(valid).astype("boolean")

    return s


def infer_column_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Second-pass semantic type inference for uploaded data.
    Useful when CSV/Excel import leaves formatted numbers/dates as strings.
    """
    df = df.copy()

    for col in df.columns:
        s = df[col]

        # normalize strings first
        s = clean_string_series(s)

        # only try inference on text-like columns
        if pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s):
            s_bool = try_parse_boolean(s)
            if not s_bool.equals(s):
                df[col] = s_bool
                continue

            s_num = try_parse_numeric(s)
            if not s_num.equals(s):
                df[col] = s_num
                continue

            s_dt = try_parse_datetime(s)
            if not s_dt.equals(s):
                df[col] = s_dt
                continue

            df[col] = s
        else:
            df[col] = s

    return df


def load_dataset(uploaded_file) -> tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Parse an uploaded Streamlit file object into a DataFrame.
    Returns (df, None) on success or (None, error_msg) on failure.
    """
    try:
        name = uploaded_file.name.lower()

        if name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, low_memory=False)
        elif name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file)
        elif name.endswith(".json"):
            df = pd.read_json(uploaded_file)
        else:
            return None, "Unsupported file type. Please upload CSV, Excel, or JSON."

        # Basic cleanup
        df.columns = [normalize_column_name(c) for c in df.columns]
        df = df.loc[:, ~df.columns.duplicated()]  # drop duplicate columns

        # Better type inference
        df = infer_column_types(df)

        return df, None

    except Exception as e:
        return None, str(e)


def get_display_dtype(series: pd.Series) -> str:
    """
    Return a user-friendly semantic dtype label for the sidebar / schema.
    """
    if pd.api.types.is_integer_dtype(series):
        return "int"
    if pd.api.types.is_float_dtype(series):
        return "float"
    if pd.api.types.is_bool_dtype(series):
        return "bool"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    return "str"


def get_schema_summary(df: pd.DataFrame) -> dict:
    """
    Build a rich schema dict used for LLM prompt injection and sidebar display.
    """
    columns = {}

    for col in df.columns:
        dtype = get_display_dtype(df[col])
        non_null = int(df[col].notna().sum())
        n_unique = int(df[col].nunique(dropna=True))

        sample_vals = df[col].dropna().head(3).tolist()
        sample_str = ", ".join(str(v) for v in sample_vals)
        if len(sample_str) > 60:
            sample_str = sample_str[:57] + "..."

        columns[col] = {
            "dtype": dtype,
            "non_null": non_null,
            "n_unique": n_unique,
            "sample": sample_str,
        }

    return {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": columns,
    }


def schema_to_prompt_text(schema: dict) -> str:
    """
    Convert schema dict to a compact, LLM-friendly text block.
    """
    lines = [
        "Table name: df",
        f"Rows: {schema['row_count']:,} | Columns: {schema['column_count']}",
        "",
        "Columns:",
    ]

    for col, info in schema["columns"].items():
        lines.append(
            f"  - {col} ({info['dtype']}): "
            f"{info['non_null']:,} non-null, {info['n_unique']:,} unique. "
            f"Samples: {info['sample']}"
        )

    return "\n".join(lines)
