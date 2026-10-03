import csv
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ATTENDANCE_FILE = DATA_DIR / "attendance.csv"
STUDENTS_FILE = DATA_DIR / "students.csv"


def ensure_attendance_file():
    DATA_DIR.mkdir(exist_ok=True)
    if not ATTENDANCE_FILE.exists():
        with open(ATTENDANCE_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["student_id", "name", "date", "time", "status"])


def load_attendance(date_filter=None, student_id_filter=None):
    """Read attendance records with optional date and student ID filters."""
    ensure_attendance_file()
    records = []
    with open(ATTENDANCE_FILE, "r", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row.get("student_id"):
                if date_filter and row.get("date") != date_filter:
                    continue
                if student_id_filter and str(row.get("student_id")) != str(student_id_filter):
                    continue
                records.append({
                    "student_id": row.get("student_id", ""),
                    "name": row.get("name", ""),
                    "date": row.get("date", ""),
                    "time": row.get("time", ""),
                    "status": row.get("status", "")
                })
    return records


def check_duplicate_attendance(student_id, selected_date):
    """Check whether the student has already been marked Present for today."""
    ensure_attendance_file()
    for record in load_attendance(date_filter=selected_date):
        if str(record["student_id"]) == str(student_id) and record["status"].lower() == "present":
            return True
    return False


def mark_attendance(student_id, name):
    """Add a new attendance record only if it is not a duplicate for the same date."""
    ensure_attendance_file()
    today = datetime.now().strftime("%d-%m-%Y")
    if check_duplicate_attendance(student_id, today):
        return False

    with open(ATTENDANCE_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            student_id,
            name,
            today,
            datetime.now().strftime("%H:%M:%S"),
            "Present"
        ])
    return True


def get_dashboard_stats():
    """Calculate dashboard summary values."""
    from student import load_students

    students = load_students()
    today = datetime.now().strftime("%d-%m-%Y")
    present_records = [record for record in load_attendance(date_filter=today) if record["status"].lower() == "present"]

    total_students = len(students)
    today_present = len(present_records)
    today_absent = max(total_students - today_present, 0)

    attendance_percentage = 0
    if total_students > 0:
        attendance_percentage = round((today_present / total_students) * 100, 2)

    return {
        "total_students": total_students,
        "today_present": today_present,
        "today_absent": today_absent,
        "attendance_percentage": attendance_percentage
    }


def get_absent_students(selected_date):
    """Return students absent on the selected date."""
    from student import load_students

    students = load_students()
    present_students = set()
    present_records = load_attendance(date_filter=selected_date)
    for record in present_records:
        if record["status"].lower() == "present":
            present_students.add(str(record["student_id"]))

    absent_students = []
    for student in students:
        student_id = str(student["student_id"])
        if student_id not in present_students:
            absent_students.append(student)
    return absent_students
