"""
CV Attendance System — Main Entry Point

Interactive CLI menu:
  1. Register students (face capture + embedding)
  2. Start live attendance session
  3. View registered students
  4. View attendance reports
  5. Exit
"""

import sys
from datetime import date

from database import init_db, get_all_students, get_attendance_report
from register import register_student
from camera import run_attendance_session


def main():
    """Initialize DB and run the main menu loop."""
    init_db()

    while True:
        print()
        print("=" * 50)
        print("       CV ATTENDANCE SYSTEM")
        print("=" * 50)
        print("  1.  Register New Student")
        print("  2.  Start Attendance Session")
        print("  3.  View Registered Students")
        print("  4.  View Attendance Report")
        print("  5.  Exit")
        print("-" * 50)

        choice = input("  Select option [1-5]: ").strip()

        # ── 1. Register ──
        if choice == "1":
            register_student()

        # ── 2. Attendance ──
        elif choice == "2":
            run_attendance_session()

        # ── 3. List Students ──
        elif choice == "3":
            _show_students()

        # ── 4. Report ──
        elif choice == "4":
            _show_report()

        # ── 5. Exit ──
        elif choice == "5":
            print("\n  Goodbye!\n")
            sys.exit(0)

        else:
            print("\n  Invalid option — enter 1-5.")


def _show_students():
    """Display all registered students in a table."""
    students = get_all_students()

    if not students:
        print("\n  No students registered yet.")
        return

    print(f"\n  Registered Students ({len(students)})")
    print(f"  {'ID':<5} {'Name':<22} {'Roll':<12} {'Class':<10}")
    print("  " + "-" * 50)
    for s in students:
        print(
            f"  {s['id']:<5} {s['name']:<22} "
            f"{s['roll_number']:<12} {s['class_name']:<10}"
        )


def _show_report():
    """Display attendance report filtered by date and optional class."""
    date_str = input("  Date (YYYY-MM-DD) [today]: ").strip()
    if not date_str:
        date_str = date.today().isoformat()

    class_filter = input("  Class (leave blank for all): ").strip() or None

    report = get_attendance_report(date_str, class_filter)

    if not report:
        print(f"\n  No attendance records for {date_str}.")
        return

    print(f"\n  Attendance Report — {date_str}")
    print(
        f"  {'Name':<20} {'Roll':<10} {'Status':<12} "
        f"{'Detections':<12} {'First Seen':<10} {'Last Seen':<10}"
    )
    print("  " + "-" * 74)

    for r in report:
        first = r['first_seen'][11:19] if r.get('first_seen') else '-'
        last = r['last_seen'][11:19] if r.get('last_seen') else '-'
        icon = "✓" if r['status'] == 'PRESENT' else " "
        print(
            f"  {icon} {r['name']:<18} {r['roll_number']:<10} "
            f"{r['status']:<12} {r['total_detections']:<12} "
            f"{first:<10} {last:<10}"
        )


if __name__ == "__main__":
    main()
