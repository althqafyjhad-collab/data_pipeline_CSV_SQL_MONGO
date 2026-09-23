"""
db.py - PostgreSQL connection and data loading utilities
========================================================

This module encapsulates everything related to connecting to the
PostgreSQL database `university_tranining` and reading data from
its tables (e.g. `students`).

Two connection strategies are provided so the learner can compare:

    1. psycopg2  : the low-level / raw driver (DBAPI 2.0 compatible)
    2. SQLAlchemy: the ORM/engine abstraction recommended with pandas

All connection parameters are read from environment variables
(or a local `.env` file) so that credentials are never hard-coded
in source code.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd
from dotenv import load_dotenv
from psycopg2 import connect, sql
from psycopg2.extensions import connection as PgConnection
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Connection, Engine

# ------------------------------------------------------------------
# 1) Load environment variables from a `.env` file if it exists
# ------------------------------------------------------------------
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ------------------------------------------------------------------
# 2) Default connection parameters (overridable via environment)
# ------------------------------------------------------------------
DB_CONFIG: Dict[str, str] = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": os.getenv("PGPORT", "5432"),
    "dbname": os.getenv("PGDATABASE", "university_tranining"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", "postgres"),
}

# The SQL query used by the original pipeline (joins several tables)
STUDENT_AVERAGE_QUERY = """
SELECT
    s.student_id,
    s.full_name,
    c.course_name,
    AVG(a.score) AS average_score
FROM assessments a
INNER JOIN students s
    ON a.student_id = s.student_id
INNER JOIN courses c
    ON a.course_id = c.course_id
GROUP BY
    s.student_id,
    s.full_name,
    c.course_id,
    c.course_name
"""


# ==================================================================
# Approach (A) - psycopg2 (the low-level driver)
# ==================================================================

def get_connection_psycopg2() -> PgConnection:
    """
    Open a direct PostgreSQL connection using the psycopg2 driver.

    psycopg2 speaks the PostgreSQL wire protocol directly.
    It returns a DBAPI-2.0-compatible connection object that you can
    use to run raw SQL with a cursor.
    """
    return connect(**DB_CONFIG)


def ping_psycopg2() -> bool:
    """
    Verify the connection works by executing `SELECT 1`.
    """
    try:
        with get_connection_psycopg2() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return True
    except Exception as exc:  # OperationalError, ProgrammingError, ...
        print(f"[psycopg2] Connection failed: {exc}")
        return False


def list_tables_psycopg2() -> List[str]:
    """
    List all user tables in the public schema.
    """
    with get_connection_psycopg2() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT tablename
                FROM pg_catalog.pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename;
                """
            )
            return [row[0] for row in cur.fetchall()]


def read_table_psycopg2(
    table_name: str,
    columns: Optional[List[str]] = None,
    where: Optional[str] = None,
) -> pd.DataFrame:
    """
    Read a whole table (or selected columns / filtered rows) into a DataFrame.

    Uses `sql.Identifier` / `sql.SQL` from psycopg2 to build the query
    safely, preventing SQL injection from the table name.
    """
    col_sql = sql.SQL(", ").join(
        sql.Identifier(c) for c in columns
    ) if columns else sql.SQL("*")

    base = sql.SQL("SELECT {cols} FROM {table}").format(
        cols=col_sql,
        table=sql.Identifier(table_name),
    )

    query = base
    if where:
        query = sql.SQL("{base} WHERE {cond}").format(
            base=base,
            cond=sql.SQL(where),
        )

    with get_connection_psycopg2() as conn:
        return pd.read_sql_query(query.as_string(conn), conn)


# ==================================================================
# Approach (B) - SQLAlchemy (engine, recommended with pandas)
# ==================================================================

def get_engine() -> Engine:
    """
    Build a SQLAlchemy Engine for PostgreSQL.

    A string connection URL is built from DB_CONFIG and passed to
    `create_engine`. The Engine manages a connection pool under the
    hood, reusing connections instead of reopening them each time.
    """
    url = (
        f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    )
    return create_engine(url, pool_pre_ping=True)


def ping_sqlalchemy() -> bool:
    """
    Test the engine by running `SELECT 1`.
    """
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        print(f"[SQLAlchemy] Connection failed: {exc}")
        return False


def list_tables_sqlalchemy() -> List[str]:
    """
    Introspect the database and return table names.
    """
    inspector = inspect(get_engine())
    return inspector.get_table_names()


def read_table_sqlalchemy(
    table_name: str,
    columns: Optional[List[str]] = None,
    where: Optional[str] = None,
) -> pd.DataFrame:
    """
    Read a table into a pandas DataFrame using the SQLAlchemy engine.

    - If `columns` is None every column is read.
    - If `where` is provided it is appended as a WHERE clause.
      (The user is expected to provide a trusted, controlled filter.)
    """
    engine = get_engine()
    if columns is None and where is None:
        return pd.read_sql_table(table_name, engine)

    select_cols = ", ".join(columns) if columns else "*"
    query = f"SELECT {select_cols} FROM {table_name}"
    if where:
        query += f" WHERE {where}"

    return pd.read_sql_query(query, engine)


def read_query_sqlalchemy(query: str) -> pd.DataFrame:
    """
    Run an arbitrary SQL SELECT and return the result as a DataFrame.
    """
    engine = get_engine()
    return pd.read_sql_query(query, engine)


# ==================================================================
# High-level helpers (used by the pipeline)
# ==================================================================

def load_students_table(
    engine: Optional[Engine] = None,
    columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Convenience wrapper: load the `students` table from PostgreSQL.
    """
    engine = engine or get_engine()
    return read_table_sqlalchemy("students", columns=columns)


def run_pipeline_query(query: str = STUDENT_AVERAGE_QUERY) -> pd.DataFrame:
    """
    Run the JOIN query that aggregates student averages per course.
    """
    return read_query_sqlalchemy(query)


if __name__ == "__main__":
    print("=== PostgreSQL connection test ===")
    print(f"Config: {DB_CONFIG}")

    print("\n[psycopg2] ping:", ping_psycopg2())
    print("[psycopg2] tables:", list_tables_psycopg2())

    print("\n[SQLAlchemy] ping:", ping_sqlalchemy())
    print("[SQLAlchemy] tables:", list_tables_sqlalchemy())

    print("\n[SQLAlchemy] students sample:")
    df = load_students_table()
    print(df.head())