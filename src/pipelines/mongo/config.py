"""
config.py - MongoDB connection settings for the Mongo pipeline.
============================================================

Settings are read from environment variables (optionally from a
`.env` file) so credentials are never hard-coded.
"""

import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

# Load .env if present (project root).
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

MONGO_CONFIG: Dict[str, str] = {
    "host": os.getenv("MONGO_HOST", "localhost"),
    "port": os.getenv("MONGO_PORT", "27017"),
    "database": os.getenv("MONGO_DATABASE", "student_db"),
    "collection": os.getenv("MONGO_COLLECTION", "students"),
}

# Optional credentials (not required on a local default install).
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")


def uri() -> str:
    """
    Build the MongoDB connection URI.

    Credentials are only added when both are provided.
    """
    if MONGO_USER and MONGO_PASSWORD:
        return (
            f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}"
            f"@{MONGO_CONFIG['host']}:{MONGO_CONFIG['port']}"
        )
    return f"mongodb://{MONGO_CONFIG['host']}:{MONGO_CONFIG['port']}"