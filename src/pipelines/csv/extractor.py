"""
extractor.py - READING stage of the CSV pipeline.
================================================

This module does one job only: read raw data from a CSV file.

It performs no cleaning, no validation and no writing. Those stages
live in `processor.py` and `writer.py` so that every concern stays in
its own module.
"""

import logging
from pathlib import Path

import pandas as pd

from common.paths import CSV_INPUT_FILE


def extract_csv(
    file_path: Path = CSV_INPUT_FILE,
) -> pd.DataFrame:
    """
    Read a CSV file into a DataFrame and return it untouched.

    Parameters
    ----------
    file_path:
        Path of the CSV file to read.

    Returns
    -------
    pd.DataFrame
        The raw contents of the file.

    Raises
    ------
    FileNotFoundError
        When the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    df = pd.read_csv(file_path)

    logging.getLogger("csv_pipeline").info(
        "[read] %s rows x %s columns from %s",
        len(df),
        len(df.columns),
        file_path.name,
    )

    return df