"""
Student Registration — capture face samples via webcam, compute
an averaged 128-d embedding, and store in the database.
"""

import os
import cv2
import numpy as np

from config import CAMERA_INDEX, NUM_REGISTRATION_SAMPLES, FACES_DIR
from face_engine import detect_faces, get_face_encodings, crop_face
import database as db


def register_student():
    """Interactive registration flow: collect info → capture faces → save."""

    print("\n── Student Registration ──\n")
    name = input("  Name        : ").strip()
    roll_number = input("  Roll Number : ").strip()
    class_name = input("  Class       : ").strip()

    if not all([name, roll_number, class_name]):
        print("\n  [ERROR] All fields are required.")
        return

    print(f"\n  Registering: {name} | Roll: {roll_number} | Class: {class_name}")
    print(f"  Will capture {NUM_REGISTRATION_SAMPLES} face samples.")
    print("  Controls: SPACE = capture  |  ESC = cancel\n")

    camera = cv2.VideoCapture(CAMERA_INDEX)
    if not camera.isOpened():
        print("  [ERROR] Cannot open camera.")
        return

    encodings_collected = []
    sample_count = 0

    # Directory to save face crops for this student
    student_dir = os.path.join(
        FACES_DIR, f"{roll_number}_{name.replace(' ', '_')}"
    )
    os.makedirs(student_dir, exist_ok=True)

    while sample_count < NUM_REGISTRATION_SAMPLES:
        ret, frame = camera.read()
        if not ret:
            print("  [ERROR] Camera read failed.")
            break

        display = frame.copy()
        face_locations = detect_faces(frame)

        # Draw bounding boxes on all detected faces
        for (top, right, bottom, left) in face_locations:
            cv2.rectangle(display, (left, top), (right, bottom), (0, 255, 0), 2)

        # HUD text
        cv2.putText(
            display,
            f"Samples: {sample_count}/{NUM_REGISTRATION_SAMPLES}  |  SPACE=capture  ESC=cancel",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2,
        )

        cv2.imshow("Register Student", display)
        key = cv2.waitKey(1) & 0xFF

        # ── ESC → cancel ──
        if key == 27:
            print("  [CANCELLED] Registration aborted.")
            camera.release()
            cv2.destroyAllWindows()
            return

        # ── SPACE → capture sample ──
        if key == 32:
            if len(face_locations) == 0:
                print("  ✗ No face detected — try again.")
            elif len(face_locations) > 1:
                print("  ✗ Multiple faces detected — only the student should be in frame.")
            else:
                encodings, _ = get_face_encodings(frame, face_locations)
                if encodings:
                    encodings_collected.append(encodings[0])

                    # Save the cropped face image
                    face_img = crop_face(frame, face_locations[0])
                    cv2.imwrite(
                        os.path.join(student_dir, f"sample_{sample_count + 1}.jpg"),
                        face_img,
                    )
                    sample_count += 1
                    print(f"  ✓ Sample {sample_count}/{NUM_REGISTRATION_SAMPLES} captured!")
                else:
                    print("  ✗ Could not encode face — try again.")

    camera.release()
    cv2.destroyAllWindows()

    # ── Validate & save ──
    if len(encodings_collected) < NUM_REGISTRATION_SAMPLES:
        print("\n  [ERROR] Not enough samples. Registration failed.")
        return

    # Average embeddings for a robust representation
    avg_encoding = np.mean(encodings_collected, axis=0)

    try:
        student_id = db.add_student(name, roll_number, class_name, avg_encoding)
        print(f"\n  ✓ Student registered successfully!")
        print(f"    ID    : {student_id}")
        print(f"    Name  : {name}")
        print(f"    Roll  : {roll_number}")
        print(f"    Class : {class_name}")
        print(f"    Faces : {student_dir}")
    except sqlite3.IntegrityError:
        print(f"\n  [ERROR] Roll number '{roll_number}' already exists.")
    except Exception as e:
        print(f"\n  [ERROR] {e}")
