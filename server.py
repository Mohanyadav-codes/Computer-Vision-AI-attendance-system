"""
Flask Web Server — Admin panel + API for the CV Attendance System.

Serves the web frontend, handles camera streaming via MJPEG,
and exposes REST API endpoints for all operations.
"""

import os
import io
import csv
import base64
import threading
import time

import cv2
import numpy as np
from datetime import datetime, date
from flask import (
    Flask, request, jsonify,
    Response, redirect, url_for,
)
from flask_cors import CORS

import config
from database import (
    init_db, add_student, get_all_students, delete_student,
    get_attendance_report, get_or_create_attendance,
)
from face_engine import detect_faces, get_face_encodings, recognize_face, crop_face
from attendance_engine import AttendanceEngine

# Set static folder to the React build directory
app = Flask(__name__, static_folder='frontend/dist', static_url_path='/')
CORS(app)

# ═══════════════════════════════════════════════════════════════
#  Serve React App
# ═══════════════════════════════════════════════════════════════

@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

@app.errorhandler(404)
def not_found(e):
    # For React Router to handle client-side routing
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return app.send_static_file('index.html')



# ═══════════════════════════════════════════════════════════════
#  Camera Manager — thread-safe, lazy-open camera
# ═══════════════════════════════════════════════════════════════

class CameraManager:
    def __init__(self):
        self._camera = None
        self._lock = threading.Lock()

    def get_frame(self):
        with self._lock:
            if self._camera is None or not self._camera.isOpened():
                self._camera = cv2.VideoCapture(config.CAMERA_INDEX)
                self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
                self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
            ok, frame = self._camera.read()
            return frame if ok else None

    def release(self):
        with self._lock:
            if self._camera is not None:
                self._camera.release()
                self._camera = None


camera_mgr = CameraManager()


# ═══════════════════════════════════════════════════════════════
#  Session State
# ═══════════════════════════════════════════════════════════════

class SessionState:
    def __init__(self):
        self.engine: AttendanceEngine | None = None
        self.active = False
        self.class_name: str | None = None
        self.started_at: datetime | None = None


session = SessionState()


# ═══════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════

def _b64_encode_image(img):
    """Encode a BGR image to base64 JPEG string."""
    _, buf = cv2.imencode('.jpg', img)
    return base64.b64encode(buf).decode('utf-8')


