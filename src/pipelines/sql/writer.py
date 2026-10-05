"""
writer.py - WRITING stage of the SQL pipeline.
===============================================

Saves the processed DataFrame to a CSV file.
It performs no reading, cleaning or validation.
"""

import logging
import sys
from pathlib import Path

# Allow running this file directly from the project root.
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[2]),
)

import pandas as pd

from common.paths import SQL_OUTPUT_FILE


def write_sql(df: pd.DataFrame, output_path: Path = SQL_OUTPUT_FILE) -> Path:
    """Write the DataFrame to `output_path` and return that path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    logging.getLogger("sql_pipeline").info(
        "[write] %s rows saved to %s", len(df), output_path
    )
    return output_path