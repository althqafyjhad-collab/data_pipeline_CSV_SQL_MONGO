"""
processor.py - PROCESSING stage of the CSV pipeline.
====================================================

Turns the raw CSV DataFrame into a clean, ML-ready dataset.

Stages applied here:
    1. schema validation
    2. type conversion
    3. cleaning (duplicates, text, out-of-range values)
    4. final validation
"""

import logging

import pandas as pd

from common.schemas import (
    CSV_NUMERIC_COLUMNS,
    CSV_REQUIRED_COLUMNS,
    CSV_TEXT_COLUMNS,
    ensure_not_empty,
    ensure_required_columns,
    ensure_unique,
)

logger = logging.getLogger("csv_pipeline")


def validate_schema(df: pd.DataFrame) -> None:
    """Check that the raw file exposes every expected column."""
    ensure_not_empty(df, "Input dataset")
    ensure_required_columns(df, CSV_REQUIRED_COLUMNS)
    logger.info("[schema] validation passed.")


def convert_types(df: pd.DataFrame) -> pd.DataFrame:
    """Cast numeric columns, using NaN for unparsable values."""
    df = df.copy()
    for column in CSV_NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate rows/ids, normalise text, and blank out values
    that fall outside the valid ranges.
    """
    df = df.copy()

    df = df.drop_duplicates(keep="first")
    df = df.drop_duplicates(subset="student_id", keep="first")

    for column in CSV_TEXT_COLUMNS:
        df[column] = df[column].astype(str).str.strip().str.title()

    df.loc[~df["gpa"].between(0.0, 4.0), "gpa"] = pd.NA
    df.loc[~df["age"].between(16, 80), "age"] = pd.NA
    df.loc[~df["attendance"].between(0, 100), "attendance"] = pd.NA

    for column in ("age", "gpa", "attendance"):
        df[column] = df[column].fillna(df[column].median())

    logger.info(
        "[clean] %s rows x %s columns after cleaning",
        len(df),
        len(df.columns),
    )
    return df


def validate_data(df: pd.DataFrame) -> None:
    """Final quality gate before the dataset is written out."""
    ensure_not_empty(df, "DataFrame")
    ensure_unique(df, "student_id")

    if df["name"].isnull().any():
        raise ValueError("name contains NULL values.")
    if not df["age"].between(16, 80).all():
        raise ValueError("Invalid age values.")
    if not df["gpa"].between(0.0, 4.0).all():
        raise ValueError("Invalid gpa values.")
    if not df["attendance"].between(0, 100).all():
        raise ValueError("Invalid attendance values.")

    logger.info("[validate] final data is valid.")