def _b64_decode_image(b64_str):
    """Decode a base64 string to a BGR numpy image."""
    if ',' in b64_str:
        b64_str = b64_str.split(',', 1)[1]
    data = base64.b64decode(b64_str)
    arr = np.frombuffer(data, np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


STATUS_COLORS = {
    "UNKNOWN":   (128, 128, 128),
    "DETECTED":  (0, 165, 255),
    "CONFIRMED": (0, 255, 255),
    "PRESENT":   (0, 255, 0),
}


# ═══════════════════════════════════════════════════════════════
#  API — Core Data
# ═══════════════════════════════════════════════════════════════

@app.route('/api/students', methods=['GET'])
def api_get_students():
    """Get all students."""
    students = get_all_students()
    safe_students = []
    for s in students:
        safe = {k: v for k, v in s.items() if k != 'face_encoding'}
        safe_students.append(safe)
    return jsonify(safe_students)

@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    """Get current settings."""
    settings = {
        'CAMERA_INDEX': config.CAMERA_INDEX,
        'FRAME_WIDTH': config.FRAME_WIDTH,
        'FRAME_HEIGHT': config.FRAME_HEIGHT,
        'PROCESS_EVERY_N_FRAMES': config.PROCESS_EVERY_N_FRAMES,
        'FACE_RECOGNITION_TOLERANCE': config.FACE_RECOGNITION_TOLERANCE,
        'FACE_RECOGNITION_MODEL': config.FACE_RECOGNITION_MODEL,
        'NUM_REGISTRATION_SAMPLES': config.NUM_REGISTRATION_SAMPLES,
        'DETECTION_THRESHOLD': config.DETECTION_THRESHOLD,
        'DETECTION_WINDOW_SECONDS': config.DETECTION_WINDOW_SECONDS,
        'CONFIRMATION_SPAN_SECONDS': config.CONFIRMATION_SPAN_SECONDS,
        'DISAPPEARANCE_TOLERANCE_SECONDS': config.DISAPPEARANCE_TOLERANCE_SECONDS,
    }
    return jsonify(settings)



# ═══════════════════════════════════════════════════════════════
#  API — Students
# ═══════════════════════════════════════════════════════════════

@app.route('/api/students/register', methods=['POST'])
def api_register_student():
    """Register a student with base64 face images from the browser."""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        roll_number = data.get('roll_number', '').strip()
        class_name = data.get('class_name', '').strip()
        encodings_b64 = data.get('encodings', [])

        if not all([name, roll_number, class_name]):
            return jsonify({'error': 'All fields are required'}), 400

        if len(encodings_b64) < config.NUM_REGISTRATION_SAMPLES:
            return jsonify({'error': f'Need {config.NUM_REGISTRATION_SAMPLES} face samples'}), 400

        # Decode the encodings sent from capture endpoint
        encodings = []
        for enc_b64 in encodings_b64:
            enc_bytes = base64.b64decode(enc_b64)
            enc_array = np.frombuffer(enc_bytes, dtype=np.float64)
            encodings.append(enc_array)

        # Average for robust representation
        avg_encoding = np.mean(encodings, axis=0)

        student_id = add_student(name, roll_number, class_name, avg_encoding)
        return jsonify({'success': True, 'student_id': student_id})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/students/<int:student_id>', methods=['DELETE'])
def api_delete_student(student_id):
    """Delete a student by ID."""
    if delete_student(student_id):
        return jsonify({'success': True})
    return jsonify({'error': 'Student not found'}), 404


# ═══════════════════════════════════════════════════════════════
#  API — Registration Camera
# ═══════════════════════════════════════════════════════════════

def _gen_registration_frames():
    """MJPEG generator: camera with face-detection boxes for registration."""
    while True:
        frame = camera_mgr.get_frame()
        if frame is None:
            time.sleep(0.03)
            continue

        faces = detect_faces(frame)
        color = (0, 255, 0) if len(faces) == 1 else (0, 0, 255)

        for (top, right, bottom, left) in faces:
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

        status = f"Faces: {len(faces)}"
        cv2.putText(frame, status, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        _, buf = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n')


@app.route('/api/register/feed')
def api_register_feed():
    """MJPEG stream for the registration page camera."""
    return Response(
        _gen_registration_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
    )


@app.route('/api/register/capture', methods=['POST'])
def api_register_capture():
    """Capture a single face from the camera, return face image + encoding."""
    frame = camera_mgr.get_frame()
    if frame is None:
        return jsonify({'error': 'Camera not available'}), 500

    faces = detect_faces(frame)
    if len(faces) == 0:
        return jsonify({'error': 'No face detected'}), 400
    if len(faces) > 1:
        return jsonify({'error': 'Multiple faces — only one person should be in frame'}), 400

    encodings, _ = get_face_encodings(frame, faces)
    if not encodings:
        return jsonify({'error': 'Could not compute face encoding'}), 400

    # Crop face for thumbnail
    face_img = crop_face(frame, faces[0])
    face_b64 = _b64_encode_image(face_img)

    # Encode the 128-d vector as base64 bytes for transport
    encoding_b64 = base64.b64encode(encodings[0].tobytes()).decode('utf-8')

    return jsonify({
        'success': True,
        'face_image': face_b64,
        'encoding': encoding_b64,
    })


# ═══════════════════════════════════════════════════════════════
#  API — Attendance Session
# ═══════════════════════════════════════════════════════════════

@app.route('/api/attendance/start', methods=['POST'])
def api_start_session():
    """Start a live attendance session for a class."""
    data = request.get_json()
    class_name = data.get('class_name', '').strip()

    if not class_name:
        return jsonify({'error': 'Class name is required'}), 400

    session.engine = AttendanceEngine(class_name)
    session.active = True
    session.class_name = class_name
    session.started_at = datetime.now()

    if not session.engine.students:
        session.active = False
        return jsonify({'error': 'No students registered'}), 400

    return jsonify({
        'success': True,
        'student_count': len(session.engine.students),
    })


@app.route('/api/attendance/stop', methods=['POST'])
def api_stop_session():
    """Stop the active attendance session and return summary."""
    if not session.active:
        return jsonify({'error': 'No active session'}), 400

    summary = session.engine.get_status_summary()
    session.active = False
    session.engine = None
    session.class_name = None
    session.started_at = None
    camera_mgr.release()

    return jsonify({'success': True, 'summary': summary})


@app.route('/api/attendance/status')
def api_attendance_status():
    """Get current session status and per-student states."""
    if not session.active or not session.engine:
        return jsonify({'session_active': False})

    elapsed = ''
    if session.started_at:
        delta = datetime.now() - session.started_at
        mins, secs = divmod(int(delta.total_seconds()), 60)
        elapsed = f"{mins:02d}:{secs:02d}"

    return jsonify({
        'session_active': True,
        'class_name': session.class_name,
        'elapsed': elapsed,
        'summary': session.engine.get_status_summary(),
    })


def _gen_attendance_frames():
    """MJPEG generator: camera with recognition + state overlays."""
    frame_count = 0
    last_check = time.time()

    while session.active and session.engine:
        frame = camera_mgr.get_frame()
        if frame is None:
            time.sleep(0.03)
            continue

        frame_count += 1
        now = datetime.now()
        display = frame.copy()

        # Process every Nth frame
        if frame_count % config.PROCESS_EVERY_N_FRAMES == 0:
            face_locations = detect_faces(frame)

            if face_locations:
                encodings, locations = get_face_encodings(frame, face_locations)

                for encoding, loc in zip(encodings, locations):
                    top, right, bottom, left = loc

                    student_id, confidence = recognize_face(
                        encoding,
                        session.engine.known_encodings,
                        session.engine.known_ids,
                    )

                    if student_id is not None:
                        state = session.engine.process_recognition(student_id, now)
                        tracker = session.engine.get_tracker(student_id)
                        color = STATUS_COLORS.get(state, (255, 255, 255))

                        cv2.rectangle(display, (left, top), (right, bottom), color, 2)
                        label = f"{tracker.student_name} [{state}]"
                        cv2.putText(display, label, (left, top - 25),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
                        cv2.putText(display, f"{confidence:.2f}", (left, top - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                    else:
                        cv2.rectangle(display, (left, top), (right, bottom), (0, 0, 255), 2)
                        cv2.putText(display, "Unknown", (left, top - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)

            # Disappearance check every 30s
            if time.time() - last_check > 30:
                session.engine.check_all_disappearances(now)
                last_check = time.time()

        # Timestamp overlay
        cv2.putText(display, now.strftime("%H:%M:%S"),
                    (display.shape[1] - 130, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        _, buf = cv2.imencode('.jpg', display)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n')


@app.route('/api/attendance/feed')
def api_attendance_feed():
    """MJPEG stream for the live attendance session."""
    if not session.active:
        return jsonify({'error': 'No active session'}), 400
    return Response(
        _gen_attendance_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
    )


# ═══════════════════════════════════════════════════════════════
#  API — Reports
# ═══════════════════════════════════════════════════════════════

@app.route('/api/reports/data')
def api_reports_data():
    """Get attendance report as JSON."""
    date_str = request.args.get('date', date.today().isoformat())
    class_name = request.args.get('class_name', '').strip() or None
    report = get_attendance_report(date_str, class_name)
    return jsonify(report)


@app.route('/api/reports/export')
def api_reports_export():
    """Download attendance report as CSV."""
    date_str = request.args.get('date', date.today().isoformat())
    class_name = request.args.get('class_name', '').strip() or None
    report = get_attendance_report(date_str, class_name)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['Name', 'Roll Number', 'Class', 'Date', 'Status',
                     'Detections', 'First Seen', 'Last Seen'])
    for r in report:
        writer.writerow([
            r.get('name', ''), r.get('roll_number', ''),
            r.get('class_name', ''), r.get('date', ''),
            r.get('status', ''), r.get('total_detections', 0),
            r.get('first_seen', ''), r.get('last_seen', ''),
        ])

    return Response(
        buf.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=attendance_{date_str}.csv'
        },
    )


# ═══════════════════════════════════════════════════════════════
#  API — Settings
# ═══════════════════════════════════════════════════════════════

@app.route('/api/settings', methods=['POST'])
def api_update_settings():
    """Update config values at runtime."""
    data = request.get_json()

    # Type mapping for safe casting
    INT_KEYS = {
        'CAMERA_INDEX', 'FRAME_WIDTH', 'FRAME_HEIGHT',
        'PROCESS_EVERY_N_FRAMES', 'NUM_REGISTRATION_SAMPLES',
        'DETECTION_THRESHOLD', 'DETECTION_WINDOW_SECONDS',
        'CONFIRMATION_SPAN_SECONDS', 'DISAPPEARANCE_TOLERANCE_SECONDS',
    }
    FLOAT_KEYS = {'FACE_RECOGNITION_TOLERANCE'}
    STR_KEYS = {'FACE_RECOGNITION_MODEL'}

    for key, value in data.items():
        if hasattr(config, key):
            if key in INT_KEYS:
                setattr(config, key, int(value))
            elif key in FLOAT_KEYS:
                setattr(config, key, float(value))
            elif key in STR_KEYS:
                setattr(config, key, str(value))

    return jsonify({'success': True})


# ═══════════════════════════════════════════════════════════════
#  API — Stats (for dashboard AJAX)
# ═══════════════════════════════════════════════════════════════

@app.route('/api/stats')
def api_stats():
    """Dashboard statistics."""
    students = get_all_students()
    total = len(students)
    classes = sorted(set(s['class_name'] for s in students))

    today = date.today().isoformat()
    report = get_attendance_report(today)
    present = sum(1 for r in report if r.get('status') == 'PRESENT')

    return jsonify({
        'total_students': total,
        'classes': classes,
        'today_present': present,
        'today_absent': total - present,
    })


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    init_db()
    print("\n  Open http://localhost:5000 in your browser\n")
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
