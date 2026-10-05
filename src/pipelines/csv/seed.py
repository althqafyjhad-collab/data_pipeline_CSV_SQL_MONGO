"""
seed.py - Regenerate the raw CSV file with random students.
==========================================================

Writes about 100 random students to `data/raw/students_raw.csv`,
preserving the original 8 records at the top of the file.

Usage
-----
    python src/pipelines/csv/seed.py [count]
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from common.paths import CSV_INPUT_FILE, ensure_directories
from common.sample_data import generate_students

TARGET_TOTAL = 100
HEADER = ["student_id", "name", "age", "gpa", "attendance", "city"]


def seed_csv(
    count: int = TARGET_TOTAL,
    output_path: Path = CSV_INPUT_FILE,
) -> int:
    """
    Write random students to the raw CSV file.

    When the file already exists, its original rows are kept and the
    random ones are appended after them.

    Returns
    -------
    int
        The total number of data rows written.
    """
    ensure_directories()

    existing_ids = []
    existing_rows = []

    if output_path.exists():
        df = pd.read_csv(output_path)
        existing_rows = df.to_dict("records")
        existing_ids = [int(r["student_id"]) for r in existing_rows]

    missing = max(0, count - len(existing_rows))
    start_id = max(existing_ids) + 1 if existing_ids else 1

    # Nothing to add: leave the file untouched so re-running the
    # script is always safe.
    if missing == 0:
        print(f"[seed] file already holds {len(existing_rows)} rows; nothing to add.")
        return len(existing_rows)

    students = generate_students(count=missing, start_id=start_id)

    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER)
        writer.writeheader()

        for row in existing_rows:
            writer.writerow(
                {
                    "student_id": row["student_id"],
                    "name": row["name"],
                    "age": "" if pd.isna(row.get("age")) else row["age"],
                    "gpa": "" if pd.isna(row.get("gpa")) else row["gpa"],
                    "attendance": (
                        ""
                        if pd.isna(row.get("attendance"))
                        else row["attendance"]
                    ),
                    "city": row["city"],
                }
            )

        for student in students:
            writer.writerow(
                {
                    "student_id": student.student_id,
                    "name": student.name,
                    "age": student.age,
                    "gpa": "" if student.gpa is None else student.gpa,
                    "attendance": student.attendance,
                    "city": student.city,
                }
            )

    total = len(existing_rows) + missing
    print(f"[seed] wrote {total} rows to {output_path}")
    return total


if __name__ == "__main__":
    target = int(sys.argv[1]) if len(sys.argv) > 1 else TARGET_TOTAL
    seed_csv(target)

    check = pd.read_csv(CSV_INPUT_FILE)
    print(f"[seed] file now has {len(check)} rows")
    print(check.head())