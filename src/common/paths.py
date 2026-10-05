"""
paths.py - Central location for every filesystem path used by the project.
==============================================================

All pipelines (SQL and CSV) import their paths from here, so changing
a folder name only requires editing this single file.
"""

from pathlib import Path

# Root of the project (the folder that contains `src/`)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# --- Folders ---------------------------------------------------------
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"

# --- CSV pipeline paths ---------------------------------------------
CSV_INPUT_FILE = RAW_DIR / "students_raw.csv"
CSV_OUTPUT_FILE = PROCESSED_DIR / "students_ml_ready.csv"
CSV_LOG_FILE = LOGS_DIR / "pipeline_csv.log"

# --- SQL pipeline paths ---------------------------------------------
SQL_OUTPUT_FILE = PROCESSED_DIR / "students_sql_ml_ready.csv"
SQL_LOG_FILE = LOGS_DIR / "pipeline_sql.log"

# --- Environment file -----------------------------------------------
ENV_FILE = PROJECT_ROOT / ".env"
ENV_EXAMPLE_FILE = PROJECT_ROOT / ".env.example"


def ensure_directories() -> None:
    """Create the output/log folders if they do not exist yet."""
    for folder in (RAW_DIR, PROCESSED_DIR, LOGS_DIR):
        folder.mkdir(parents=True, exist_ok=True)