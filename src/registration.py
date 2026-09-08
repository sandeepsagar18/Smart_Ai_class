import cv2
import time
import shutil
from pathlib import Path
from src.database import add_student, delete_student, student_exists, get_student_info
from src.detector import FaceDetector
from utils.config import KNOWN_FACES_DIR, CAMERA_ID


def search_student_record(roll_number):
    record = get_student_info(roll_number)
    if record:
        student_dir = Path(KNOWN_FACES_DIR) / roll_number
        image_count = len(list(student_dir.glob("*.jpg"))) if student_dir.exists() else 0
        return True, record, image_count
    return False, None, 0


def delete_existing_student(roll_number):
    if not student_exists(roll_number):
        return False, f"Roll Number {roll_number} not found in database."

    delete_student(roll_number)
    student_dir = Path(KNOWN_FACES_DIR) / roll_number
    if student_dir.exists():
        shutil.rmtree(student_dir)
    return True, f"All records and images for {roll_number} deleted successfully."


def get_camera(camera_id=CAMERA_ID):
    """Attempt to open camera with DirectShow backend first for fast, reliable Windows access."""
    for backend in [cv2.CAP_DSHOW, None]:
        for cid in [camera_id, 0, 1]:
            try:
                if backend is not None:
                    cap = cv2.VideoCapture(cid, backend)
                else:
                    cap = cv2.VideoCapture(cid)
                if cap.isOpened():
                    ret, _ = cap.read()
                    if ret:
                        return cap
                cap.release()
            except Exception:
                pass
    return None


def register_student(roll_number, name, gender, degree, year, branch, section):
    if student_exists(roll_number):
        return False, f"Roll Number {roll_number} is already registered!"

    if not add_student(roll_number, name, gender, degree, year, branch, section):
        return False, "Database insertion failed."

    student_dir = Path(KNOWN_FACES_DIR) / roll_number
    student_dir.mkdir(parents=True, exist_ok=True)

    instructions = [
        "Look STRAIGHT at the camera",
        "Turn your head slightly LEFT",
        "Turn your head slightly RIGHT",
        "Tilt your head slightly UP",
        "Tilt your head slightly DOWN"
    ]

    # Open camera with DirectShow fallback
    cap = get_camera(CAMERA_ID)
    if cap is None or not cap.isOpened():
        delete_student(roll_number)
        if student_dir.exists():
            shutil.rmtree(student_dir)
        return False, f"Unable to open camera (Device ID {CAMERA_ID}). Please verify that your webcam is connected and not in use by another app."

    # Warm up camera sensor
    for _ in range(5):
        cap.read()

    try:
        detector = FaceDetector()
    except Exception as e:
        cap.release()
        delete_student(roll_number)
        if student_dir.exists():
            shutil.rmtree(student_dir)
        return False, f"Failed to initialize Face Detection model: {str(e)}"

    count = 0
    aborted = False
    BLUR_THRESHOLD = 65

    win_title = "SmartClass Vision - Student Registration Capture"
    cv2.namedWindow(win_title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_title, 760, 560)
    cv2.setWindowProperty(win_title, cv2.WND_PROP_TOPMOST, 1)

    while count < 5:
        ret, frame = cap.read()
        if not ret:
            break

        # Check if window was closed via 'X'
        try:
            if cv2.getWindowProperty(win_title, cv2.WND_PROP_VISIBLE) < 1:
                aborted = True
                break
        except Exception:
            pass

        clean_frame = frame.copy()
        h, w = frame.shape[:2]

        processed_frame, cropped_faces = detector.detect_faces(frame)
        is_aligned = False
        captured_crop = None

        if len(cropped_faces) == 1:
            fx1, fy1, fx2, fy2 = cropped_faces[0]["coords"]
            # Dynamic crop with 30% padding around detected face
            pad_w = int((fx2 - fx1) * 0.3)
            pad_h = int((fy2 - fy1) * 0.4)
            cx1 = max(0, fx1 - pad_w)
            cy1 = max(0, fy1 - pad_h)
            cx2 = min(w, fx2 + pad_w)
            cy2 = min(h, fy2 + int(pad_h * 0.4))

            captured_crop = clean_frame[cy1:cy2, cx1:cx2]
            is_aligned = True
            color = (0, 255, 0)
            msg = "Face Locked! Press 'C' or Spacebar to Capture"

            # Draw green box around student face
            cv2.rectangle(processed_frame, (fx1, fy1), (fx2, fy2), color, 3)
            cv2.circle(processed_frame, ((fx1 + fx2) // 2, (fy1 + fy2) // 2), 4, color, -1)
        elif len(cropped_faces) > 1:
            msg = "Multiple faces detected! Only 1 student allowed in frame."
            color = (0, 0, 255)
        else:
            msg = "Looking for student face... Please face the camera"
            color = (0, 165, 255)

        # Header Info Banner
        cv2.rectangle(processed_frame, (0, 0), (w, 58), (20, 20, 20), -1)
        cv2.putText(processed_frame, f"Student: {name} ({roll_number}) | Pose {count + 1}/5", (15, 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
        cv2.putText(processed_frame, f"Pose Instruction: {instructions[count]}", (15, 49),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 200), 2)

        # Status text in center
        cv2.rectangle(processed_frame, (10, h - 85), (w - 10, h - 50), (20, 20, 20), -1)
        cv2.putText(processed_frame, msg, (20, h - 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)

        # Footer Hint Banner
        cv2.rectangle(processed_frame, (0, h - 45), (w, h), (15, 15, 15), -1)
        hint = "Press 'C' or Spacebar to Capture  |  Press 'Q' or ESC to Cancel"
        cv2.putText(processed_frame, hint, (20, h - 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if is_aligned else (180, 180, 180), 2)

        cv2.imshow(win_title, processed_frame)
        key = cv2.waitKey(20) & 0xFF

        is_capture_key = key in (ord('c'), ord('C'), 32, 13)  # 'c', 'C', Space, Enter
        is_cancel_key = key in (ord('q'), ord('Q'), 27)       # 'q', 'Q', ESC

        if is_cancel_key:
            aborted = True
            break
        elif is_capture_key and is_aligned and captured_crop is not None and captured_crop.size > 0:
            img_path = student_dir / f"{roll_number}_{count}.jpg"
            cv2.imwrite(str(img_path), captured_crop)
            count += 1
            # Visual feedback on capture
            flash = processed_frame.copy()
            cv2.putText(flash, f"Pose {count}/5 CAPTURED!", (w // 4, h // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0), 3)
            cv2.imshow(win_title, flash)
            cv2.waitKey(300)

    cap.release()
    cv2.destroyAllWindows()

    if count < 5 or aborted:
        delete_student(roll_number)
        if student_dir.exists():
            shutil.rmtree(student_dir)
        if aborted:
            return False, "Registration cancelled by user. Incomplete data cleaned up."
        else:
            return False, f"Registration stopped: Only captured {count}/5 poses. Please try again."

    return True, f"Registration complete for {name} ({roll_number})! All 5 poses captured successfully."