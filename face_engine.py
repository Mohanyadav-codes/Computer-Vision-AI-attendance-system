"""
Face Engine — detection, alignment, encoding, and recognition.
Wraps the face_recognition library (dlib under the hood).
Produces 128-dimensional face embeddings.
"""

import cv2
import numpy as np
import face_recognition

from config import FACE_RECOGNITION_TOLERANCE, FACE_RECOGNITION_MODEL


def detect_faces(frame):
    """
    Detect all faces in a BGR frame.

    Returns:
        list of (top, right, bottom, left) tuples
    """
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb, model=FACE_RECOGNITION_MODEL)
    return locations


def get_face_encodings(frame, face_locations=None):
    """
    Compute 128-d face encodings for every face in the frame.

    Args:
        frame:          BGR image (numpy array)
        face_locations: optional pre-detected locations

    Returns:
        (encodings, face_locations) — parallel lists
    """
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    if face_locations is None:
        face_locations = face_recognition.face_locations(rgb, model=FACE_RECOGNITION_MODEL)

    encodings = face_recognition.face_encodings(rgb, face_locations)
    return encodings, face_locations


def recognize_face(face_encoding, known_encodings, known_ids, tolerance=None):
    """
    Match a single face encoding against a gallery of known encodings.

    Args:
        face_encoding:   128-d numpy array
        known_encodings: list of 128-d numpy arrays
        known_ids:       list of student IDs (parallel to known_encodings)
        tolerance:       max distance for a match (lower = stricter)

    Returns:
        (student_id, confidence) or (None, None)
    """
    if tolerance is None:
        tolerance = FACE_RECOGNITION_TOLERANCE

    if not known_encodings:
        return None, None

    # Compute Euclidean distances to every known face
    distances = face_recognition.face_distance(known_encodings, face_encoding)
    best_idx = int(np.argmin(distances))
    best_distance = distances[best_idx]

    if best_distance <= tolerance:
        confidence = round(1.0 - best_distance, 3)
        return known_ids[best_idx], confidence

    return None, None


def crop_face(frame, face_location, margin=20):
    """
    Crop a detected face from the frame with a pixel margin.

    Args:
        frame:          BGR image
        face_location:  (top, right, bottom, left) tuple
        margin:         extra pixels around the face

    Returns:
        Cropped BGR image
    """
    top, right, bottom, left = face_location
    h, w = frame.shape[:2]

    top = max(0, top - margin)
    right = min(w, right + margin)
    bottom = min(h, bottom + margin)
    left = max(0, left - margin)

    return frame[top:bottom, left:right]
