"""
Live Camera — real-time face detection, recognition, and attendance tracking.

Opens the webcam, detects faces every Nth frame, matches them against
registered students, and feeds results into the AttendanceEngine.

On-screen overlay shows each student's name, state, and confidence.
A status panel in the top-left corner shows all tracked students.

Press 'q' to end the session and print the final attendance summary.
"""

import time
import cv2
from datetime import datetime

from config import (
    CAMERA_INDEX,
    FRAME_WIDTH,
    FRAME_HEIGHT,
    PROCESS_EVERY_N_FRAMES,
)
from face_engine import detect_faces, get_face_encodings, recognize_face
from attendance_engine import AttendanceEngine


# Color coding per state (BGR)
COLORS = {
    "UNKNOWN":   (128, 128, 128),   # Gray
    "DETECTED":  (0, 165, 255),     # Orange
    "CONFIRMED": (0, 255, 255),     # Yellow
    "PRESENT":   (0, 255, 0),       # Green
}


def run_attendance_session():
    """Main attendance loop — blocks until user presses 'q'."""

    class_name = input("\n  Enter class name (e.g., CSE-A): ").strip()
    if not class_name:
        print("  [ERROR] Class name is required.")
        return

    engine = AttendanceEngine(class_name)

    if not engine.students:
        print("  [ERROR] No registered students. Register students first.")
        return

    print(f"\n  ── Attendance Session ──")
    print(f"  Class            : {class_name}")
    print(f"  Registered       : {len(engine.students)} students")
    print(f"  Press 'q' to end.\n")

    camera = cv2.VideoCapture(CAMERA_INDEX)
    if not camera.isOpened():
        print("  [ERROR] Cannot open camera.")
        return

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    frame_count = 0
    last_disappearance_check = time.time()

    # Cache for face data between processed frames (smoother drawing)
    cached_faces = []   # list of (location, student_id, confidence, state, name)

    while True:
        ret, frame = camera.read()
        if not ret:
            print("  [ERROR] Camera read failed.")
            break

        frame_count += 1
        display = frame.copy()
        now = datetime.now()

        # ── Process faces every Nth frame ──
        if frame_count % PROCESS_EVERY_N_FRAMES == 0:
            face_locations = detect_faces(frame)
            cached_faces = []

            if face_locations:
                encodings, locations = get_face_encodings(frame, face_locations)

                for encoding, location in zip(encodings, locations):
                    student_id, confidence = recognize_face(
                        encoding, engine.known_encodings, engine.known_ids
                    )

                    if student_id is not None:
                        state = engine.process_recognition(student_id, now)
                        tracker = engine.get_tracker(student_id)
                        cached_faces.append(
                            (location, student_id, confidence, state, tracker.student_name)
                        )
                    else:
                        cached_faces.append(
                            (location, None, None, None, "Unknown")
                        )

            # ── Disappearance check every 30s ──
            if time.time() - last_disappearance_check > 30:
                engine.check_all_disappearances(now)
                last_disappearance_check = time.time()

        # ── Draw face boxes from cache ──
        for (location, sid, conf, state, name) in cached_faces:
            top, right, bottom, left = location

            if sid is not None:
                color = COLORS.get(state, (255, 255, 255))
                cv2.rectangle(display, (left, top), (right, bottom), color, 2)

                label = f"{name} [{state}]"
                cv2.putText(display, label, (left, top - 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
                cv2.putText(display, f"Conf: {conf:.2f}", (left, top - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            else:
                cv2.rectangle(display, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.putText(display, "Unknown", (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)

        # ── Status overlay ──
        _draw_status_overlay(display, engine)

        # ── Clock ──
        cv2.putText(display, now.strftime("%H:%M:%S"),
                     (FRAME_WIDTH - 130, 30),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow(f"Attendance — {class_name}", display)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera.release()
    cv2.destroyAllWindows()

    _print_final_summary(engine)


# ─── Overlay helpers ──────────────────────────────────────────

def _draw_status_overlay(frame, engine):
    """Semi-transparent panel in the top-left showing all tracked students."""
    summary = engine.get_status_summary()
    if not summary:
        return

    panel_h = 28 + len(summary) * 22
    panel_w = 320

    # Semi-transparent black background
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (panel_w, panel_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    cv2.putText(frame, "ATTENDANCE STATUS", (10, 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    y = 40
    for name, info in summary.items():
        color = COLORS.get(info['state'], (255, 255, 255))
        icon = "+" if info['state'] == "PRESENT" else ">"
        text = f"{icon} {name}: {info['state']} ({info['detections']}x)"
        cv2.putText(frame, text, (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.43, color, 1)
        y += 22


def _print_final_summary(engine):
    """Print attendance summary to the console when session ends."""
    print()
    print("=" * 60)
    print("             ATTENDANCE SUMMARY")
    print("=" * 60)

    summary = engine.get_status_summary()

    if not summary:
        print("  No students were detected during this session.")
        print("=" * 60)
        return

    present = 0
    for name, info in summary.items():
        icon = "PASS" if info['state'] == "PRESENT" else "----"
        print(
            f"  [{icon}]  {name:<20}  {info['state']:<12}  "
            f"detections={info['detections']:<4}  "
            f"{info['first_seen']} → {info['last_seen']}"
        )
        if info['state'] == "PRESENT":
            present += 1

    total = len(engine.students)
    print(f"\n  Result: {present}/{total} students marked PRESENT")
    print("=" * 60)
