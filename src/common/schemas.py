"""
schemas.py - Validation rules for each data source.
==================================================

The CSV source and the SQL source have completely different columns,
so each one declares its own required columns and its own validators.

Keeping them here means the two pipelines never depend on each other.
"""

from typing import List

import pandas as pd

# =====================
# CSV source schema
# =====================
CSV_REQUIRED_COLUMNS: List[str] = [
    "student_id",
    "name",
    "age",
    "gpa",
    "attendance",
    "city",
]

CSV_NUMERIC_COLUMNS: List[str] = [
    "student_id",
    "age",
    "gpa",
    "attendance",
]

CSV_TEXT_COLUMNS: List[str] = ["name", "city"]

# =====================
# SQL source schema
# =====================
SQL_REQUIRED_COLUMNS: List[str] = [
    "student_id",
    "full_name",
    "gender",
    "birth_date",
    "city",
    "enrollment_year",
    "status",
]

SQL_NUMERIC_COLUMNS: List[str] = [
    "student_id",
    "enrollment_year",
    "total_courses",
    "completed_courses",
    "average_score",
]

SQL_DATE_COLUMNS: List[str] = ["birth_date"]

SQL_TEXT_COLUMNS: List[str] = ["full_name", "city"]


# =====================
# Generic validators
# =====================

def ensure_required_columns(
    df: pd.DataFrame,
    required: List[str],
) -> None:
    """Raise ValueError if any required column is missing."""
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def ensure_not_empty(df: pd.DataFrame, label: str) -> None:
    """Raise ValueError when the DataFrame contains no rows."""
    if df.empty:
        raise ValueError(f"{label} is empty.")


def ensure_unique(df: pd.DataFrame, column: str) -> None:
    """Raise ValueError when `column` contains NULLs or duplicates."""
    if df[column].isnull().any():
        raise ValueError(f"{column} contains NULL values.")
    if df[column].duplicated().any():
        raise ValueError(f"{column} is not unique.")