import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Data Directories
KNOWN_FACES_DIR = BASE_DIR / "data" / "known_faces"
UNKNOWN_FACES_DIR = BASE_DIR / "data" / "unknown_faces"
ATTENDANCE_DIR = BASE_DIR / "data" / "attendance_records"
CLASS_PHOTOS_DIR = BASE_DIR / "data" / "class_photos"

# Model Directories
YUNET_MODEL_PATH = BASE_DIR / "models" / "face_detection_yunet_2023mar.onnx"
DEEPFACE_DIR = BASE_DIR / "models"

# Camera Settings
CAMERA_ID = 0
CONFIDENCE_THRESHOLD = 0.50
ATTENDANCE_WINDOW_MINUTES = 15