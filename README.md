# 🎓 SmartClass Vision

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-blueviolet.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![OpenCV YuNet](https://img.shields.io/badge/Face%20Detection-OpenCV%20YuNet%20DNN-brightgreen.svg)](https://github.com/opencv/opencv_zoo)
[![ArcFace](https://img.shields.io/badge/Face%20Recognition-InsightFace%20ArcFace-orange.svg)](https://github.com/deepinsight/insightface)
[![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)](https://www.sqlite.org/)

An automated, high-precision **AI-Powered Face Recognition Attendance & Classroom Management System** built with **OpenCV YuNet Deep Neural Network (DNN)**, **InsightFace ArcFace 512-D Embeddings**, and **CustomTkinter**. Designed specifically for colleges and schools to eliminate proxy attendance, enforce strict section isolation, provide anti-spoofing defense, and deliver comprehensive administrative control.

---

## 🚀 Key System Capabilities

### 1. OpenCV YuNet DNN Face Detection & 5-Point Alignment
- **Dedicated Face Detection DNN**: Uses `face_detection_yunet_2023mar.onnx` to detect human faces in real time while ignoring non-face background objects (monitors, chairs, posters).
- **5-Point Landmark Normalization**: Automatically extracts 5 key facial coordinates (both eyes, nose tip, both mouth corners) and applies an affine transformation to normalize head pose into standard $112 \times 112$ aligned crops before recognition.

### 2. InsightFace ArcFace Biometric Recognition
- **512-Dimensional Deep Metric Hyperspace**: Live faces are encoded with ArcFace (Additive Angular Margin Loss) deep learning feature vectors.
- **Centroid Profile Matching**: Computes Cosine Similarity against quality-filtered student centroid models.
- **Ambiguity Margin Guard**: Requires top match to hold a $\ge 0.06$ margin over the second-place candidate to avoid false identity swaps.

### 3. Multi-Shot Temporal Consensus Engine
- **25-Second Batch Scanning**: Captures 10 multi-angle audit frames over ~25 seconds with a 2.5-second interval between snaps.
- **Consensus Rule**: A student must achieve at least 3 high-similarity matches ($\ge 0.58$) across the 10 shots to pass consensus and be marked **PRESENT**.
- **Real-Time Section Roster Update**: Immediately switches the dashboard view to the scanned class and updates attendance status to **PRESENT** in green.

### 4. Enterprise Security & Anti-Spoofing
- **Face Quality Gates**: Rejects motion blur via Laplacian variance, enforces balanced illumination, and discards extreme side-profile poses.
- **Anti-Spoofing Defense**: Texture and chromatic balance analysis to detect printed photo attacks and screen replays.
- **Section & Branch Isolation**: Only marks attendance for students registered in the teacher's selected Degree, Year, Branch, and Section. Out-of-section faces are rejected.
- **Cryptographic HMAC-SHA256 Signing**: Every generated CSV attendance sheet is digitally signed with an HMAC-SHA256 signature to guarantee tamper-proof audit records.

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **GUI Framework** | CustomTkinter | Modern dark-mode responsive kiosk interface |
| **Face Detection** | OpenCV YuNet DNN (`ONNX`) | Real-time face detection and 5-point landmark extraction |
| **Face Alignment** | Affine Transformation | Standardized $112 \times 112$ canonical face crops |
| **Face Recognition** | InsightFace ArcFace | 512-D angular margin biometric embeddings |
| **Computer Vision** | OpenCV (`cv2`), NumPy, PIL | Image transformations, Laplacian filtering, video streaming |
| **Database** | SQLite3, Pandas, Pickle | Student database, subject enrollment, centroid storage |
| **Security** | Argon2 / PBKDF2, HMAC-SHA256 | Credential hashing and tamper-proof attendance sheets |

---

## 📂 Project Architecture

```text
SmartClassVision/
├── data/
│   ├── attendance_records/     # Auto-generated and cryptographically signed CSV sheets
│   ├── backups/                # SQLite database snapshots
│   ├── class_photos/           # Timestamped 10-shot session audit photos
│   ├── database/               # Master SQLite database (smartclass.db)
│   ├── known_faces/            # 5-shot student registration photos (by Roll Number)
│   ├── unknown_faces/          # Spoof incidents and audit captures
│   └── embeddings.pkl          # Quality-filtered ArcFace centroids for all students
├── models/
│   ├── face_detection_yunet_2023mar.onnx   # OpenCV YuNet face detector model
│   └── weights/                            # ArcFace neural network weights
├── src/
│   ├── anti_spoof.py           # Texture analysis, blur, and pose quality gates
│   ├── attendance_logic.py     # 10-shot multi-angle attendance engine
│   ├── database.py             # SQLite schema, HMAC signatures, RBAC queries
│   ├── detector.py             # OpenCV YuNet DNN detector with 5-point alignment
│   ├── recognizer.py           # ArcFace inference and centroid cosine matching
│   └── registration.py         # Multi-shot student dataset registration
├── utils/
│   └── config.py               # Central threshold and path configuration
├── tests/                      # Automated system and security test suites
├── gui.py                      # Main desktop application interface
├── requirements.txt            # Python dependencies
├── run.bat                     # Windows quick launch script
└── README.md                   # Project documentation
```

---

## ⚙️ Quick Start Guide

### 1. Clone & Setup Environment
```bash
git clone https://github.com/sandeepsagar18/Smart_Ai_class.git
cd Smart_Ai_class

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python gui.py
```
*(Or double-click `run.bat` on Windows)*

---

## 🔑 Default Credentials

On initial startup, the database creates a default administrative account:

| Role | Employee ID | Default Password |
| :--- | :--- | :--- |
| **System Administrator** | `ADMIN01` | `admin123` |

> ⚠️ **Note**: Change the default admin password after initial login. Master Key for registering new admin accounts: `SmartClass@Admin#2026`.

---

## 👨‍💻 Author & Maintainer

Developed & Maintained by **Sandeep Sagar**  
- **GitHub**: [@sandeepsagar18](https://github.com/sandeepsagar18)  
- **Repository**: [Smart_Ai_class](https://github.com/sandeepsagar18/Smart_Ai_class.git)  
- **Email**: sandeepsagarkumar85@gmail.com  

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
