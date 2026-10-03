import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from attendance import load_attendance
from student import load_students

BASE_DIR = Path(__file__).resolve().parent
GENERATED_DIR = BASE_DIR / "static" / "generated"
REPORT_FILE = GENERATED_DIR / "attendance_report.png"


def generate_attendance_report():
    """Generate a simple attendance report graph as an image file."""
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    students = load_students()
    records = load_attendance()

    present_count = 0
    absent_count = len(students)
    student_attendance = {student["student_id"]: 0 for student in students}
    daily_counts = {}

    for record in records:
        if record["status"].lower() == "present":
            present_count += 1
            absent_count = max(absent_count - 1, 0)
            student_attendance[record["student_id"]] = student_attendance.get(record["student_id"], 0) + 1
        if record["date"]:
            daily_counts[record["date"]] = daily_counts.get(record["date"], 0) + 1

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Present vs Absent pie chart
    labels = ["Present", "Absent"]
    total_presence = present_count + absent_count
    if total_presence == 0:
        sizes = [1, 1]
    else:
        sizes = [present_count, absent_count]
    axes[0].pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
    axes[0].set_title("Present vs Absent")

    # Student-wise attendance bar chart
    if students:
        student_ids = [student["student_id"] for student in students]
        values = [student_attendance.get(student["student_id"], 0) for student in students]
        axes[1].bar(student_ids, values, color="steelblue")
        axes[1].set_title("Student-wise Attendance")
        axes[1].set_xlabel("Roll No")
        axes[1].set_ylabel("Present Days")
        axes[1].tick_params(axis="x", rotation=45)
    else:
        axes[1].text(0.5, 0.5, "No students registered", ha="center", va="center")
        axes[1].set_title("Student-wise Attendance")

    # Daily attendance count line chart
    if daily_counts:
        dates = list(daily_counts.keys())
        counts = list(daily_counts.values())
        axes[2].plot(dates, counts, marker="o", color="green")
        axes[2].set_title("Daily Attendance Count")
        axes[2].set_xlabel("Date")
        axes[2].set_ylabel("Count")
        axes[2].tick_params(axis="x", rotation=45)
    else:
        axes[2].text(0.5, 0.5, "No attendance data", ha="center", va="center")
        axes[2].set_title("Daily Attendance Count")

    fig.tight_layout()
    fig.savefig(REPORT_FILE)
    plt.close(fig)
    return str(REPORT_FILE)
