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

# Biometric & Computer Vision Quality Gates
MIN_FACE_SIZE = 70               # Minimum face width/height in pixels
BLUR_THRESHOLD = 150.0           # Minimum Laplacian variance for motion blur rejection
MIN_BRIGHTNESS = 40.0            # Minimum average luminance (reject underexposed)
MAX_BRIGHTNESS = 225.0           # Maximum average luminance (reject overexposed)
MIN_CONTRAST = 25.0              # Minimum standard deviation of pixels
MAX_YAW_RATIO = 0.22             # Landmark asymmetry cutoff: abs(NoseX - MidEyesX) / EyeDistance

# YuNet Detection & ArcFace Recognition Thresholds
YUNET_SCORE_THRESHOLD = 0.75     # DNN face detection confidence cutoff
ARCFACE_SIMILARITY_THRESHOLD = 0.65 # Cosine similarity required to verify identity (distance <= 0.35)
AMBIGUITY_MARGIN = 0.06          # Minimum separation between top-1 and top-2 candidate similarities

# Temporal Consensus & Attendance Logic
TOTAL_CAPTURE_SHOTS = 7          # Total multi-angle shots per session
REQUIRED_CONSISTENT_VOTES = 5    # Required matching votes out of total shots (5 of 7)
SHOT_COUNTDOWN_SECONDS = 1.2     # Countdown interval between shots

# Features
ENABLE_5POINT_ALIGNMENT = True   # Standard ArcFace 112x112 affine transformation
DEBUG_MODE = True                # Render rich real-time diagnostic overlay