import cv2
import numpy as np
from pathlib import Path
from utils.config import (
    BASE_DIR, YUNET_MODEL_PATH, YUNET_SCORE_THRESHOLD,
    MIN_FACE_SIZE, ENABLE_5POINT_ALIGNMENT
)

# Canonical 5-point landmark coordinates for standard 112x112 ArcFace alignment
# (Right Eye, Left Eye, Nose Tip, Right Mouth Corner, Left Mouth Corner)
ARCFACE_REFERENCE_POINTS = np.array([
    [38.2946, 51.6963],
    [73.5318, 51.5014],
    [56.0252, 71.7366],
    [41.5493, 92.3655],
    [70.7299, 92.2041]
], dtype=np.float32)


def align_face_5point(image, landmarks, target_size=(112, 112)):
    """
    Computes a partial affine transformation (rotation, translation, scale)
    to warp facial landmarks onto canonical ArcFace reference points.
    Prevents head tilt, perspective slant, and camera distortion.
    """
    src_pts = np.array(landmarks, dtype=np.float32)
    tform, _ = cv2.estimateAffinePartial2D(src_pts, ARCFACE_REFERENCE_POINTS)
    if tform is None:
        return cv2.resize(image, target_size)
    aligned = cv2.warpAffine(image, tform, target_size, borderMode=cv2.BORDER_REPLICATE)
    return aligned


class FaceDetector:
    """
    Dedicated Human Face Detector powered by OpenCV YuNet (Deep Neural Network)
    with 5-point landmark extraction and canonical 112x112 ArcFace affine alignment.
    """
    def __init__(self):
        self.yunet = None
        if YUNET_MODEL_PATH.exists():
            try:
                self.yunet = cv2.FaceDetectorYN.create(
                    model=str(YUNET_MODEL_PATH),
                    config="",
                    input_size=(640, 480),
                    score_threshold=YUNET_SCORE_THRESHOLD,
                    nms_threshold=0.30,
                    top_k=50
                )
            except Exception as e:
                print(f"[WARNING] Could not initialize YuNet: {e}")

        # Fallback Haar Cascade
        self.haar_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    def detect_faces(self, frame):
        h, w = frame.shape[:2]
        detected_faces = []

        # 1. Primary: YuNet Dedicated DNN Face Detector
        if self.yunet is not None:
            try:
                self.yunet.setInputSize((w, h))
                _, faces = self.yunet.detect(frame)
                if faces is not None:
                    for f in faces:
                        x, y, fw, fh = map(int, f[:4])
                        score = float(f[-1])
                        
                        # Filter out tiny or truncated detections
                        if fw < MIN_FACE_SIZE or fh < MIN_FACE_SIZE:
                            continue

                        x1 = max(0, x)
                        y1 = max(0, y)
                        x2 = min(w, x + fw)
                        y2 = min(h, y + fh)

                        raw_crop = frame[y1:y2, x1:x2]
                        if raw_crop.size == 0:
                            continue

                        # Extract 5 facial landmarks (Right Eye, Left Eye, Nose, Right Mouth, Left Mouth)
                        landmarks = f[4:14].reshape((5, 2))

                        if ENABLE_5POINT_ALIGNMENT:
                            aligned_face = align_face_5point(frame, landmarks)
                        else:
                            aligned_face = cv2.resize(raw_crop, (112, 112))

                        detected_faces.append({
                            "coords": (x1, y1, x2, y2),
                            "score": score,
                            "landmarks": landmarks,
                            "raw_crop": raw_crop,
                            "image": aligned_face  # Canonical aligned face for ArcFace
                        })
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    return frame, detected_faces
            except Exception as e:
                pass

        # 2. Fallback: OpenCV Frontal Face Haar Cascade
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        haar_faces = self.haar_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(MIN_FACE_SIZE, MIN_FACE_SIZE)
        )
        for (x, y, fw, fh) in haar_faces:
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(w, x + fw), min(h, y + fh)
            raw_crop = frame[y1:y2, x1:x2]
            if raw_crop.size > 0:
                aligned = cv2.resize(raw_crop, (112, 112))
                detected_faces.append({
                    "coords": (x1, y1, x2, y2),
                    "score": 0.85,
                    "landmarks": None,
                    "raw_crop": raw_crop,
                    "image": aligned
                })
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        return frame, detected_faces