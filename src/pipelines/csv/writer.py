"""
writer.py - WRITING stage of the CSV pipeline.
================================================

This module does one job only: save a DataFrame to a CSV file.

It never reads, cleans or validates data.
"""

import logging
from pathlib import Path

import pandas as pd

from common.paths import CSV_OUTPUT_FILE


def write_csv(
    df: pd.DataFrame,
    output_path: Path = CSV_OUTPUT_FILE,
) -> Path:
    """
    Save the DataFrame to `output_path` as a CSV file.

    The parent folder is created when missing.

    Returns
    -------
    Path
        The path the file was written to.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    logging.getLogger("csv_pipeline").info(
        "[write] %s rows saved to %s",
        len(df),
        output_path,
    )

    return output_path