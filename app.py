import time
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, Response, flash, jsonify, render_template, request, redirect, url_for

from attendance import get_absent_students, get_dashboard_stats, load_attendance, mark_attendance
from face_recognition import process_attendance_frame, save_face_sample, train_face_recognizer
from reports import generate_attendance_report
from student import delete_student, get_student_by_id, load_students, save_student

app = Flask(__name__)
app.secret_key = "hazzari-secret"

BASE_DIR = Path(__file__).resolve().parent
FACE_SAMPLE_COUNT = 25

STATUS = {
    "name": "Waiting for a face",
    "student_id": "-",
    "confidence": "-",
    "status": "Ready",
    "message": "No face detected. Please look at the camera."
}


def camera_error_message():
    return "Camera access is unavailable in this environment. Please run HAAZIR on a local machine with a webcam connected and open http://127.0.0.1:5000/ there."


def ensure_data_files():
    base = BASE_DIR / "data"
    base.mkdir(exist_ok=True)
    (BASE_DIR / "dataset").mkdir(exist_ok=True)
    (BASE_DIR / "trainer").mkdir(exist_ok=True)


@app.context_processor
def inject_globals():
    return {
        "app_name": "HAZZARI",
        "tagline": "Your Face. Your Attendance."
    }


@app.route("/")
def index():
    stats = get_dashboard_stats()
    return render_template("index.html", stats=stats)


@app.route("/register", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        student = {
            "student_id": request.form.get("student_id", "").strip(),
            "name": request.form.get("name", "").strip(),
            "prn": request.form.get("prn", "").strip(),
            "class": request.form.get("class", "").strip(),
            "division": request.form.get("division", "").strip(),
            "department": request.form.get("department", "").strip()
        }

        if not all(student.values()):
            flash("Please complete all student details.")
            return redirect(url_for("register_student"))
        if not student["student_id"].isdigit():
            flash("Student ID / Roll Number must contain digits only.")
            return redirect(url_for("register_student"))

        try:
            save_student(student)
            flash("Student details saved. Allow camera access, then start face capture below.")
            return redirect(url_for("register_student", student_id=student["student_id"]))
        except Exception as exc:
            flash(str(exc))
            return redirect(url_for("register_student"))

    student_id = request.args.get("student_id", "").strip()
    registered_student = get_student_by_id(student_id) if student_id else None
    sample_count = 0
    if registered_student:
        sample_dir = BASE_DIR / "dataset" / student_id
        sample_count = len(list(sample_dir.glob("*.jpg"))) if sample_dir.exists() else 0
    return render_template(
        "register.html",
        registered_student=registered_student,
        sample_count=sample_count,
        sample_target=FACE_SAMPLE_COUNT
    )


@app.route("/capture_face/<student_id>", methods=["POST"])
def capture_face(student_id):
    if not student_id.isdigit() or not get_student_by_id(student_id):
        return jsonify({"error": "Register a valid student before capturing face samples."}), 400

    image_file = request.files.get("frame")
    if image_file is None:
        return jsonify({"error": "No camera frame was received."}), 400

    image_data = np.frombuffer(image_file.read(), dtype=np.uint8)
    frame = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
    if frame is None:
        return jsonify({"error": "The camera frame could not be read. Please try again."}), 400

    try:
        result = save_face_sample(student_id, frame, FACE_SAMPLE_COUNT)
        return jsonify(result)
    except (FileNotFoundError, OSError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/finish_face_capture/<student_id>", methods=["POST"])
def finish_face_capture(student_id):
    if not student_id.isdigit() or not get_student_by_id(student_id):
        return jsonify({"error": "Student record not found."}), 400

    sample_dir = BASE_DIR / "dataset" / student_id
    sample_count = len(list(sample_dir.glob("*.jpg"))) if sample_dir.exists() else 0
    if sample_count < FACE_SAMPLE_COUNT:
        return jsonify({"error": f"Capture all {FACE_SAMPLE_COUNT} face samples before training."}), 400

    try:
        train_face_recognizer()
        return jsonify({"message": "Face samples captured and model trained successfully."})
    except (FileNotFoundError, OSError, ValueError, AttributeError) as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/attendance")
def attendance_page():
    return render_template("attendance.html")


@app.route("/video_feed")
def video_feed():
    def generate_frames():
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            STATUS.update({
                "name": "Camera unavailable",
                "student_id": "-",
                "confidence": "-",
                "status": "Camera Error",
                "message": camera_error_message()
            })
            return

        last_student_id = None
        while True:
            success, frame = camera.read()
            if not success:
                STATUS["message"] = "Unable to read frames from camera."
                break

            try:
                result = process_attendance_frame(frame, last_student_id)
                if result.get("student_id") and result["status"] == "Recognized":
                    if result.get("attendance_marked"):
                        last_student_id = result["student_id"]
                    else:
                        last_student_id = result["student_id"]

                STATUS.update({
                    "name": result.get("name", "Unknown"),
                    "student_id": result.get("student_id", "-"),
                    "confidence": result.get("confidence", "-"),
                    "status": result.get("status", "Waiting"),
                    "message": result.get("message", "No face detected. Please look at the camera.")
                })

                if result.get("message"):
                    cv2.putText(frame, result["message"], (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                if result.get("name"):
                    cv2.putText(frame, f"Name: {result['name']}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                ret, buffer = cv2.imencode(".jpg", frame)
                frame_data = buffer.tobytes()
                yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame_data + b"\r\n")
                time.sleep(0.1)
            except Exception as exc:
                STATUS["message"] = str(exc)
                break

        camera.release()

    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/status")
def status_endpoint():
    return jsonify(STATUS)


@app.route("/students")
def students():
    student_list = load_students()
    return render_template("students.html", students=student_list)


@app.route("/delete_student/<student_id>", methods=["POST"])
def delete_student_route(student_id):
    try:
        delete_student(student_id)
        flash("Student record, attendance history, and face dataset deleted successfully.")
    except Exception as exc:
        flash(str(exc))
    return redirect(url_for("students"))


@app.route("/records")
def records():
    selected_date = request.args.get("date", "")
    student_id = request.args.get("student_id", "")
    attendance = load_attendance(date_filter=selected_date or None, student_id_filter=student_id or None)
    return render_template("records.html", records=attendance, students=load_students(), selected_date=selected_date, selected_student_id=student_id)


@app.route("/reports")
def reports():
    selected_date = request.args.get("date", "")
    report_file = None
    try:
        generate_attendance_report()
        report_file = url_for("static", filename="generated/attendance_report.png")
    except Exception as exc:
        flash(str(exc))

    absent_students = get_absent_students(selected_date) if selected_date else []
    return render_template("reports.html", report_file=report_file, selected_date=selected_date, absent_students=absent_students)


@app.route("/mark_demo")
def mark_demo():
    sample_student = get_student_by_id("101")
    if sample_student:
        mark_attendance("101", sample_student["name"])
        flash("Demo attendance marked successfully.")
    else:
        flash("No sample student found.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    ensure_data_files()
    print("HAAZIR is running...")
    app.run(host="127.0.0.1", port=5000, debug=True)
