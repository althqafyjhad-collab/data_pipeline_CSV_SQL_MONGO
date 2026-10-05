"""
processor.py - PROCESSING stage of the SQL pipeline.
====================================================

Turns the raw database DataFrame into a clean, ML-ready dataset.
"""

import logging

import pandas as pd

from common.schemas import (
    SQL_DATE_COLUMNS,
    SQL_NUMERIC_COLUMNS,
    SQL_REQUIRED_COLUMNS,
    SQL_TEXT_COLUMNS,
    ensure_not_empty,
    ensure_required_columns,
    ensure_unique,
)

logger = logging.getLogger("sql_pipeline")


def validate_schema(df: pd.DataFrame) -> None:
    """Check that the database query exposed every expected column."""
    ensure_not_empty(df, "Students table")
    ensure_required_columns(df, SQL_REQUIRED_COLUMNS)
    logger.info("[schema] validation passed.")


def convert_types(df: pd.DataFrame) -> pd.DataFrame:
    """Cast numeric and date columns to their proper types."""
    df = df.copy()

    for column in SQL_NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    for column in SQL_DATE_COLUMNS:
        df[column] = pd.to_datetime(df[column], errors="coerce")

    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicates, normalise text fields, convert gender codes to
    readable labels, and blank out out-of-range values.
    """
    df = df.copy()

    df = df.drop_duplicates(keep="first")
    df = df.drop_duplicates(subset="student_id", keep="first")

    for column in SQL_TEXT_COLUMNS:
        df[column] = df[column].astype(str).str.strip()

    df["full_name"] = df["full_name"].str.title()
    df["city"] = df["city"].str.title()
    df["city"] = df["city"].str.replace("'A", "'a", regex=False)

    df["gender"] = df["gender"].astype(str).str.strip().str.upper()
    df["status"] = df["status"].astype(str).str.strip().str.title()

    df.loc[df["gender"] == "M", "gender"] = "Male"
    df.loc[df["gender"] == "F", "gender"] = "Female"

    df.loc[
        ~df["enrollment_year"].between(1900, 2100), "enrollment_year"
    ] = pd.NA

    df.loc[
        ~df["average_score"].between(0, 100), "average_score"
    ] = pd.NA

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

    for column in ("full_name", "gender", "birth_date", "enrollment_year"):
        if df[column].isnull().any():
            raise ValueError(f"{column} contains NULL values.")

    if not df["enrollment_year"].between(1900, 2100).all():
        raise ValueError("Invalid enrollment_year values.")

    logger.info("[validate] final data is valid.")