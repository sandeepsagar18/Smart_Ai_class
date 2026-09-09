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
        self.threshold = 0.35

        if EMBEDDINGS_FILE.exists():
            with open(EMBEDDINGS_FILE, "rb") as f:
                self.known_embeddings = pickle.load(f)

    def train_system(self):
        print(f"\n[INFO] Training High-Definition {self.model_name} Engine...")
        embeddings_dict = {}

        for student_folder in os.listdir(KNOWN_FACES_DIR):
            folder_path = Path(KNOWN_FACES_DIR) / student_folder
            if not folder_path.is_dir(): continue

            roll_number = student_folder
            embeddings_dict[roll_number] = []

            for img_file in os.listdir(folder_path):
                img_path = str(folder_path / img_file)
                try:
                    res = DeepFace.represent(img_path, model_name=self.model_name, enforce_detection=False)
                    if len(res) > 0:
                        embeddings_dict[roll_number].append(res[0]["embedding"])
                except Exception as e:
                    print(f"[WARNING] Could not process {img_path}: {e}")

        with open(EMBEDDINGS_FILE, "wb") as f:
            pickle.dump(embeddings_dict, f)

        self.known_embeddings = embeddings_dict
        print(f"[SUCCESS] Training complete! Loaded {len(self.known_embeddings)} students into HD memory.")

    def recognize(self, face_crop, candidate_rolls=None):
        if not self.known_embeddings:
            return "Unknown", 0.0
        try:
            if face_crop.shape[0] < 20 or face_crop.shape[1] < 20:
                return "Unknown", 0.0

            res = DeepFace.represent(face_crop, model_name=self.model_name, enforce_detection=False)
            if len(res) == 0: return "Unknown", 0.0

            live_embedding = np.array(res[0]["embedding"])
            best_match = "Unknown"
            best_distance = float("inf")

            # If candidates provided (e.g. section students), search candidate pool first
            search_pool = self.known_embeddings
            effective_threshold = self.threshold
            if candidate_rolls:
                filtered_pool = {k: v for k, v in self.known_embeddings.items() if str(k) in [str(r) for r in candidate_rolls]}
                if filtered_pool:
                    search_pool = filtered_pool
                    # Generous angular tolerance for enrolled section roster
                    effective_threshold = 0.42

            for roll_number, saved_embeddings in search_pool.items():
                for saved_emb in saved_embeddings:
                    saved_emb = np.array(saved_emb)
                    distance = np.dot(live_embedding, saved_emb) / (
                                np.linalg.norm(live_embedding) * np.linalg.norm(saved_emb))
                    cosine_distance = 1 - distance

                    if cosine_distance < best_distance:
                        best_distance = cosine_distance
                        best_match = roll_number

            if best_distance < effective_threshold:
                confidence = round((1 - (best_distance / effective_threshold)) * 100, 2)
                return best_match, confidence
            else:
                return "Unknown", 0.0

        except Exception as e:
            return "Unknown", 0.0