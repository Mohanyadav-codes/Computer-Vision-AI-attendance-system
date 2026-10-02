"""
Global configuration for the CV Attendance System.
Adjust thresholds here to tune behavior.
"""

import os

# ─── Project Paths ────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
FACES_DIR = os.path.join(DATA_DIR, "faces")
DB_PATH = os.path.join(DATA_DIR, "attendance.db")

# ─── Face Recognition ────────────────────────────────────────
FACE_RECOGNITION_TOLERANCE = 0.5       # Lower = stricter matching (0.6 is default)
FACE_RECOGNITION_MODEL = "hog"         # "hog" (CPU, fast) or "cnn" (GPU, accurate)
NUM_REGISTRATION_SAMPLES = 5           # Face captures during registration

# ─── Camera ───────────────────────────────────────────────────
CAMERA_INDEX = 0                       # 0 = default webcam
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
PROCESS_EVERY_N_FRAMES = 3            # Skip frames for performance

# ─── Attendance State Machine ────────────────────────────────
# UNKNOWN → DETECTED → CONFIRMED → PRESENT
#
# DETECTED:  first face match
# CONFIRMED: >= DETECTION_THRESHOLD detections within DETECTION_WINDOW
# PRESENT:   first_seen → last_seen span >= CONFIRMATION_SPAN
#
DETECTION_THRESHOLD = 3                # Detections to move DETECTED → CONFIRMED
DETECTION_WINDOW_SECONDS = 120         # Window for counting detections (2 min)
CONFIRMATION_SPAN_SECONDS = 300        # Time span for CONFIRMED → PRESENT (5 min)
DISAPPEARANCE_TOLERANCE_SECONDS = 300  # Max gap before state reset (5 min)

# ─── Ensure directories exist ────────────────────────────────
os.makedirs(FACES_DIR, exist_ok=True)
