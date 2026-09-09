import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Data Directories
KNOWN_FACES_DIR = BASE_DIR / "data" / "known_faces"
UNKNOWN_FACES_DIR = BASE_DIR / "data" / "unknown_faces"
ATTENDANCE_DIR = BASE_DIR / "data" / "attendance_records"
CLASS_PHOTOS_DIR = BASE_DIR / "data" / "class_photos"

# Model Directories
YOLO_WEIGHTS_CANDIDATE = BASE_DIR / "models" / "yolo_weights" / "yolov8n-face.pt"
if not YOLO_WEIGHTS_CANDIDATE.exists():
    if (BASE_DIR / "yolov8n.pt").exists():
        YOLO_WEIGHTS_CANDIDATE = BASE_DIR / "yolov8n.pt"
YOLO_WEIGHTS = YOLO_WEIGHTS_CANDIDATE
DEEPFACE_DIR = BASE_DIR / "models"

# Camera Settings
CAMERA_ID = 0
CONFIDENCE_THRESHOLD = 0.50
ATTENDANCE_WINDOW_MINUTES = 15