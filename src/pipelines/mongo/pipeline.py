"""
pipeline.py - Orchestration of the Mongo pipeline.
==================================================

Runs the three independent stages in order:

    extractor  ->  processor  ->  writer

Usage
-----
    python src/pipelines/mongo/pipeline.py             # normal run
    python src/pipelines/mongo/pipeline.py --verbose   # show the data
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from common.display import print_header, print_stage
from common.logging_setup import get_logger, log_failure
from common.paths import MONGO_LOG_FILE, MONGO_OUTPUT_FILE
from pipelines.mongo.config import MONGO_CONFIG
from pipelines.mongo.extractor import extract_students, ping
from pipelines.mongo.processor import (
    clean,
    convert_types,
    drop_internal_columns,
    validate_data,
    validate_schema,
)
from pipelines.mongo.writer import write_mongo


def parse_args(argv=None) -> argparse.Namespace:
    """Read the command line options."""
    parser = argparse.ArgumentParser(
        description="Run the MongoDB student pipeline."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print the documents read from MongoDB and the result.",
    )
    return parser.parse_args(argv)


def run_mongo_pipeline(
    output_file: Path = MONGO_OUTPUT_FILE,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Execute the Mongo pipeline end to end and return the final DataFrame.

    Parameters
    ----------
    output_file:
        Where the cleaned dataset is written.
    verbose:
        When True, print the data at every stage to the console.
    """
    logger = get_logger("mongo_pipeline", MONGO_LOG_FILE)
    logger.info("Mongo pipeline started.")

    if verbose:
        print_header("MONGO PIPELINE")
        print(
            f"collection: {MONGO_CONFIG['database']}."
            f"{MONGO_CONFIG['collection']}"
        )
        print(f"output    : {output_file}")

    try:
        if not ping():
            raise ConnectionError(
                "MongoDB is unreachable; check the connection settings."
            )

        # ---- Stage 1: READ -------------------------------------
        df = extract_students()

        if verbose:
            print_stage("INPUT (raw documents)", df)

        # ---- Stage 2: PROCESS ----------------------------------
        validate_schema(df)
        df = drop_internal_columns(df)

        if verbose:
            print_stage("AFTER DROPPING INTERNAL FIELDS", df)

        df = convert_types(df)
        df = clean(df)
        validate_data(df)

        if verbose:
            print_stage("AFTER CLEANING", df)

        # ---- Stage 3: WRITE -------------------------------------
        write_mongo(df, output_file)

        if verbose:
            print_header("MONGO PIPELINE RESULT")
            print(f"rows written: {len(df)}")
            print(f"saved to    : {output_file}")

        logger.info("Mongo pipeline completed successfully.")
        print(f"Mongo pipeline completed successfully -> {output_file}")
        return df

    except Exception as error:
        log_failure(logger, "mongo_pipeline", error)
        print(f"Mongo pipeline failed: {error}")
        raise


if __name__ == "__main__":
    options = parse_args()
    run_mongo_pipeline(verbose=options.verbose)