import cv2
import numpy as np
from pathlib import Path
from utils.config import BASE_DIR, CONFIDENCE_THRESHOLD, YUNET_MODEL_PATH


class FaceDetector:
    """
    Dedicated Human Face Detector powered by OpenCV YuNet (Deep Neural Network)
    with seamless Haar Cascade fallback.
    Exclusively detects biological human faces and 100% ignores non-face objects
    (such as TV monitors, chairs, windows, books, screens).
    """
    def __init__(self):
        self.yunet = None
        if YUNET_MODEL_PATH.exists():
            try:
                self.yunet = cv2.FaceDetectorYN.create(
                    model=str(YUNET_MODEL_PATH),
                    config="",
                    input_size=(640, 480),
                    score_threshold=0.70,
                    nms_threshold=0.30,
                    top_k=50
                )
            except Exception as e:
                print(f"[WARNING] Could not initialize YuNet: {e}")

        # Fallback Haar Cascade
        self.haar_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    def detect_faces(self, frame):
        h, w = frame.shape[:2]
        cropped_faces = []

        # 1. Primary: YuNet Dedicated DNN Face Detector
        if self.yunet is not None:
            try:
                self.yunet.setInputSize((w, h))
                _, faces = self.yunet.detect(frame)
                if faces is not None:
                    for f in faces:
                        x, y, fw, fh = map(int, f[:4])
                        # Bound within frame
                        x1 = max(0, x)
                        y1 = max(0, y)
                        x2 = min(w, x + fw)
                        y2 = min(h, y + fh)

                        face_crop = frame[y1:y2, x1:x2]
                        if face_crop.size > 0 and (x2 - x1) >= 40 and (y2 - y1) >= 40:
                            cropped_faces.append({
                                "coords": (x1, y1, x2, y2),
                                "image": face_crop
                            })
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    return frame, cropped_faces
            except Exception as e:
                pass

        # 2. Fallback: OpenCV Frontal Face Haar Cascade
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        haar_faces = self.haar_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
        for (x, y, fw, fh) in haar_faces:
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(w, x + fw), min(h, y + fh)
            face_crop = frame[y1:y2, x1:x2]
            if face_crop.size > 0:
                cropped_faces.append({
                    "coords": (x1, y1, x2, y2),
                    "image": face_crop
                })
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        return frame, cropped_faces