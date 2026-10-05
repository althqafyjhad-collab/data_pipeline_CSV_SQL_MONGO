"""
seed.py - Fill MongoDB with random student documents.
====================================================

Inserts random students into the configured collection using the same
generator as the other sources, so all three datasets are comparable.

Usage
-----
    python src/pipelines/mongo/seed.py [count]
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pymongo.errors import BulkWriteError

from common.sample_data import generate_students
from pipelines.mongo.extractor import get_collection, get_database, ping
from pipelines.mongo.config import MONGO_CONFIG

TARGET_TOTAL = 100


def seed_mongodb(count: int = TARGET_TOTAL) -> int:
    """
    Insert random students so the collection holds about `count` records.

    Existing documents are preserved; only new random students are added.

    Returns
    -------
    int
        The total number of documents in the collection afterwards.
    """
    if not ping():
        raise ConnectionError("MongoDB is unreachable.")

    collection = get_collection()
    existing = collection.count_documents({})
    missing = max(0, count - existing)

    if missing == 0:
        print(
            f"[seed] collection already holds {existing} documents; "
            "nothing to add."
        )
        return existing

    students = generate_students(count=missing)
    now = datetime.now(timezone.utc)

    documents = []
    for student in students:
        documents.append(
            {
                "student_id": student.student_id,
                "name": student.name,
                "age": student.age,
                "gpa": student.gpa,
                "attendance": student.attendance,
                "city": student.city,
                "createdAt": now,
                "updatedAt": now,
            }
        )

    # `student_id` is indexed, so drop the duplicate ids coming from the
    # generator's deliberate duplicates before inserting.
    seen = set()
    unique_documents = []
    for document in documents:
        if document["student_id"] in seen:
            continue
        seen.add(document["student_id"])
        unique_documents.append(document)

    # Start the generated ids after the highest existing one.
    highest = max(
        (d.get("student_id", 0) for d in collection.find({}, {"student_id": 1})),
        default=0,
    )
    offset = highest
    for document in unique_documents:
        document["student_id"] = document["student_id"] + offset

    try:
        result = collection.insert_many(unique_documents)
        inserted = len(result.inserted_ids)
    except BulkWriteError as error:
        inserted = error.details.get("nInserted", 0)

    total = collection.count_documents({})
    print(
        f"[seed] inserted {inserted} documents into "
        f"{MONGO_CONFIG['database']}.{MONGO_CONFIG['collection']}; "
        f"total now {total}"
    )
    return total


if __name__ == "__main__":
    target = int(sys.argv[1]) if len(sys.argv) > 1 else TARGET_TOTAL
    total = seed_mongodb(target)

    # Build an index on student_id when it does not exist yet.
    collection = get_collection()
    if "student_id_1" not in collection.index_information():
        collection.create_index("student_id")
        print("[seed] created index on student_id")

    print(f"[seed] database: {MONGO_CONFIG['database']}")
    print(f"[seed] collections: {get_database().list_collection_names()}")
    print(f"[seed] documents in {MONGO_CONFIG['collection']}: {total}")