"""
run_all.py - Run every pipeline from a single command.
====================================================

Usage
-----
    python run_all.py             # default: shows all inputs and outputs
    python run_all.py --quiet     # only the outcome of each pipeline

Each pipeline is still independent and can be run on its own:

    python src/pipelines/csv/pipeline.py   [--quiet]
    python src/pipelines/sql/pipeline.py   [--quiet]
    python src/pipelines/mongo/pipeline.py [--quiet]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from pipelines.csv.pipeline import run_csv_pipeline
from pipelines.mongo.pipeline import run_mongo_pipeline
from pipelines.sql.pipeline import run_sql_pipeline


def parse_args(argv=None) -> argparse.Namespace:
    """Read the command line options."""
    parser = argparse.ArgumentParser(
        description="Run every student data pipeline."
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Hide the data previews and only report the outcome.",
    )
    return parser.parse_args(argv)


def main(verbose: bool = True) -> None:
    """Run the three pipelines in order."""
    for title, runner in (
        ("CSV pipeline", run_csv_pipeline),
        ("SQL pipeline", run_sql_pipeline),
        ("MongoDB pipeline", run_mongo_pipeline),
    ):
        print("=" * 60)
        print(f"Running {title}")
        print("=" * 60)
        runner(verbose=verbose)
        print()

    print("All pipelines finished.")


if __name__ == "__main__":
    options = parse_args()
    main(verbose=not options.quiet)