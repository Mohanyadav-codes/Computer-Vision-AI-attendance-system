# Computer Vision AI Attendance System

A real-time face recognition-based attendance system that uses a **state machine** to intelligently track student presence — handling temporary disappearances, requiring consistent detections, and tracking movement throughout a class session.

## How It Works

### State Machine
```
UNKNOWN → DETECTED → CONFIRMED → PRESENT
```

| Transition | Condition |
|-----------|-----------|
| `UNKNOWN → DETECTED` | First face match |
| `DETECTED → CONFIRMED` | 3+ detections within 2 minutes |
| `CONFIRMED → PRESENT` | Seen across a 5+ minute span |
| `DETECTED/CONFIRMED → UNKNOWN` | Disappeared for > 5 minutes |
| `PRESENT` | **Locked in** — never downgrades |

### Handles Real Scenarios
- ✅ Student temporarily blocked by another person → stays tracked
- ✅ Someone walks past the camera → not marked present (too few detections)
- ✅ Student present for the full class → marked PRESENT
- ✅ Student leaves early → state won't reach PRESENT

## Project Structure

```
├── app.py                 # CLI entry point (main menu)
├── config.py              # All tunable thresholds & paths
├── database.py            # SQLite schema + CRUD
├── face_engine.py         # Face detection, encoding (128-d), recognition
├── attendance_engine.py   # State machine + disappearance tolerance
├── register.py            # Student registration with face capture
├── camera.py              # Live camera feed + real-time recognition
└── requirements.txt       # Python dependencies
```

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run
python app.py
```

## Tech Stack
- **Python 3.10+**
- **OpenCV** — camera feed & display
- **face_recognition** (dlib) — 128-dimensional face embeddings
- **SQLite** — zero-config local database
- **NumPy** — embedding math

## Usage

1. **Register students** — captures 5 face samples via webcam, averages embeddings
2. **Start attendance session** — live camera with color-coded state overlays
3. **View reports** — attendance by date and class

## License
MIT
