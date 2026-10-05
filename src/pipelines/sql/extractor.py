"""
extractor.py - READING stage of the SQL pipeline.
=================================================

Reads data from PostgreSQL and returns it as a DataFrame.

No cleaning, no validation, no writing happens here.
"""

import logging
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from pipelines.sql.config import connection_url

logger = logging.getLogger("sql_pipeline")

_engine: Optional[Engine] = None

# Columns present in both the `students` table and the summary query.
# They are dropped from the summary before merging to avoid the
# duplicated `x` / `x_y` columns that pandas would create.
SQL_SUMMARY_DUPLICATE_COLUMNS = [
    "full_name",
    "gender",
    "city",
    "enrollment_year",
    "status",
]

# Per-student summary used as ML features.
STUDENT_SUMMARY_QUERY = """
SELECT
    s.student_id,
    s.full_name,
    s.gender,
    s.city,
    s.enrollment_year,
    s.status,
    COUNT(DISTINCT e.course_id)                AS total_courses,
    COUNT(DISTINCT CASE
        WHEN e.enrollment_status = 'Completed'
        THEN e.course_id
    END)                                       AS completed_courses,
    ROUND(
        AVG(a.score) FILTER (WHERE a.score IS NOT NULL),
        2
    )                                          AS average_score
FROM students s
LEFT JOIN enrollments e
    ON e.student_id = s.student_id
LEFT JOIN assessments a
    ON a.student_id = s.student_id
    AND a.course_id = e.course_id
GROUP BY
    s.student_id,
    s.full_name,
    s.gender,
    s.city,
    s.enrollment_year,
    s.status
"""


def get_engine() -> Engine:
    """Return a shared SQLAlchemy engine (created once)."""
    global _engine
    if _engine is None:
        _engine = create_engine(connection_url(), pool_pre_ping=True)
    return _engine


def ping() -> bool:
    """Return True when the database answers a simple query."""
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as error:
        logger.error("[ping] connection failed: %s", error)
        return False


def extract_students() -> pd.DataFrame:
    """
    Read the `students` table together with the per-student summary
    and return the merged DataFrame.
    """
    engine = get_engine()

    students = pd.read_sql_table("students", engine)
    summary = pd.read_sql_query(STUDENT_SUMMARY_QUERY, engine)

    # `students` already carries full_name / gender / city /
    # enrollment_year / status, so we only take the aggregated feature
    # columns from the summary to avoid duplicated columns.
    features = summary.drop(columns=SQL_SUMMARY_DUPLICATE_COLUMNS)

    df = students.merge(features, on="student_id", how="left")

    logger.info(
        "[read] %s rows x %s columns from database",
        len(df),
        len(df.columns),
    )
    return df