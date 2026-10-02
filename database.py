"""
Database layer — SQLite schema + CRUD for students and attendance.
Uses pickle to serialize numpy face encodings into BLOB columns.
"""

import sqlite3
import pickle
from datetime import datetime, date

from config import DB_PATH


# ─── Connection ───────────────────────────────────────────────

def get_connection():
    """Get a SQLite connection with Row factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ─── Schema ───────────────────────────────────────────────────

def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            roll_number     TEXT NOT NULL UNIQUE,
            class_name      TEXT NOT NULL,
            face_encoding   BLOB NOT NULL,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id        INTEGER NOT NULL,
            date              DATE NOT NULL,
            class_name        TEXT NOT NULL,
            first_seen        TIMESTAMP,
            last_seen         TIMESTAMP,
            total_detections  INTEGER DEFAULT 0,
            status            TEXT DEFAULT 'UNKNOWN',
            FOREIGN KEY (student_id) REFERENCES students(id),
            UNIQUE(student_id, date, class_name)
        )
    ''')

    conn.commit()
    conn.close()
    print("[DB] Database initialized.")


# ─── Students CRUD ────────────────────────────────────────────

def add_student(name, roll_number, class_name, face_encoding):
    """
    Insert a new student with their averaged face encoding.
    Returns the new student ID.
    """
    conn = get_connection()
    cursor = conn.cursor()
    encoding_blob = pickle.dumps(face_encoding)

    cursor.execute(
        'INSERT INTO students (name, roll_number, class_name, face_encoding) '
        'VALUES (?, ?, ?, ?)',
        (name, roll_number, class_name, encoding_blob)
    )
    conn.commit()
    student_id = cursor.lastrowid
    conn.close()
    return student_id


def get_all_students():
    """Fetch all students with deserialized face encodings."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students ORDER BY roll_number')
    rows = cursor.fetchall()
    conn.close()

    students = []
    for row in rows:
        student = dict(row)
        student['face_encoding'] = pickle.loads(student['face_encoding'])
        students.append(student)
    return students


def delete_student(student_id):
    """Delete a student and their attendance records."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM attendance WHERE student_id = ?', (student_id,))
    cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    return deleted > 0


# ─── Attendance CRUD ──────────────────────────────────────────

def get_or_create_attendance(student_id, class_name, today=None):
    """
    Get today's attendance record for a student, or create one.
    Returns a dict with all attendance fields.
    """
    if today is None:
        today = date.today().isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT * FROM attendance WHERE student_id = ? AND date = ? AND class_name = ?',
        (student_id, today, class_name)
    )
    row = cursor.fetchone()

    if row:
        attendance = dict(row)
    else:
        now = datetime.now().isoformat()
        cursor.execute(
            '''INSERT INTO attendance
               (student_id, date, class_name, first_seen, last_seen, total_detections, status)
               VALUES (?, ?, ?, ?, ?, 0, 'UNKNOWN')''',
            (student_id, today, class_name, now, now)
        )
        conn.commit()
        attendance = {
            'id': cursor.lastrowid,
            'student_id': student_id,
            'date': today,
            'class_name': class_name,
            'first_seen': now,
            'last_seen': now,
            'total_detections': 0,
            'status': 'UNKNOWN',
        }

    conn.close()
    return attendance


def update_attendance(attendance_id, last_seen, total_detections, status):
    """Update an existing attendance record."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE attendance SET last_seen = ?, total_detections = ?, status = ? WHERE id = ?',
        (last_seen, total_detections, status, attendance_id)
    )
    conn.commit()
    conn.close()


def get_attendance_report(date_str=None, class_name=None):
    """
    Fetch attendance records joined with student info.
    Optionally filter by date and/or class.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = '''
        SELECT a.*, s.name, s.roll_number
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE 1=1
    '''
    params = []

    if date_str:
        query += ' AND a.date = ?'
        params.append(date_str)
    if class_name:
        query += ' AND a.class_name = ?'
        params.append(class_name)

    query += ' ORDER BY s.roll_number'

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
