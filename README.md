# HAAZIR

HAAZIR is a simple face recognition-based student attendance system built using Python, Flask, OpenCV, NumPy, and Matplotlib. It is designed as a lightweight college project that is easy to understand and demonstrate in a viva.

## Features

- Student registration with details and PRN
- Face capture using webcam
- Face samples saved in dataset folders
- Face recognition model training with LBPH recognizer
- Automatic attendance marking without manual name selection
- Duplicate attendance prevention for the same student on the same day
- Attendance records with date and time
- Simple attendance percentage statistics
- Attendance report graphs using Matplotlib
- CSV-based storage using Python file handling
- Student deletion removes the student record, attendance history, and dataset folder

## Technology Used

- Python
- Flask
- OpenCV
- NumPy
- Matplotlib
- CSV file handling

## Python Libraries

- Flask
- opencv-contrib-python
- numpy
- matplotlib

## Project Structure

HAAZIR/
├── app.py
├── face_recognition.py
├── attendance.py
├── student.py
├── reports.py
├── requirements.txt
├── README.md
├── data/
│   ├── students.csv
│   └── attendance.csv
├── dataset/
├── trainer/
│   └── trainer.yml
├── static/
│   ├── style.css
│   └── generated/
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── register.html
│   ├── attendance.html
│   ├── students.html
│   ├── records.html
│   └── reports.html

## How Face Registration Works

1. A student enters roll number, name, PRN, class, division, and department.
2. After saving the details, the registration page opens a visible live camera preview. Allow camera access when the browser prompts.
3. Click Capture Face Samples; the browser sends camera frames to Flask, which detects and saves 25 cropped face samples in that student's dataset folder.
4. The saved images are used to train the LBPH recognizer.
5. The trained model is stored in trainer/trainer.yml.

Use `http://127.0.0.1:5000/` on the same computer running the Flask app; browser camera access is restricted to localhost or secure HTTPS pages.

## How Attendance Works

1. The user opens the Attendance page.
2. The camera captures the live face.
3. The system compares the detected face with trained student faces.
4. If the face matches a registered student and confidence is acceptable, attendance is stored.
5. If the student already has Present status on the same date, the system prevents duplicate entry.
6. The attendance record is saved in attendance.csv with date and time.

## How to Run

1. Install dependencies:
   pip install -r requirements.txt
2. Start the Flask app:
   python app.py
3. Open the browser:
   http://127.0.0.1:5000/

## CSV Data Format

### students.csv

student_id,name,prn,class,division,department
101,Omkar Madoli,123456,SY CSE,A,CSE

### attendance.csv

student_id,name,date,time,status
101,Omkar Madoli,04-10-2026,09:15:22,Present

## Future Scope

- Add teacher login
- Add semester-wise reports
- Add email notifications
- Add face recognition accuracy improvements
- Add multiple session support

## Important Notes

- All face data stays local on the machine.
- No external cloud service is used.
- The code is intentionally simple and suitable for college-level projects and viva explanations.
