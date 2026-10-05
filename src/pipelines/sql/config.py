"""
config.py - Database connection settings for the SQL pipeline.
============================================================

Credentials are read from environment variables (optionally from a
`.env` file) so they are never hard-coded in the source code.

The defaults match a local PostgreSQL installation.
"""

import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

# Load .env if present (project root).
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

DB_CONFIG: Dict[str, str] = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": os.getenv("PGPORT", "5432"),
    "dbname": os.getenv("PGDATABASE", "advanced_sql_training_db"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", "postgres"),
}


def connection_url() -> str:
    """Build the SQLAlchemy connection URL from DB_CONFIG."""
    return (
        f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    )