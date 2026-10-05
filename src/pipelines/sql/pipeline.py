"""
pipeline.py - Orchestration of the SQL pipeline.
=================================================

Runs the three independent stages in order:

    extractor  ->  processor  ->  writer

Usage
-----
    python src/pipelines/sql/pipeline.py             # normal run
    python src/pipelines/sql/pipeline.py --verbose   # show the data
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from common.display import print_header, print_stage
from common.logging_setup import get_logger, log_failure
from common.paths import SQL_LOG_FILE, SQL_OUTPUT_FILE
from pipelines.sql.config import DB_CONFIG
from pipelines.sql.extractor import extract_students, ping
from pipelines.sql.processor import (
    clean,
    convert_types,
    validate_data,
    validate_schema,
)
from pipelines.sql.writer import write_sql


def parse_args(argv=None) -> argparse.Namespace:
    """Read the command line options."""
    parser = argparse.ArgumentParser(
        description="Run the PostgreSQL student pipeline."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print the data read from the database and the result.",
    )
    return parser.parse_args(argv)


def run_sql_pipeline(
    output_file: Path = SQL_OUTPUT_FILE,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Execute the SQL pipeline end to end and return the final DataFrame.

    Parameters
    ----------
    output_file:
        Where the cleaned dataset is written.
    verbose:
        When True, print the data at every stage to the console.
    """
    logger = get_logger("sql_pipeline", SQL_LOG_FILE)
    logger.info("SQL pipeline started.")

    if verbose:
        print_header("SQL PIPELINE")
        print(
            f"database: {DB_CONFIG['dbname']} "
            f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}"
        )
        print(f"output  : {output_file}")

    try:
        if not ping():
            raise ConnectionError(
                "PostgreSQL is unreachable; check the connection settings."
            )

        # ---- Stage 1: READ -------------------------------------
        df = extract_students()

        if verbose:
            print_stage("INPUT (from PostgreSQL)", df)

        # ---- Stage 2: PROCESS ----------------------------------
        validate_schema(df)
        df = convert_types(df)

        if verbose:
            print_stage("AFTER TYPE CONVERSION", df)

        df = clean(df)
        validate_data(df)

        if verbose:
            print_stage("AFTER CLEANING", df)

        # ---- Stage 3: WRITE -------------------------------------
        write_sql(df, output_file)

        if verbose:
            print_header("SQL PIPELINE RESULT")
            print(f"rows written: {len(df)}")
            print(f"saved to    : {output_file}")

        logger.info("SQL pipeline completed successfully.")
        print(f"SQL pipeline completed successfully -> {output_file}")
        return df

    except Exception as error:
        log_failure(logger, "sql_pipeline", error)
        print(f"SQL pipeline failed: {error}")
        raise


if __name__ == "__main__":
    options = parse_args()
    run_sql_pipeline(verbose=options.verbose)