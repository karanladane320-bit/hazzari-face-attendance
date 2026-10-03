import os
from pathlib import Path

import cv2
import numpy as np

from attendance import mark_attendance
from student import get_student_by_id, load_students

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset"
TRAINER_DIR = BASE_DIR / "trainer"
TRAINER_PATH = TRAINER_DIR / "trainer.yml"
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
RECOGNITION_THRESHOLD = 80.0


def save_face_sample(student_id, frame, total_samples=25):
    """Detect and save one face sample received from the registration page."""
    if not str(student_id).isdigit():
        raise ValueError("Student ID must contain digits only.")

    student_folder = DATASET_DIR / str(student_id)
    student_folder.mkdir(parents=True, exist_ok=True)

    if not os.path.exists(CASCADE_PATH):
        raise FileNotFoundError("Face detection model not found.")

    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    samples = list(student_folder.glob("*.jpg"))
    if len(samples) >= total_samples:
        return {"status": "complete", "samples": len(samples), "message": "All face samples are already captured."}
    if len(faces) == 0:
        return {"status": "no_face", "samples": len(samples), "message": "No face detected. Look at the camera."}
    if len(faces) > 1:
        return {"status": "multiple_faces", "samples": len(samples), "message": "Please keep only one person in front of the camera."}

    x, y, width, height = faces[0]
    face_region = gray[y:y + height, x:x + width]
    resized = cv2.resize(face_region, (100, 100))
    next_sample = len(samples) + 1
    file_name = student_folder / f"{next_sample}.jpg"
    if not cv2.imwrite(str(file_name), resized):
        raise OSError("Could not save the face sample.")

    saved_samples = next_sample
    is_complete = saved_samples >= total_samples
    return {
        "status": "complete" if is_complete else "captured",
        "samples": saved_samples,
        "message": "Face samples captured. Training the model..." if is_complete else "Face detected. Capturing samples..."
    }


def train_face_recognizer():
    """Train the LBPH recognizer using all registered face samples."""
    TRAINER_DIR.mkdir(exist_ok=True)

    faces = []
    labels = []

    for student_dir in DATASET_DIR.iterdir():
        if not student_dir.is_dir():
            continue
        student_id = student_dir.name
        if not student_id.isdigit():
            continue
        for image_path in student_dir.glob("*.jpg"):
            image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            if image is None:
                continue
            faces.append(np.asarray(image, dtype=np.uint8))
            labels.append(int(student_id))

    if len(faces) == 0 or len(labels) == 0:
        raise ValueError("No face data available for training.")

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.asarray(labels, dtype=np.int32))
    recognizer.save(str(TRAINER_PATH))
    return True


def analyze_frame(frame):
    """Detect faces in a frame and return the recognized student id if a valid match is found."""
    if not os.path.exists(TRAINER_PATH):
        raise FileNotFoundError("Model file missing. Please train the face recognizer first.")

    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    if len(faces) == 0:
        return {"status": "No face detected", "student_id": None, "name": None, "confidence": None}
    if len(faces) > 1:
        return {"status": "Multiple faces detected", "student_id": None, "name": None, "confidence": None}

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(str(TRAINER_PATH))
    x, y, w, h = faces[0]
    face = gray[y:y + h, x:x + w]
    face = cv2.resize(face, (100, 100))

    student_id, confidence = recognizer.predict(face)
    student = get_student_by_id(student_id)

    if student is None or confidence > RECOGNITION_THRESHOLD:
        return {"status": "Unknown Student", "student_id": None, "name": None, "confidence": round(confidence, 2)}

    return {
        "status": "Recognized",
        "student_id": student_id,
        "name": student["name"],
        "confidence": round(confidence, 2)
    }


def process_attendance_frame(frame, last_student_id=None):
    """Analyze current frame and mark attendance when valid recognition is found."""
    result = analyze_frame(frame)
    if result["status"] == "Recognized":
        student_id = result["student_id"]
        if last_student_id == student_id:
            return {**result, "attendance_marked": False, "message": "Attendance already marked."}
        attendance_saved = mark_attendance(student_id, result["name"])
        if attendance_saved:
            result["attendance_marked"] = True
            result["message"] = f"Recognized: {result['name']} | Roll No: {student_id} | Status: PRESENT"
        else:
            result["attendance_marked"] = False
            result["message"] = "Attendance already marked."
        return result

    if result["status"] == "Unknown Student":
        result["attendance_marked"] = False
        result["message"] = "Unknown Student"
        return result

    if result["status"] == "Multiple faces detected":
        result["attendance_marked"] = False
        result["message"] = "Please keep only one person in front of the camera."
        return result

    result["attendance_marked"] = False
    result["message"] = "No face detected. Please look at the camera."
    return result
