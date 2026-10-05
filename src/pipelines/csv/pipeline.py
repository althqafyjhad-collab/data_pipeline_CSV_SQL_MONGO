"""
pipeline.py - Orchestration of the CSV pipeline.
================================================

Runs the three independent stages in order:

    extractor  ->  processor  ->  writer

Usage
-----
    python src/pipelines/csv/pipeline.py
"""

import sys
from pathlib import Path

# Allow running this file directly from the project root.
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[2]),
)

import pandas as pd

from common.logging_setup import get_logger, log_failure
from common.paths import CSV_INPUT_FILE, CSV_LOG_FILE, CSV_OUTPUT_FILE
from pipelines.csv.extractor import extract_csv
from pipelines.csv.processor import (
    clean,
    convert_types,
    validate_data,
    validate_schema,
)
from pipelines.csv.writer import write_csv


def run_csv_pipeline(
    input_file: Path = CSV_INPUT_FILE,
    output_file: Path = CSV_OUTPUT_FILE,
) -> pd.DataFrame:
    """
    Execute the CSV pipeline end to end and return the final DataFrame.

    Parameters
    ----------
    input_file:
        Raw CSV file to read.
    output_file:
        Where the cleaned dataset is written.
    """
    logger = get_logger("csv_pipeline", CSV_LOG_FILE)
    logger.info("CSV pipeline started.")

    try:
        # ---- Stage 1: READ -------------------------------------
        df = extract_csv(input_file)

        # ---- Stage 2: PROCESS ----------------------------------
        validate_schema(df)
        df = convert_types(df)
        df = clean(df)
        validate_data(df)

        # ---- Stage 3: WRITE -------------------------------------
        write_csv(df, output_file)

        logger.info("CSV pipeline completed successfully.")
        print(f"CSV pipeline completed successfully -> {output_file}")
        return df

    except Exception as error:
        log_failure(logger, "csv_pipeline", error)
        print(f"CSV pipeline failed: {error}")
        raise


if __name__ == "__main__":
    run_csv_pipeline()