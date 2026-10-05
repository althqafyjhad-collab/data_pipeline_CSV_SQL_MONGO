"""
pipeline.py - Orchestration of the SQL pipeline.
=================================================

Runs the three independent stages in order:

    extractor  ->  processor  ->  writer

Usage
-----
    python src/pipelines/sql/pipeline.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from common.logging_setup import get_logger, log_failure
from common.paths import SQL_LOG_FILE, SQL_OUTPUT_FILE
from pipelines.sql.extractor import extract_students, ping
from pipelines.sql.processor import (
    clean,
    convert_types,
    validate_data,
    validate_schema,
)
from pipelines.sql.writer import write_sql


def run_sql_pipeline(output_file: Path = SQL_OUTPUT_FILE) -> pd.DataFrame:
    """
    Execute the SQL pipeline end to end and return the final DataFrame.
    """
    logger = get_logger("sql_pipeline", SQL_LOG_FILE)
    logger.info("SQL pipeline started.")

    try:
        if not ping():
            raise ConnectionError(
                "PostgreSQL is unreachable; check the connection settings."
            )

        # ---- Stage 1: READ -------------------------------------
        df = extract_students()

        # ---- Stage 2: PROCESS ----------------------------------
        validate_schema(df)
        df = convert_types(df)
        df = clean(df)
        validate_data(df)

        # ---- Stage 3: WRITE -------------------------------------
        write_sql(df, output_file)

        logger.info("SQL pipeline completed successfully.")
        print(f"SQL pipeline completed successfully -> {output_file}")
        return df

    except Exception as error:
        log_failure(logger, "sql_pipeline", error)
        print(f"SQL pipeline failed: {error}")
        raise


if __name__ == "__main__":
    run_sql_pipeline()