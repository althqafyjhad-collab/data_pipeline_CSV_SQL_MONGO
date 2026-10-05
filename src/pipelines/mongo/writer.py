"""
writer.py - WRITING stage of the Mongo pipeline.
=================================================

Saves the processed DataFrame to a CSV file.

It performs no reading, no cleaning and no validation.
"""

import logging
from pathlib import Path

import pandas as pd

from common.paths import MONGO_OUTPUT_FILE


def write_mongo(
    df: pd.DataFrame,
    output_path: Path = MONGO_OUTPUT_FILE,
) -> Path:
    """Write the DataFrame to `output_path` and return that path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    logging.getLogger("mongo_pipeline").info(
        "[write] %s rows saved to %s", len(df), output_path
    )
    return output_path