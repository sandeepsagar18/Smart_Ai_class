import os
import pickle
import numpy as np
from pathlib import Path
from utils.config import KNOWN_FACES_DIR, BASE_DIR, DEEPFACE_DIR

os.environ["DEEPFACE_HOME"] = str(DEEPFACE_DIR)
from deepface import DeepFace

EMBEDDINGS_FILE = BASE_DIR / "data" / "embeddings.pkl"


class FaceRecognizer:
    def __init__(self):
        self.model_name = "ArcFace"
        self.known_embeddings = {}
        self.centroids = {}
        self.threshold = 0.32

        if EMBEDDINGS_FILE.exists():
            with open(EMBEDDINGS_FILE, "rb") as f:
                self.known_embeddings = pickle.load(f)
            self._compute_centroids()

        # Warm up the ArcFace neural network weights in memory to eliminate cold-start delay
        try:
            DeepFace.build_model(self.model_name)
        except Exception as e:
            pass

    def _compute_centroids(self):
        self.centroids = {}
        for roll, embs in self.known_embeddings.items():
            if not embs: continue
            normed = [np.array(e) / (np.linalg.norm(e) + 1e-10) for e in embs]
            c = np.mean(normed, axis=0)
            c = c / (np.linalg.norm(c) + 1e-10)
            self.centroids[roll] = c

    def train_system(self):
        from src.detector import FaceDetector
        print(f"\n[INFO] Training High-Definition {self.model_name} Engine with True Face Cropping...")
        detector = FaceDetector()
        embeddings_dict = {}

        for student_folder in os.listdir(KNOWN_FACES_DIR):
            folder_path = Path(KNOWN_FACES_DIR) / student_folder
            if not folder_path.is_dir(): continue

            roll_number = student_folder
            embeddings_dict[roll_number] = []

            for img_file in os.listdir(folder_path):
                img_path = str(folder_path / img_file)
                try:
                    raw_img = cv2.imread(img_path)
                    if raw_img is None: continue
                    _, faces = detector.detect_faces(raw_img)
                    face_crop = faces[0]["image"] if faces else raw_img

                    res = DeepFace.represent(face_crop, model_name=self.model_name, enforce_detection=False)
                    if len(res) > 0:
                        embeddings_dict[roll_number].append(res[0]["embedding"])
                except Exception as e:
                    print(f"[WARNING] Could not process {img_path}: {e}")

        with open(EMBEDDINGS_FILE, "wb") as f:
            pickle.dump(embeddings_dict, f)

        self.known_embeddings = embeddings_dict
        self._compute_centroids()
        print(f"[SUCCESS] Training complete! Loaded {len(self.known_embeddings)} students with centroid profiles into HD memory.")

    def _match_single_embedding(self, live_embedding, candidate_rolls=None):
        live_norm = live_embedding / (np.linalg.norm(live_embedding) + 1e-10)
        best_match = "Unknown"
        best_distance = float("inf")

        # Prioritize section candidates if available
        search_centroids = self.centroids
        if candidate_rolls:
            candidate_set = set(map(str, candidate_rolls))
            # First pass: check section candidates
            for roll in candidate_set:
                if roll in self.centroids:
                    c_dist = 1.0 - float(np.dot(live_norm, self.centroids[roll]))
                    if c_dist < best_distance:
                        best_distance = c_dist
                        best_match = roll

            if best_distance < self.threshold:
                confidence = round((1 - (best_distance / self.threshold)) * 100, 2)
                return best_match, confidence

        # Full database scan if not resolved
        for roll_number, centroid in search_centroids.items():
            c_dist = 1.0 - float(np.dot(live_norm, centroid))
            if c_dist < best_distance:
                best_distance = c_dist
                best_match = roll_number

        if best_distance < self.threshold:
            confidence = round((1 - (best_distance / self.threshold)) * 100, 2)
            return best_match, confidence
        return "Unknown", 0.0

    def recognize(self, face_crop, candidate_rolls=None):
        if not self.centroids:
            return "Unknown", 0.0
        try:
            if face_crop.shape[0] < 20 or face_crop.shape[1] < 20:
                return "Unknown", 0.0

            res = DeepFace.represent(face_crop, model_name=self.model_name, enforce_detection=False)
            if len(res) == 0: return "Unknown", 0.0

            live_embedding = np.array(res[0]["embedding"])
            return self._match_single_embedding(live_embedding, candidate_rolls=candidate_rolls)
        except Exception:
            return "Unknown", 0.0

    def recognize_batch(self, face_crops, candidate_rolls=None):
        """
        Batch vectorized ArcFace inference:
        Processes multiple face crops in a single forward pass for high-speed crowd attendance.
        """
        if not face_crops or not self.centroids:
            return [("Unknown", 0.0)] * len(face_crops)
        try:
            valid_indices = []
            valid_crops = []
            for idx, crop in enumerate(face_crops):
                if crop.shape[0] >= 20 and crop.shape[1] >= 20:
                    valid_indices.append(idx)
                    valid_crops.append(crop)

            if not valid_crops:
                return [("Unknown", 0.0)] * len(face_crops)

            # Single batch forward pass through ArcFace
            batch_results = DeepFace.represent(valid_crops, model_name=self.model_name, enforce_detection=False)
            
            output = [("Unknown", 0.0)] * len(face_crops)
            for res_idx, orig_idx in enumerate(valid_indices):
                if res_idx < len(batch_results):
                    emb = np.array(batch_results[res_idx]["embedding"])
                    output[orig_idx] = self._match_single_embedding(emb, candidate_rolls=candidate_rolls)
            return output
        except Exception:
            # Fallback to single recognition on error
            return [self.recognize(c, candidate_rolls=candidate_rolls) for c in face_crops]