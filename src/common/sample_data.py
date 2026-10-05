"""
sample_data.py - Generate a shared random student dataset.
=========================================================

Produces deterministic pseudo-random students so every source (CSV,
SQL, MongoDB) can be filled with comparable records.

The same `seed` always yields the same students, which keeps the
generated data reproducible.
"""

import random
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import List

# Random seed for reproducibility.
SEED = 20260905

CITIES: List[str] = [
    "Sana'a", "Dhamar", "Ibb", "Taiz", "Hodeidah",
    "Aden", "Mukalla", "Ibb", "Sana'a", "Dhamar",
]

FIRST_NAMES: List[str] = [
    "Ali", "Sara", "Omar", "Noor", "Khaled", "Maryam", "Yousef",
    "Reem", "Ahmed", "Lina", "Fahd", "Huda", "Mazen", "Salma",
    "Waleed", "Aisha", "Younes", "Rana", "Bilal", "Dina",
]

LAST_NAMES: List[str] = [
    "Mohammed", "Ahmed", "Hassan", "Abdullah", "Saleh", "Ali",
    "Al-Hakimi", "Al-Sabri", "Al-Yemeni", "Al-Ariqi",
]

GENDERS: List[str] = ["M", "F"]

STATUSES: List[str] = ["Active", "Graduated", "Suspended"]


@dataclass
class Student:
    """One student record in the flat (CSV/MongoDB) shape."""
    student_id: int
    name: str
    age: int
    gpa: float
    attendance: int
    city: str


def generate_students(
    count: int = 100,
    start_id: int = 1,
    seed: int = SEED,
) -> List[Student]:
    """
    Build `count` random students.

    Some records are deliberately imperfect so the cleaning stage has
    real work to do:
        - a few empty `gpa` values (missing data)
        - a few out-of-range `age` / `attendance` values
        - a few duplicated students

    Parameters
    ----------
    count:
        How many students to generate.
    start_id:
        The first `student_id`.
    seed:
        Random seed for reproducibility.
    """
    rng = random.Random(seed)

    students: List[Student] = []

    for offset in range(count):
        student_id = start_id + offset
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)

        # --- Missing data (about 7%) -------------------------
        gpa: object = round(rng.uniform(1.5, 4.0), 2)
        if rng.random() < 0.07:
            gpa = None

        # --- Invalid values (about 5%) -----------------------
        age = rng.randint(16, 30)
        if rng.random() < 0.05:
            age = rng.choice([-5, 0, 95])

        attendance = rng.randint(55, 100)
        if rng.random() < 0.05:
            attendance = rng.choice([105, 120, -10])

        students.append(
            Student(
                student_id=student_id,
                name=f"{first} {last}",
                age=age,
                gpa=gpa,
                attendance=attendance,
                city=rng.choice(CITIES),
            )
        )

    # --- Duplicate a few students on purpose ---------------
    # Needed by the CSV pipeline to exercise de-duplication, but
    # only possible when there is enough material to copy from.
    if students:
        duplicates = rng.sample(students, k=min(3, len(students)))
        for duplicate in duplicates:
            clone = Student(**asdict(duplicate))
            students.append(clone)

    rng.shuffle(students)
    return students


def generate_sql_students(
    count: int = 100,
    start_id: int = 100,
    seed: int = SEED,
) -> List[dict]:
    """
    Build random students in the SQL schema shape:
    `full_name`, `gender`, `birth_date`, `enrollment_year`, `status`.
    """
    rng = random.Random(seed)
    today = date.today()

    rows: List[dict] = []

    for offset in range(count):
        student_id = start_id + offset
        birth_date = date(rng.randint(1998, 2005), rng.randint(1, 12), rng.randint(1, 28))
        enrollment_year = rng.choice([2022, 2023, 2024, 2025])

        rows.append(
            {
                "student_id": student_id,
                "full_name": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
                "gender": rng.choice(GENDERS),
                "birth_date": birth_date,
                "city": rng.choice(CITIES),
                "enrollment_year": enrollment_year,
                "status": rng.choices(
                    STATUSES, weights=[6, 3, 1]
                )[0],
            }
        )

    return rows


def generate_enrollments(
    student_ids: List[int],
    course_ids: List[int],
    seed: int = SEED,
    max_courses: int = 4,
) -> List[dict]:
    """
    Create random enrollments for the given students.

    Enrollments always reference existing `student_id` and `course_id`
    values so the foreign keys stay valid.
    """
    rng = random.Random(seed)
    semesters = ["Fall", "Spring", "Summer"]
    statuses = ["Active", "Completed", "Dropped"]

    rows: List[dict] = []
    enrollment_id = 1

    for student_id in student_ids:
        chosen = rng.sample(course_ids, k=min(max_courses, len(course_ids)))

        for course_id in chosen:
            semester = rng.choice(semesters)
            enrollment_date = date(2025, 9, 1) + timedelta(days=rng.randint(0, 300))

            rows.append(
                {
                    "enrollment_id": enrollment_id,
                    "student_id": student_id,
                    "course_id": course_id,
                    "semester": semester,
                    "academic_year": "2025-2026",
                    "enrollment_date": enrollment_date,
                    "enrollment_status": rng.choices(
                        statuses, weights=[2, 6, 2]
                    )[0],
                }
            )
            enrollment_id += 1

    return rows


def generate_assessments(
    enrollments: List[dict],
    seed: int = SEED,
) -> List[dict]:
    """
    Create a Quiz / Midterm / Final assessment for every enrollment.

    About 4% of the Final scores are left NULL on purpose so the
    pipelines can practise missing-data handling.
    """
    rng = random.Random(seed)
    types = [("Quiz", 0), ("Midterm", 45), ("Final", 90)]

    rows: List[dict] = []
    assessment_id = 1

    for enrollment in enrollments:
        base = rng.randint(50, 75)

        for assessment_type, day_offset in types:
            score: object = float(
                min(100, max(0, base + rng.randint(0, 20)))
            )
            if assessment_type == "Final" and rng.random() < 0.04:
                score = None

            rows.append(
                {
                    "assessment_id": assessment_id,
                    "student_id": enrollment["student_id"],
                    "course_id": enrollment["course_id"],
                    "assessment_type": assessment_type,
                    "score": score,
                    "assessment_date": enrollment["enrollment_date"]
                    + timedelta(days=day_offset),
                    "semester": enrollment["semester"],
                    "academic_year": enrollment["academic_year"],
                }
            )
            assessment_id += 1

    return rows