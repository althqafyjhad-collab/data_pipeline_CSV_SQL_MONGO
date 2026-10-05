"""
processor.py - PROCESSING stage of the Mongo pipeline.
======================================================

Turns the raw MongoDB DataFrame into a clean, ML-ready dataset.
"""

import logging

import pandas as pd

from common.schemas import (
    MONGO_INTERNAL_COLUMNS,
    MONGO_NUMERIC_COLUMNS,
    MONGO_REQUIRED_COLUMNS,
    MONGO_TEXT_COLUMNS,
    ensure_not_empty,
    ensure_required_columns,
    ensure_unique,
)

logger = logging.getLogger("mongo_pipeline")


def validate_schema(df: pd.DataFrame) -> None:
    """Check that the documents expose every expected field."""
    ensure_not_empty(df, "MongoDB collection")
    ensure_required_columns(df, MONGO_REQUIRED_COLUMNS)
    logger.info("[schema] validation passed.")


def drop_internal_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove MongoDB bookkeeping fields so they never reach the output.

    (`_id` is an ObjectId, `__v` is a version counter, and the
    timestamps are metadata.)
    """
    df = df.copy()
    to_drop = [c for c in MONGO_INTERNAL_COLUMNS if c in df.columns]
    if to_drop:
        df = df.drop(columns=to_drop)
    return df


def convert_types(df: pd.DataFrame) -> pd.DataFrame:
    """Cast numeric columns, using NaN for unparsable values."""
    df = df.copy()
    for column in MONGO_NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicates, normalise text fields, and blank out values that
    fall outside the valid ranges.
    """
    df = df.copy()

    df = df.drop_duplicates(keep="first")
    df = df.drop_duplicates(subset="student_id", keep="first")

    for column in MONGO_TEXT_COLUMNS:
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