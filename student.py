import csv
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STUDENTS_FILE = DATA_DIR / "students.csv"
DATASET_DIR = BASE_DIR / "dataset"


def ensure_files():
    DATA_DIR.mkdir(exist_ok=True)
    DATASET_DIR.mkdir(exist_ok=True)
    if not STUDENTS_FILE.exists():
        with open(STUDENTS_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["student_id", "name", "prn", "class", "division", "department"])


def load_students():
    """Read student data from CSV and return a list of dictionaries."""
    ensure_files()
    students = []
    with open(STUDENTS_FILE, "r", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row.get("student_id"):
                students.append({
                    "student_id": row.get("student_id", ""),
                    "name": row.get("name", ""),
                    "prn": row.get("prn", ""),
                    "class": row.get("class", ""),
                    "division": row.get("division", ""),
                    "department": row.get("department", "")
                })
    return students


def get_student_by_id(student_id):
    for student in load_students():
        if str(student["student_id"]) == str(student_id):
            return student
    return None


def save_student(student):
    """Save student details to the CSV file."""
    ensure_files()
    student_id = str(student["student_id"]).strip()
    if not student_id:
        raise ValueError("Student ID is required.")

    if get_student_by_id(student_id):
        raise ValueError(f"Student ID {student_id} already exists.")

    with open(STUDENTS_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            student["student_id"],
            student["name"],
            student["prn"],
            student["class"],
            student["division"],
            student["department"]
        ])

    student_folder = DATASET_DIR / student_id
    student_folder.mkdir(exist_ok=True)
    return student_id


def delete_student(student_id):
    """Delete a student record, all attendance entries, and their face dataset folder."""
    students = load_students()
    new_students = [student for student in students if str(student["student_id"]) != str(student_id)]

    with open(STUDENTS_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["student_id", "name", "prn", "class", "division", "department"])
        for student in new_students:
            writer.writerow([
                student["student_id"],
                student["name"],
                student["prn"],
                student["class"],
                student["division"],
                student["department"]
            ])

    attendance_path = BASE_DIR / "data" / "attendance.csv"
    if attendance_path.exists():
        rows = []
        with open(attendance_path, "r", newline="") as file:
            reader = csv.reader(file)
            rows = list(reader)
        if rows:
            filtered_rows = [row for row in rows if str(row[0]) != str(student_id)]
            with open(attendance_path, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerows(filtered_rows)

    student_folder = DATASET_DIR / str(student_id)
    if student_folder.exists():
        for file in student_folder.iterdir():
            if file.is_file():
                file.unlink()
        student_folder.rmdir()

    return True
