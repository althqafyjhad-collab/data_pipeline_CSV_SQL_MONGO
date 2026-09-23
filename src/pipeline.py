from pathlib import Path
import logging
import pandas as pd

from db import (
    get_engine,
    ping_sqlalchemy,
    load_students_table,
)

# Names of the tables that exist in the PostgreSQL database
# `university_tranining` (edit if your schema differs).
STUDENTS_TABLE = "students"

RAW_FILE = Path("data/raw/students_raw.csv")
OUTPUT_FILE = Path("data/processed/students_ml_ready.csv")
LOG_FILE = Path("logs/pipeline.log")

REQUIRED_COLUMNS = {
    "student_id",
    "name",
    "age",
    "gpa",
    "attendance",
    "city",
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
    database `university_tranining`. The CSV file path is kept only
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
        "age", 
        "gpa",
        "attendance"
        ]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")


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

    df["name"] = (
        df["name"]
        .str.strip()
        .str.title()
    )

    df["city"] = (
        df["city"]
        .str.strip()
        .str.title()
    )

    # --------------------------------------------------
    # Invalid GPA
    # Valid range: 0 - 4
    # --------------------------------------------------

    df.loc[
        ~df["gpa"].between(0.0, 4.0),
        "gpa"
    ] = pd.NA

    # --------------------------------------------------
    # Invalid Age
    # Valid range: 16 - 80
    # --------------------------------------------------

    df.loc[
        ~df["age"].between(16, 80),
        "age"
    ] = pd.NA

    # --------------------------------------------------
    # Invalid Attendance
    # Valid range: 0 - 100
    # --------------------------------------------------

    df.loc[
        ~df["attendance"].between(0, 100),
        "attendance"
    ] = pd.NA

    # --------------------------------------------------
    # Fill missing numeric values with median
    # --------------------------------------------------

    for column in [
        "age",
        "gpa",
        "attendance"
    ]:

        df[column] = df[column].fillna(
            df[column].median()
        )

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
    if not df["age"].between(16,80).all():
        errors.append("Invalid age values.")
    if df["name"].isnull().any():
        errors.append("name contains NULL values.")
    if not df["gpa"].between(0.0, 4.0).all():
        errors.append("Invalid gpa values.")
    if not df["attendance"].between(0, 100).all():
        errors.append("Invalid attendance values.")
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