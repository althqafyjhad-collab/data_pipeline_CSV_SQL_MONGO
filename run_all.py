"""
run_all.py - Run both pipelines from a single command.
====================================================

Usage
-----
    python run_all.py

Each pipeline is still independent and can be run on its own:

    python src/pipelines/csv/pipeline.py
    python src/pipelines/sql/pipeline.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from pipelines.csv.pipeline import run_csv_pipeline
from pipelines.sql.pipeline import run_sql_pipeline


def main() -> None:
    print("=" * 60)
    print("Running CSV pipeline")
    print("=" * 60)
    run_csv_pipeline()

    print()
    print("=" * 60)
    print("Running SQL pipeline")
    print("=" * 60)
    run_sql_pipeline()

    print()
    print("Both pipelines finished.")


if __name__ == "__main__":
    main()