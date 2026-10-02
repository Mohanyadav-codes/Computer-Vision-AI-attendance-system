"""
Attendance Engine — state machine + tracking logic.

Each student transitions through:

    UNKNOWN → DETECTED → CONFIRMED → PRESENT

State transitions:
    UNKNOWN  → DETECTED   : First face match
    DETECTED → CONFIRMED  : ≥ DETECTION_THRESHOLD matches within DETECTION_WINDOW
    CONFIRMED → PRESENT   : first_seen → now span ≥ CONFIRMATION_SPAN

Disappearance tolerance:
    If a student vanishes for > DISAPPEARANCE_TOLERANCE and hasn't reached
    PRESENT, their state resets to UNKNOWN. Once PRESENT, state never downgrades.
"""

from datetime import datetime, timedelta

from config import (
    DETECTION_THRESHOLD,
    DETECTION_WINDOW_SECONDS,
    CONFIRMATION_SPAN_SECONDS,
    DISAPPEARANCE_TOLERANCE_SECONDS,
)
import database as db


class StudentTracker:
    """Tracks a single student's attendance state throughout a session."""

    STATES = ("UNKNOWN", "DETECTED", "CONFIRMED", "PRESENT")

    def __init__(self, student_id, student_name, attendance_record):
        self.student_id = student_id
        self.student_name = student_name
        self.attendance_id = attendance_record['id']

        # Restore state from DB (handles session resume)
        self.state = attendance_record.get('status', 'UNKNOWN')
        self.first_seen = (
            datetime.fromisoformat(attendance_record['first_seen'])
            if attendance_record.get('first_seen') else None
        )
        self.last_seen = (
            datetime.fromisoformat(attendance_record['last_seen'])
            if attendance_record.get('last_seen') else None
        )
        self.total_detections = attendance_record.get('total_detections', 0)

        # In-memory sliding window of recent detection timestamps
        self.recent_detections: list[datetime] = []

    # ─── Core API ─────────────────────────────────────────────

    def record_detection(self, timestamp=None):
        """Record a face detection event and advance the state machine."""
        if timestamp is None:
            timestamp = datetime.now()

        # Update timestamps & counters
        self.last_seen = timestamp
        self.total_detections += 1
        self.recent_detections.append(timestamp)

        if self.first_seen is None:
            self.first_seen = timestamp

        # Prune detections outside the sliding window
        cutoff = timestamp - timedelta(seconds=DETECTION_WINDOW_SECONDS)
        self.recent_detections = [t for t in self.recent_detections if t >= cutoff]

        # Evaluate state transitions
        self._advance_state(timestamp)

        # Persist to DB
        self._save()

    def check_disappearance(self, current_time=None):
        """
        Called periodically. If the student hasn't been seen for too long
        and isn't already PRESENT, reset their state.
        """
        if current_time is None:
            current_time = datetime.now()

        if self.last_seen is None:
            return

        # Once PRESENT, never downgrade
        if self.state == "PRESENT":
            return

        gap = (current_time - self.last_seen).total_seconds()

        if gap > DISAPPEARANCE_TOLERANCE_SECONDS:
            self.state = "UNKNOWN"
            self.recent_detections.clear()
            self._save()

    # ─── State Machine ────────────────────────────────────────

    def _advance_state(self, timestamp):
        """Evaluate and apply state transitions in order."""

        # UNKNOWN → DETECTED (first sighting)
        if self.state == "UNKNOWN":
            self.state = "DETECTED"

        # DETECTED → CONFIRMED (enough recent detections)
        if self.state == "DETECTED":
            if len(self.recent_detections) >= DETECTION_THRESHOLD:
                self.state = "CONFIRMED"

        # CONFIRMED → PRESENT (seen across a long enough time span)
        if self.state == "CONFIRMED":
            if self.first_seen is not None:
                span = (timestamp - self.first_seen).total_seconds()
                if span >= CONFIRMATION_SPAN_SECONDS:
                    self.state = "PRESENT"

    # ─── Persistence ──────────────────────────────────────────

    def _save(self):
        """Write current state to the database."""
        db.update_attendance(
            self.attendance_id,
            self.last_seen.isoformat() if self.last_seen else None,
            self.total_detections,
            self.state,
        )


class AttendanceEngine:
    """
    Manages attendance tracking for all students in a class session.

    Usage:
        engine = AttendanceEngine("CSE-A")

        # For each recognized face:
        state = engine.process_recognition(student_id, timestamp)

        # Periodically:
        engine.check_all_disappearances(current_time)
    """

    def __init__(self, class_name):
        self.class_name = class_name
        self.trackers: dict[int, StudentTracker] = {}

        # Load registered students and their encodings
        self.students = []
        self.known_encodings = []
        self.known_ids = []
        self._load_students()

    def _load_students(self):
        """Load all registered students from the database."""
        self.students = db.get_all_students()
        self.known_encodings = [s['face_encoding'] for s in self.students]
        self.known_ids = [s['id'] for s in self.students]

    def get_tracker(self, student_id) -> StudentTracker | None:
        """Get or create a StudentTracker for the given student."""
        if student_id not in self.trackers:
            student = next(
                (s for s in self.students if s['id'] == student_id), None
            )
            if student is None:
                return None

            attendance_record = db.get_or_create_attendance(
                student_id, self.class_name
            )
            self.trackers[student_id] = StudentTracker(
                student_id, student['name'], attendance_record
            )
        return self.trackers[student_id]

    def process_recognition(self, student_id, timestamp=None):
        """
        Called when a student's face is recognized in a frame.
        Returns the student's current attendance state.
        """
        tracker = self.get_tracker(student_id)
        if tracker:
            tracker.record_detection(timestamp)
            return tracker.state
        return None

    def check_all_disappearances(self, current_time=None):
        """Check every tracked student for disappearance timeout."""
        for tracker in self.trackers.values():
            tracker.check_disappearance(current_time)

    def get_status_summary(self):
        """
        Return a dict of {student_name: {state, detections, first_seen, last_seen}}
        for all tracked students.
        """
        summary = {}
        for tracker in self.trackers.values():
            summary[tracker.student_name] = {
                'state': tracker.state,
                'detections': tracker.total_detections,
                'first_seen': (
                    tracker.first_seen.strftime('%H:%M:%S')
                    if tracker.first_seen else '-'
                ),
                'last_seen': (
                    tracker.last_seen.strftime('%H:%M:%S')
                    if tracker.last_seen else '-'
                ),
            }
        return summary
