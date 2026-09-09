# 🎓 SmartClass Vision (v0.2 Enterprise Edition)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-blueviolet.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![OpenCV YuNet](https://img.shields.io/badge/Face%20Detection-OpenCV%20YuNet%20DNN-brightgreen.svg)](https://github.com/opencv/opencv_zoo)
[![ArcFace](https://img.shields.io/badge/Face%20Recognition-InsightFace%20ArcFace-orange.svg)](https://github.com/deepinsight/insightface)
[![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)](https://www.sqlite.org/)

An automated, high-precision **AI-Powered Face Recognition Attendance & Classroom Management System** built with **OpenCV YuNet Deep Neural Network (DNN)**, **ArcFace Biometric Embeddings**, and **CustomTkinter**. Designed specifically for academic institutions, **SmartClass Vision** eliminates proxy attendance, enforces strict branch/section isolation, provides multi-layered anti-spoofing protection, and offers a comprehensive role-based administrative control suite.

---

## 🌟 Key Highlights & Features

### 👁️ High-Accuracy Face Detection & Recognition
- **OpenCV YuNet DNN Detector**: Dedicated neural network detecting frontal and angled human faces, filtering out non-human background objects.
- **YuNet 5-Point Landmark Affine Alignment**: Standardized 112×112 facial alignment based on eye, nose, and mouth corner coordinates to normalize head pose before feature extraction.
- **InsightFace ArcFace 512-D Embeddings**: Vectorized ArcFace backbone utilizing Cosine Similarity with quality-filtered student centroid models.
- **10-Shot Multi-Angle Temporal Consensus**: Captures 10 successive audit frames over a ~25-second window. Any student must achieve at least 3 consistent high-similarity matches (>= 0.58) across the capture window to verify presence.
- **Ambiguity Margin Guard**: Enforces minimum separation (>= 0.06) between top-1 and top-2 candidates, preventing false matches between similar-looking students.

### 📸 Intelligent Student Registration & Face Quality Gate
- **Pose & Yaw Asymmetry Filter**: Landmark asymmetry gating rejects extreme side-profile angles during registration and scanning.
- **Laplacian Sharpness Analysis**: Automatically filters out motion-blurred frames.
- **Luma Exposure & Contrast Checking**: Dynamic brightness and contrast analysis ensures proper indoor lighting before accepting facial embeddings into memory.
- **Minimum Resolution Gate**: Prevents truncated or low-resolution face crops (< 45px) from degrading recognition accuracy.

### 🛡️ Multi-Layer Anti-Spoofing & Security
- **Texture Analysis**: High-frequency texture and Laplacian variance inspection to detect printed photo attacks and paper cutouts.
- **Chromatic Reflection Check**: Color-channel distribution analysis to block screen replays from smartphones, tablets, or laptops.
- **Audit Trails**: Security incidents and spoof attempts are recorded with snapshots stored in `data/unknown_faces/`.
- **HMAC-SHA256 Cryptographic Signing**: Every attendance CSV sheet generated is cryptographically signed with HMAC-SHA256 to guarantee audit immutability and tamper resistance.

### 🔒 Role-Based Access Control & Strict Section Isolation
- **Dual-Tier Authentication**: Faculty (Teacher) and System Administrator role isolation with Argon2 / PBKDF2 credential hashing.
- **Section & Branch Validation**: Validates that recognized students belong to the target Course, Degree, Year, Branch, and Section before granting attendance. Cross-section attendees are logged and rejected.
- **Brute-Force Lockout Defense**: Progressive lockout protection against automated password guessing.
- **Admin Master Key Verification**: Institutional security key required to authorize administrator account creation.

### 📊 Administrative Command Center & GUI Dashboard
- **Real-Time Section Roster**: Dashboard table automatically updates and highlights verified students as **PRESENT** in green immediately upon scan completion.
- **Granular Record Management**: Delete single student records or entire batch section records directly with admin authorization.
- **Curriculum & Faculty Matrix**: Map subjects, faculty members, sections, and student allocations.
- **Automated Database Backups**: One-click SQLite snapshots and database integrity restoration.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **GUI & UI Design** | CustomTkinter (Dark Mode, Responsive Layout) |
| **Face Detection** | OpenCV YuNet Deep Neural Network (`face_detection_yunet_2023mar.onnx`) |
| **Face Alignment** | 5-Point Landmark Affine Transformation (112×112) |
| **Face Recognition**| DeepFace / ArcFace (512-D Cosine Centroids) |
| **Computer Vision** | OpenCV (`cv2`), NumPy, PIL |
| **Database & Storage**| SQLite3, Pandas, Pickle |
| **Security & Audits** | PBKDF2 / Argon2, HMAC-SHA256, Audit Logging |

---

## 📂 Project Structure

```text
SmartClassVision/
├── data/                       # Local database, unknown face captures, embeddings
│   ├── attendance_records/     # Auto-generated daily attendance CSV sheets
│   ├── backups/                # SQLite database snapshots
│   ├── class_photos/           # Timestamped multi-shot audit photos
│   ├── database/               # Master SQLite database (smartclass.db)
│   ├── known_faces/            # Enrolled student face capture datasets (by Roll Number)
│   ├── unknown_faces/          # Spoof incident and audit snapshots
│   └── embeddings.pkl          # Precomputed quality-filtered ArcFace centroids
├── models/                     # Deep learning model weights
│   ├── face_detection_yunet_2023mar.onnx
│   └── weights/arcface_weights.h5
├── src/                        # Core application modules
│   ├── anti_spoof.py           # Texture, reflection, blur, and pose quality gates
│   ├── attendance_logic.py     # 10-shot temporal consensus attendance engine
│   ├── database.py             # SQLite schema, HMAC signing, RBAC, and queries
│   ├── detector.py             # OpenCV YuNet DNN detector with 5-point alignment
│   ├── recognizer.py           # Vectorized ArcFace inference & centroid matching
│   └── registration.py         # Multi-shot student dataset registration
├── utils/
│   └── config.py               # Path configurations and global constants
├── tests/                      # Automated test suites
│   ├── test_approach_a_isolation.py
│   └── test_enterprise_security.py
├── test_admin_portal.py        # Admin portal backend validation tests
├── gui.py                      # Main CustomTkinter desktop interface
├── requirements.txt            # Python dependencies
├── run.bat                     # Windows quick start launcher
└── README.md                   # Project documentation
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- **Python 3.10 or higher**
- **Git**
- Webcam or external camera connected

### 2. Clone the Repository
```bash
git clone https://github.com/sandeepsagar18/Smart_Ai_class.git
cd Smart_Ai_class
```

### 3. Create a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Launch the Application
```bash
python gui.py
```
*(On Windows, you can also double-click `run.bat`)*

---

## 🔑 Default Credentials & Quick Start

Upon first run, the database automatically initializes a default Administrator account:

| Account Type | Employee ID | Default Password |
| :--- | :--- | :--- |
| **System Administrator** | `ADMIN01` | `admin123` |

> ⚠️ **Security Notice**: Change the default administrator password immediately after initial login via the session bar. Default Admin Master Key for creating new admin accounts: `SmartClass@Admin#2026`.

---

## 🧪 Running Automated Tests

Run the backend test suites to verify database operations, RBAC isolation, anti-spoofing, and attendance integrity:

```bash
# Run Admin Portal verification tests
python test_admin_portal.py

# Run Security & Anti-Spoofing tests
python tests/test_enterprise_security.py

# Run Section Isolation tests
python tests/test_approach_a_isolation.py
```

---

## 👨‍💻 Author & Maintainer

Developed & Maintained by **Sandeep Sagar**  
- **GitHub**: [@sandeepsagar18](https://github.com/sandeepsagar18)  
- **Repository**: [Smart_Ai_class](https://github.com/sandeepsagar18/Smart_Ai_class.git)  
- **Email**: sandeepsagarkumar85@gmail.com  

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
