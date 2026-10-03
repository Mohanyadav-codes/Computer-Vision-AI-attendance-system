# Computer Vision AI Attendance System

A real-time face recognition-based attendance system that uses a **state machine** to intelligently track student presence — handling temporary disappearances, requiring consistent detections, and tracking movement throughout a class session.

Now featuring a modern **React Admin Panel** built with Tailwind CSS v4, served by a lightweight **Flask REST API**.

## How It Works

### State Machine
```text
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

## Tech Stack
- **Frontend**: React, Vite, Tailwind CSS v4, Lucide React, React Router
- **Backend**: Flask (Python 3.10+), REST API, MJPEG Streaming
- **CV Pipeline**: OpenCV, `face_recognition` (dlib), NumPy
- **Database**: SQLite (Zero-config local storage)

## Project Structure

```
├── server.py              # Main Flask REST API & Static File Server
├── config.py              # Tunable thresholds, camera settings
├── database.py            # SQLite schema + CRUD operations
├── face_engine.py         # Face detection, encoding (128-d)
├── attendance_engine.py   # State machine & tracker logic
├── frontend/              # React Application (Vite)
│   ├── src/               # React components & pages
│   └── dist/              # Compiled static assets (Served by Flask)
└── requirements.txt       # Python dependencies
```

## Setup & Run

The system is configured to serve the built React frontend directly from Flask, meaning you only need to run **one server in production**.

### 1. Install Backend Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies & Build
```bash
cd frontend
npm install
npm run build
cd ..
```

### 3. Run the Application
```bash
python server.py
```
Open **[http://localhost:5000](http://localhost:5000)** in your browser to access the beautiful React Admin Panel!

## Local Development (Two Servers)
If you are developing the UI and want hot-reloading:

1. **Terminal 1 (Flask API)**:
```bash
python server.py
```
2. **Terminal 2 (React Vite Dev Server)**:
```bash
cd frontend
npm run dev
```
Then open `http://localhost:5173`.

## Features
1. **Dashboard** — Live stats and recent attendance logs.
2. **Student Registration** — Interactive UI with a live camera preview, captures 5 face samples, and averages them for accuracy.
3. **Live Attendance** — Real-time MJPEG camera stream overlaid with bounding boxes and color-coded state tracking.
4. **Reports** — Filterable attendance reports with CSV export.
5. **Dynamic Settings** — Adjust CV thresholds and timing constraints in real-time from the UI.

## License
MIT
