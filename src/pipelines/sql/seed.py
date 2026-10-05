"""
seed.py - Fill PostgreSQL with random student records.
======================================================

Inserts random students, enrollments and assessments so the SQL
pipeline works on about 100 students instead of 15.

Existing rows are preserved: only the missing ids are added, and all
foreign keys stay valid.

Usage
-----
    python src/pipelines/sql/seed.py [count]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import text

from common.sample_data import (
    generate_assessments,
    generate_enrollments,
    generate_sql_students,
)
from pipelines.sql.extractor import get_engine

TARGET_TOTAL = 100

INSERT_STUDENT = """
INSERT INTO students
    (student_id, full_name, gender, birth_date,
     city, enrollment_year, status)
VALUES
    (:student_id, :full_name, :gender, :birth_date,
     :city, :enrollment_year, :status)
"""

INSERT_ENROLLMENT = """
INSERT INTO enrollments
    (enrollment_id, student_id, course_id, semester,
     academic_year, enrollment_date, enrollment_status)
VALUES
    (:enrollment_id, :student_id, :course_id, :semester,
     :academic_year, :enrollment_date, :enrollment_status)
"""

INSERT_ASSESSMENT = """
INSERT INTO assessments
    (assessment_id, student_id, course_id, assessment_type,
     score, assessment_date, semester, academic_year)
VALUES
    (:assessment_id, :student_id, :course_id, :assessment_type,
     :score, :assessment_date, :semester, :academic_year)
"""


def seed_postgresql(count: int = TARGET_TOTAL) -> dict:
    """
    Insert random records so the `students` table holds about `count` rows.

    Returns
    -------
    dict
        A summary of what was inserted and the final table counts.
    """
    engine = get_engine()

    with engine.begin() as connection:
        existing = connection.execute(
            text("SELECT COUNT(*) FROM students")
        ).scalar()

        missing = max(0, count - existing)

        if missing == 0:
            print(
                f"[seed] students already holds {existing} rows; "
                "nothing to add."
            )
            return {
                "students": 0,
                "enrollments": 0,
                "assessments": 0,
                "totals": {},
            }

        highest_id = connection.execute(
            text("SELECT COALESCE(MAX(student_id), 0) FROM students")
        ).scalar()
        highest_course = connection.execute(
            text("SELECT COALESCE(MAX(course_id), 100) FROM courses")
        ).scalar()
        highest_enrollment = connection.execute(
            text("SELECT COALESCE(MAX(enrollment_id), 0) FROM enrollments")
        ).scalar()
        highest_assessment = connection.execute(
            text("SELECT COALESCE(MAX(assessment_id), 0) FROM assessments")
        ).scalar()

        students = generate_sql_students(
            count=missing,
            start_id=highest_id + 1,
        )

        connection.execute(
            text(INSERT_STUDENT),
            [
                {
                    "student_id": row["student_id"],
                    "full_name": row["full_name"],
                    "gender": row["gender"],
                    "birth_date": row["birth_date"],
                    "city": row["city"],
                    "enrollment_year": row["enrollment_year"],
                    "status": row["status"],
                }
                for row in students
            ],
        )

        student_ids = [row["student_id"] for row in students]
        course_ids = list(range(highest_course - 5, highest_course + 1))

        enrollments = generate_enrollments(
            student_ids=student_ids,
            course_ids=course_ids,
        )
        assessments = generate_assessments(enrollments)

        for row in enrollments:
            row["enrollment_id"] += highest_enrollment
        for row in assessments:
            row["assessment_id"] += highest_assessment

        connection.execute(
            text(INSERT_ENROLLMENT),
            [
                {
                    "enrollment_id": row["enrollment_id"],
                    "student_id": row["student_id"],
                    "course_id": row["course_id"],
                    "semester": row["semester"],
                    "academic_year": row["academic_year"],
                    "enrollment_date": row["enrollment_date"],
                    "enrollment_status": row["enrollment_status"],
                }
                for row in enrollments
            ],
        )

        connection.execute(
            text(INSERT_ASSESSMENT),
            [
                {
                    "assessment_id": row["assessment_id"],
                    "student_id": row["student_id"],
                    "course_id": row["course_id"],
                    "assessment_type": row["assessment_type"],
                    "score": row["score"],
                    "assessment_date": row["assessment_date"],
                    "semester": row["semester"],
                    "academic_year": row["academic_year"],
                }
                for row in assessments
            ],
        )

        totals = {
            table: connection.execute(
                text(f"SELECT COUNT(*) FROM {table}")
            ).scalar()
            for table in (
                "students",
                "instructors",
                "courses",
                "enrollments",
                "assessments",
            )
        }

    return {
        "students": missing,
        "enrollments": len(enrollments),
        "assessments": len(assessments),
        "totals": totals,
    }


if __name__ == "__main__":
    target = int(sys.argv[1]) if len(sys.argv) > 1 else TARGET_TOTAL
    summary = seed_postgresql(target)

    print(
        f"[seed] inserted {summary['students']} students, "
        f"{summary['enrollments']} enrollments, "
        f"{summary['assessments']} assessments"
    )
    for table, count in summary["totals"].items():
        print(f"[seed] {table}: {count}")