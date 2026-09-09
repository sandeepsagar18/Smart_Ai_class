import os
import cv2
import pickle
import numpy as np
from pathlib import Path
from utils.config import (
    KNOWN_FACES_DIR, BASE_DIR, DEEPFACE_DIR,
    ARCFACE_SIMILARITY_THRESHOLD, AMBIGUITY_MARGIN
)

os.environ["DEEPFACE_HOME"] = str(DEEPFACE_DIR)
from deepface import DeepFace

EMBEDDINGS_FILE = BASE_DIR / "data" / "embeddings.pkl"


class FaceRecognizer:
    def __init__(self):
        self.model_name = "ArcFace"
        self.known_embeddings = {}
        self.centroids = {}
        # Converted to Cosine Similarity (1.0 = identical, 0.0 = orthogonal)
        # Similarity Threshold 0.65 corresponds to Cosine Distance <= 0.35
        self.min_similarity = ARCFACE_SIMILARITY_THRESHOLD
        self.ambiguity_margin = AMBIGUITY_MARGIN

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
                    face_crop = faces[0]["image"] if faces else cv2.resize(raw_img, (112, 112))

                    res = DeepFace.represent(face_crop, model_name=self.model_name, enforce_detection=False)
                    if len(res) > 0:
                        embeddings_dict[roll_number].append(res[0]["embedding"])
                except Exception as e:
                    print(f"[WARNING] Could not process {img_path}: {e}")

        with open(EMBEDDINGS_FILE, "wb") as f:
            pickle.dump(embeddings_dict, f)

        self.known_embeddings = embeddings_dict
        self._compute_centroids()
        print(f"[SUCCESS] Training complete! Loaded {len(self.known_embeddings)} students with canonical centroid profiles into HD memory.")

    def _match_single_embedding(self, live_embedding, candidate_rolls=None):
        """
        Calculates cosine similarity against all registered student centroids:
        Cosine Similarity = dot(A, B) / (||A|| * ||B||)
        Enforces:
          1. Strict minimum similarity threshold (e.g. >= 0.65).
          2. Ambiguity margin: ensures top match is clearly separated from 2nd closest student.
        """
        live_norm = live_embedding / (np.linalg.norm(live_embedding) + 1e-10)
        
        all_similarities = []
        for roll_number, centroid in self.centroids.items():
            sim = float(np.dot(live_norm, centroid))
            all_similarities.append((roll_number, sim))

        if not all_similarities:
            return "Unknown", 0.0, {"top1_sim": 0.0, "top2_sim": 0.0, "reason": "NO_EMBEDDINGS"}

        all_similarities.sort(key=lambda x: x[1], reverse=True)
        top1_roll, top1_sim = all_similarities[0]
        top2_roll, top2_sim = all_similarities[1] if len(all_similarities) > 1 else ("None", 0.0)

        diag = {
            "top1_roll": top1_roll,
            "top1_sim": round(top1_sim, 4),
            "top2_roll": top2_roll,
            "top2_sim": round(top2_sim, 4),
            "margin": round(top1_sim - top2_sim, 4)
        }

        # Step 6: Strict UNKNOWN condition
        if top1_sim < self.min_similarity:
            diag["reason"] = f"SIMILARITY_BELOW_THRESHOLD ({top1_sim:.3f} < {self.min_similarity:.2f})"
            return "Unknown", round(top1_sim * 100, 2), diag

        # Ambiguity check: prevent confusing similar-looking students
        if len(all_similarities) > 1 and (top1_sim - top2_sim) < self.ambiguity_margin:
            diag["reason"] = f"AMBIGUOUS_MATCH (Top1 {top1_roll}={top1_sim:.2f} vs Top2 {top2_roll}={top2_sim:.2f})"
            return "Unknown", round(top1_sim * 100, 2), diag

        confidence = round(min(100.0, (top1_sim / 1.0) * 100.0), 2)
        diag["reason"] = "VERIFIED_MATCH"
        return top1_roll, confidence, diag

    def recognize(self, face_crop, candidate_rolls=None):
        if not self.centroids:
            return "Unknown", 0.0, {}
        try:
            if face_crop.shape[0] < 20 or face_crop.shape[1] < 20:
                return "Unknown", 0.0, {"reason": "CROP_TOO_SMALL"}

            res = DeepFace.represent(face_crop, model_name=self.model_name, enforce_detection=False)
            if len(res) == 0:
                return "Unknown", 0.0, {"reason": "NO_REPRESENTATION"}

            live_embedding = np.array(res[0]["embedding"])
            return self._match_single_embedding(live_embedding, candidate_rolls=candidate_rolls)
        except Exception as e:
            return "Unknown", 0.0, {"reason": str(e)}

    def recognize_batch(self, face_crops, candidate_rolls=None):
        """
        Batch vectorized ArcFace inference:
        Processes multiple face crops in a single forward pass for high-speed crowd attendance.
        """
        if not face_crops or not self.centroids:
            return [("Unknown", 0.0, {})] * len(face_crops)
        try:
            valid_indices = []
            valid_crops = []
            for idx, crop in enumerate(face_crops):
                if crop.shape[0] >= 20 and crop.shape[1] >= 20:
                    valid_indices.append(idx)
                    valid_crops.append(crop)

            if not valid_crops:
                return [("Unknown", 0.0, {})] * len(face_crops)

            # Single batch forward pass through ArcFace
            batch_results = DeepFace.represent(valid_crops, model_name=self.model_name, enforce_detection=False)
            
            output = [("Unknown", 0.0, {})] * len(face_crops)
            for res_idx, orig_idx in enumerate(valid_indices):
                if res_idx < len(batch_results):
                    emb = np.array(batch_results[res_idx]["embedding"])
                    output[orig_idx] = self._match_single_embedding(emb, candidate_rolls=candidate_rolls)
            return output
        except Exception:
            return [self.recognize(c, candidate_rolls=candidate_rolls) for c in face_crops]