import cv2
import time
import re
import pandas as pd
import sqlite3
import numpy as np
from pathlib import Path
from datetime import datetime
from src.detector import FaceDetector
from src.recognizer import FaceRecognizer
from src.anti_spoof import evaluate_liveness
from src.database import get_student_info, save_attendance_entry, get_students_by_class, generate_file_checksum, log_security_event
from utils.config import ATTENDANCE_DIR, CLASS_PHOTOS_DIR, UNKNOWN_FACES_DIR, CAMERA_ID, BASE_DIR

DB_PATH = BASE_DIR / "data" / "smartclass.db"


def clean_filename(text):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', str(text))


def start_attendance(subject_info=None):
    print("\n" + "=" * 55)
    print("   SUBJECT & SECTION-SPECIFIC BATCH ATTENDANCE")
    print("=" * 55)

    if subject_info is None:
        subject_info = {
            "id": 0,
            "subject_code": "ALL",
            "subject_name": "General Session",
            "teacher_name": "Faculty",
            "teacher_emp_id": "",
            "degree": None,
            "year": None,
            "branch": None,
            "section": None
        }

    sub_id = subject_info.get("id", 0)
    sub_code = clean_filename(subject_info.get("subject_code", "GEN"))
    sub_name = subject_info.get("subject_name", "General Session")
    teacher_name = subject_info.get("teacher_name", "Faculty")
    teacher_emp_id = subject_info.get("teacher_emp_id", "")
    target_degree = subject_info.get("degree")
    target_year = subject_info.get("year")
    target_branch = subject_info.get("branch")
    target_section = subject_info.get("section")

    class_title = f"{target_degree or ''} {target_year or ''} {target_branch or 'ALL'} Sec {target_section or 'ALL'}".strip()

    # Automatically fetch enrolled students belonging to this section
    enrolled_students = get_students_by_class(target_degree, target_year, target_branch, target_section)
    enrolled_count = len(enrolled_students)

    print(f"[TEACHER]  {teacher_name}" + (f" (Emp ID: {teacher_emp_id})" if teacher_emp_id else ""))
    print(f"[SUBJECT]  {sub_code} - {sub_name}")
    print(f"[CLASS]    {class_title} -> {enrolled_count} Students Enrolled in Section")
    print("=" * 55)

    detector = FaceDetector()
    recognizer = FaceRecognizer()

    if not recognizer.known_embeddings:
        print("[ERROR] AI Brain empty. Train model first!")
        return {"error": "AI Brain is empty. Please train the model first."}

    ATTENDANCE_DIR.mkdir(parents=True, exist_ok=True)
    CLASS_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(CAMERA_ID)

    # Force High Definition
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    time.sleep(2)

    NUM_SHOTS = 5
    REQUIRED_MATCHES = 2
    captured_frames = []

    # Extract target section student roll numbers for context-aware priority matching
    enrolled_roll_numbers = [str(s[0]) for s in enrolled_students] if enrolled_students else []

    print("[INFO] Initiating Multi-Shot Batch Capture with Live Multi-Face Overlays...")

    # PHASE 1: BATCH CAPTURE WITH REAL-TIME MULTI-FACE DETECTION
    for i in range(NUM_SHOTS):
        start_wait = time.time()
        while time.time() - start_wait < 2.5:
            ret, frame = cap.read()
            if not ret: break

            display_frame = frame.copy()
            time_left = 2.5 - (time.time() - start_wait)

            # Detect multiple faces in live preview so teacher sees all students being captured
            _, live_faces = detector.detect_faces(display_frame)
            active_count = len(live_faces)

            # Draw session banner
            cv2.rectangle(display_frame, (10, 10), (750, 155), (20, 20, 20), -1)
            cv2.rectangle(display_frame, (10, 10), (750, 155), (0, 200, 255), 2)

            cv2.putText(display_frame, f"Subject: {sub_code} ({class_title})", (25, 38),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            teacher_display = f"Teacher: {teacher_name}" + (f" [{teacher_emp_id}]" if teacher_emp_id else "")
            cv2.putText(display_frame, teacher_display, (25, 68),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
            cv2.putText(display_frame, f"Section Enrolled: {enrolled_count} Students | Live Faces: {active_count}", (25, 95),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 200), 1)
            cv2.putText(display_frame, f"Scan Shot {i + 1}/{NUM_SHOTS} - Scanning All Faces: {int(time_left) + 1}s", (25, 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

            cv2.imshow("SmartClass Vision - Section Attendance Scan", display_frame)
            cv2.waitKey(1)

        # Flush camera buffer to guarantee a fresh snapshot
        for _ in range(3):
            cap.grab()
        ret, frame = cap.read()
        if ret:
            captured_frames.append(frame.copy())
            photo_name = f"ClassAudit_{sub_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_Shot{i + 1}.jpg"
            cv2.imwrite(str(CLASS_PHOTOS_DIR / photo_name), frame)
            print(f"[CAPTURE] Secured High-Res Image: {photo_name}")

            # Elegant capture visual confirmation (no harsh all-white flash screen)
            feedback_frame = frame.copy()
            cv2.rectangle(feedback_frame, (0, 0), (frame.shape[1], frame.shape[0]), (0, 255, 0), 10)
            cv2.rectangle(feedback_frame, (frame.shape[1] // 2 - 280, 20), (frame.shape[1] // 2 + 280, 85), (20, 20, 20), -1)
            cv2.rectangle(feedback_frame, (frame.shape[1] // 2 - 280, 20), (frame.shape[1] // 2 + 280, 85), (0, 255, 0), 2)
            cv2.putText(feedback_frame, f"SHOT {i + 1}/{NUM_SHOTS} SECURED", (frame.shape[1] // 2 - 210, 62),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
            cv2.imshow("SmartClass Vision - Section Attendance Scan", feedback_frame)
            cv2.waitKey(100)

    cap.release()

    # PHASE 2: AI PROCESSING (SECTION-AWARE MULTI-STUDENT RECOGNITION)
    processing_screen = np.zeros((400, 800, 3), dtype="uint8")
    cv2.putText(processing_screen, "Captures Complete.", (50, 110), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0), 2)
    cv2.putText(processing_screen, f"Cross-checking all faces against {class_title}...",
                (50, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 2)
    cv2.putText(processing_screen, f"Prioritizing {enrolled_count} enrolled students in section...",
                (50, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
    cv2.imshow("SmartClass Vision - Section Attendance Scan", processing_screen)
    cv2.waitKey(100)

    print(f"\n[INFO] Cross-referencing captures with Section Roster ({len(enrolled_roll_numbers)} enrolled candidates)...")
    student_detections = {}
    spoof_incidents = 0

    for f_idx, frame in enumerate(captured_frames):
        processed_frame, cropped_faces = detector.detect_faces(frame)
        print(f"[SHOT {f_idx + 1}] Detected {len(cropped_faces)} faces in frame")
        for face_data in cropped_faces:
            face_crop = face_data["image"]

            # BIOMETRIC LIVENESS & ANTI-SPOOFING ASSESSMENT
            is_live, l_score, l_reason = evaluate_liveness(face_crop)
            if not is_live:
                spoof_incidents += 1
                spoof_ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                UNKNOWN_FACES_DIR.mkdir(parents=True, exist_ok=True)
                spoof_path = UNKNOWN_FACES_DIR / f"spoof_{sub_code}_{spoof_ts}.jpg"
                cv2.imwrite(str(spoof_path), face_crop)
                print(f"[SECURITY ALERT - SPOOF DETECTED] Score: {l_score}%, Reason: {l_reason}")
                log_security_event("SPOOF_ATTEMPT", "CRITICAL", teacher_name,
                                   f"Biometric spoof rejected in {sub_code} ({l_reason}, Score: {l_score}%). Snapshot: {spoof_path.name}")
                continue

            # Prioritize matching against enrolled students of this section first!
            roll_number, confidence = recognizer.recognize(face_crop, candidate_rolls=enrolled_roll_numbers)
            if roll_number != "Unknown":
                student_detections[roll_number] = student_detections.get(roll_number, 0) + 1
                print(f"   -> Identified {roll_number} (Conf={confidence}%)")

    cv2.destroyAllWindows()

    # PHASE 3: CONSENSUS, SECTION FILTER & EXPORT
    attendance_list = []
    rejected_wrong_section = []
    timestamp = datetime.now().strftime("%H:%M:%S")
    today_date = datetime.now().strftime("%Y-%m-%d")

    print("\n" + "=" * 55)
    print("   SECTION VALIDATION & VERIFICATION RESULTS")
    print("=" * 55)

    for roll, count in student_detections.items():
        info = get_student_info(roll)
        if not info:
            continue

        s_roll, s_name, s_gender, s_degree, s_year, s_branch, s_section, _ = info

        # Strict Section & Branch validation
        match_degree = (target_degree is None or s_degree.strip().upper() == target_degree.strip().upper())
        match_year = (target_year is None or s_year.strip().upper() == target_year.strip().upper())
        match_branch = (target_branch is None or s_branch.strip().upper() == target_branch.strip().upper())
        match_section = (target_section is None or s_section.strip().upper() == target_section.strip().upper())

        is_correct_section = match_degree and match_year and match_branch and match_section

        if count >= REQUIRED_MATCHES:
            if is_correct_section:
                print(f"[VERIFIED - SECTION MATCH] {s_name} ({s_roll}) -> {s_branch} Sec {s_section} -> PRESENT")
                attendance_list.append({
                    "Subject Code": sub_code,
                    "Subject Name": sub_name,
                    "Teacher Name": teacher_name,
                    "Degree": s_degree,
                    "Year": s_year,
                    "Branch": s_branch,
                    "Section": s_section,
                    "Roll Number": s_roll,
                    "Name": s_name,
                    "Time Marked": timestamp,
                    "Status": "Present"
                })
                # Persist to database
                save_attendance_entry(
                    sub_id, sub_code, sub_name, teacher_name,
                    s_roll, s_name, s_branch, s_section,
                    today_date, timestamp, "Present"
                )
            else:
                print(f"[REJECTED - WRONG SECTION] Student {s_name} ({s_roll}) is enrolled in {s_branch} Sec {s_section}, NOT target {target_branch} Sec {target_section}! Attendance denied.")
                rejected_wrong_section.append({
                    "roll": s_roll, "name": s_name, "enrolled": f"{s_branch} {s_section}"
                })
        else:
            print(f"[REJECTED - LOW MATCHES] {s_name} ({s_roll}) only detected in {count}/{NUM_SHOTS} shots -> Glitch discarded.")

    filename = None
    hmac_sig = None
    if attendance_list:
        clean_sec = clean_filename(target_section or "ALL")
        clean_br = clean_filename(target_branch or "ALL")
        filename = f"Attendance_{sub_code}_{clean_br}_{clean_sec}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = ATTENDANCE_DIR / filename
        df = pd.DataFrame(attendance_list)
        df.to_csv(filepath, index=False)
        print(f"\n[SUCCESS] Saved section attendance to: {filename}")

        # Cryptographically sign the attendance file with HMAC-SHA256
        f_hash, hmac_sig = generate_file_checksum(filepath, created_by=f"{teacher_name} ({teacher_emp_id})")
        print(f"[SECURITY] Cryptographic HMAC-SHA256 Registered: {hmac_sig[:16]}...")
    else:
        print("\n[INFO] No students from the target section passed verification threshold.")

    return {
        "verified": len(attendance_list),
        "rejected_section": len(rejected_wrong_section),
        "spoofs_rejected": spoof_incidents,
        "enrolled_total": enrolled_count,
        "filename": filename,
        "hmac_signature": hmac_sig
    }