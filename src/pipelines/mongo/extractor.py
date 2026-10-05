"""
extractor.py - READING stage of the Mongo pipeline.
===================================================

Reads documents from MongoDB with pymongo and returns them as a
DataFrame.

No cleaning, no validation and no writing happen here.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Allow running this file directly from the project root.
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[2]),
)

import pandas as pd
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError

from pipelines.mongo.config import MONGO_CONFIG, uri

logger = logging.getLogger("mongo_pipeline")

_client: Optional[MongoClient] = None


def get_client() -> MongoClient:
    """Return a shared MongoClient (created once and reused)."""
    global _client
    if _client is None:
        _client = MongoClient(uri(), serverSelectionTimeoutMS=5000)
    return _client


def get_database() -> Database:
    """Return the configured database handle."""
    return get_client()[MONGO_CONFIG["database"]]


def get_collection() -> Collection:
    """Return the configured collection handle."""
    return get_database()[MONGO_CONFIG["collection"]]


def ping() -> bool:
    """Return True when the server answers a `ping` command."""
    try:
        get_client().admin.command("ping")
        return True
    except PyMongoError as error:
        logger.error("[ping] MongoDB unreachable: %s", error)
        return False


def extract_students(
    query: Optional[dict] = None,
    projection: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Read documents from the `students` collection into a DataFrame.

    Parameters
    ----------
    query:
        Optional MongoDB filter, e.g. ``{"gpa": {"$gte": 3}}``.
    projection:
        Optional field selection; by default every field is read.

    Returns
    -------
    pd.DataFrame
        The documents as rows, `_id` included.
    """
    documents = list(get_collection().find(query or {}, projection))

    if not documents:
        logger.warning("[read] no documents found.")
        return pd.DataFrame()

    df = pd.json_normalize(documents)

    logger.info(
        "[read] %s rows x %s columns from %s.%s",
        len(df),
        len(df.columns),
        MONGO_CONFIG["database"],
        MONGO_CONFIG["collection"],
    )
    return df