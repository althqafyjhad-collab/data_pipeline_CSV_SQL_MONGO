from pathlib import Path
import logging
import pandas as pd

from db import (
    get_engine,
    ping_sqlalchemy,
    load_students_table,
    load_student_summary,
)

# Name of the tables that exist in the PostgreSQL database
# `advanced_sql_training_db` (edit if your schema differs).
STUDENTS_TABLE = "students"

RAW_FILE = Path("data/raw/students_raw.csv")
OUTPUT_FILE = Path("data/processed/students_ml_ready.csv")
LOG_FILE = Path("logs/pipeline.log")

REQUIRED_COLUMNS = {
    "student_id",
    "full_name",
    "gender",
    "birth_date",
    "city",
    "enrollment_year",
    "status",
}


# =========================
# Logging Configuration
# =========================

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# =========================
# Load Data (from PostgreSQL)
# =========================

def load_data(file_path: Path = RAW_FILE) -> pd.DataFrame:
    """
    Load data into a pandas DataFrame.

    The primary source is the `students` table in the PostgreSQL
    database `advanced_sql_training_db`. The CSV file path is kept only
    as a fallback when the database is not available.
    """

    logger.info(
        f"Loading {STUDENTS_TABLE} table from PostgreSQL database"
    )

    try:
        # Ensure the DB connection is healthy before reading.
        engine = get_engine()

        if not ping_sqlalchemy():
            logger.warning(
                "PostgreSQL is unreachable; falling back to CSV"
            )
            return _load_csv(file_path)

        df = load_students_table(engine)

        if df.empty:
            raise ValueError(
                "Students table is empty."
            )

        # Merge per-student summary used for ML feature engineering.
        summary = load_student_summary(engine)
        df = df.merge(
            summary.drop(columns=["full_name", "gender", "city"]),
            on="student_id",
            how="left",
        )

        logger.info(
            f"Loaded {len(df)} rows and {len(df.columns)} columns "
            f"from PostgreSQL table '{STUDENTS_TABLE}'"
        )

        return df

    except Exception as exc:
        logger.error(f"PostgreSQL load failed: {exc}")
        raise


def _load_csv(file_path: Path) -> pd.DataFrame:
    """
    Fallback loader that reads from a CSV file (kept for compat).
    """

    logger.info(f"[fallback] Loading data from {file_path}")

    if not file_path.exists():
        raise FileNotFoundError(
            f"Data file not found: {file_path}"
        )

    df = pd.read_csv(file_path)

    if df.empty:
        raise ValueError(
            "Input dataset is empty."
        )

    logger.info(
        f"[fallback] Loaded {len(df)} rows and {len(df.columns)} columns"
    )

    return df


# =========================
# Schema Validation
# =========================

def validate_schema(df: pd.DataFrame) -> None:
    """
    Validate the schema of the DataFrame.
    """

    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    logger.info("Schema validation passed.")

# ========================
# Convert Data Types
# =========================

def convert_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert data types for specific columns.
    """
    df = df.copy()
    numeric_columns = [
        "student_id",
        "enrollment_year",
        "total_courses",
        "completed_courses",
        "average_score",
    ]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")

    return df

# ========================
# Clean Data
# ========================

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the DataFrame by handling missing values,
    invalid values, duplicates, and text fields.
    """

    df = df.copy()

    # --------------------------------------------------
    # Remove duplicate rows
    # --------------------------------------------------

    df = df.drop_duplicates(
        keep="first"
    )

    # --------------------------------------------------
    # Remove duplicate student_id entries
    # Keep the first occurrence
    # --------------------------------------------------

    df = df.drop_duplicates(
        subset="student_id",
        keep="first"
    )

    # --------------------------------------------------
    # Clean text fields
    # --------------------------------------------------

    df["full_name"] = (
        df["full_name"]
        .str.strip()
        .str.title()
    )

    df["city"] = (
        df["city"]
        .str.strip()
        .str.title()
    )

    df["gender"] = df["gender"].str.strip().str.upper()

    df["status"] = df["status"].str.strip().str.title()

    # --------------------------------------------------
    # Normalize gender codes to readable labels
    # --------------------------------------------------

    df.loc[df["gender"] == "M", "gender"] = "Male"
    df.loc[df["gender"] == "F", "gender"] = "Female"

    # --------------------------------------------------
    # Keep only valid enrollment years (>= 1900)
    # --------------------------------------------------

    df.loc[
        ~df["enrollment_year"].between(1900, 2100),
        "enrollment_year"
    ] = pd.NA

    # --------------------------------------------------
    # Cap average_score to the valid 0 - 100 range
    # --------------------------------------------------

    df.loc[
        ~df["average_score"].between(0, 100),
        "average_score"
    ] = pd.NA

    # --------------------------------------------------
    # Logging
    # --------------------------------------------------

    logger.info(
        f"After cleaning: "
        f"{len(df)} rows and "
        f"{len(df.columns)} columns"
    )

    return df

# ========================
#  Validate Data
# ======================
def validate_data(df: pd.DataFrame) -> None:
    """
    Validate the cleaned DataFrame for any remaining issues.
    """
    errors = []
    if df.empty:
        errors.append("DataFrame is empty.")

    if df["student_id"].isnull().any():
        errors.append("student_id contains values NULL.")
    if df["student_id"].duplicated().any():
        errors.append("student_id is not unique.")
    if df["full_name"].isnull().any():
        errors.append("full_name contains NULL values.")
    if df["gender"].isnull().any():
        errors.append("gender contains NULL values.")
    if df["birth_date"].isnull().any():
        errors.append("birth_date contains NULL values.")
    if df["enrollment_year"].isnull().any():
        errors.append("enrollment_year contains NULL values.")
    if not df["enrollment_year"].between(1900, 2100).all():
        errors.append("Invalid enrollment_year values.")
    if errors:
        raise ValueError("Data validation errors:\n " + "\n "
        .join(f"- {error}" for error in errors))
    
# ========================
# Save Data
# ========================
def save_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the DataFrame to a CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info("Save process data to %s",{output_path})


# =========================
# run_pipeline
# =======================
def run_pipeline():
    """
    Run the entire data processing pipeline.
    """
    try:
        logger.info(
               "Pipeline started.")
        # Extract (PostgreSQL => DataFrame)
        df = load_data()

        # Validate schema
        validate_schema(df)

        # Transform
        df = convert_data_types(df)

        # Clean
        df = clean_data(df)

        # Validate final data
        validate_data(df)

        # Load
        save_data(df, OUTPUT_FILE)
        logger.info("Pipeline completed successfully.")

        print("Pipeline completed successfully")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        print(f"Pipeline failed: {e}")

# =========================
# Main
# =========================

if __name__ == "__main__":

    run_pipeline()