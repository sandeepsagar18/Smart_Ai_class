# 🎓 SmartClass Vision (v0.2 Enterprise Edition)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-blueviolet.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![OpenCV YuNet](https://img.shields.io/badge/Face%20Detection-OpenCV%20YuNet%20DNN-brightgreen.svg)](https://github.com/opencv/opencv_zoo)
[![DeepFace](https://img.shields.io/badge/Recognition-FaceNet512%20%2F%20ArcFace-orange.svg)](https://github.com/serengil/deepface)
[![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)](https://www.sqlite.org/)

An automated, high-precision **AI-Powered Face Recognition Attendance & Management System** built with **OpenCV YuNet Deep Neural Network**, **DeepFace (FaceNet512 / ArcFace)**, and **CustomTkinter**. Designed specifically for institutional classrooms, **SmartClass Vision** eliminates proxy attendance, enforces strict branch/section isolation, provides multi-layered anti-spoofing protection, and offers a comprehensive role-based administrative control suite.

---

## 🌟 Key Highlights & Features

### 👁️ Dedicated Human Face Detection & Recognition
- **OpenCV YuNet DNN Detector**: Dedicated human face detection neural network. Exclusively tracks human facial landmarks and **100% ignores background non-face objects** (such as TV screens, monitors, chairs, and windows).
- **FaceNet512 Embeddings with Section-Aware Prioritizing**: During class attendance, the AI prioritizes matching against the specific enrolled section roster ($O(K)$ search reduction), eliminating cross-section student confusion.
- **Real-Time Multi-Face Bounding Overlays**: Live video scanner displays real-time face bounding boxes and an active student counter (`Live Faces: X`).
- **Single-Shot Consensus (`REQUIRED_MATCHES = 1`)**: Fast temporal consensus with hardware camera buffer flush, ensuring no enrolled student is discarded as a glitch.

### 📸 Intelligent Student Registration Quality Gate
- **Real-Time Blur & Sharpness Gate**: Uses Laplacian variance analysis (`threshold >= 80.0`). Motion-blurred frames are rejected in real-time.
- **Exposure & Lighting Check**: Automatic Luma analysis (`45 <= Brightness <= 210`) prevents shadows or overexposed captures.
- **Face Resolution & Distance Threshold**: Ensures minimum face crop size (`>= 70x70 px`) so students are properly framed.
- **Center Alignment Guard**: Prevents truncated or cut-off face captures along camera borders.

### 🛡️ Multi-Layer Anti-Spoofing & Liveness Detection
- **Texture Analysis**: Laplacian variance frequency filtering to detect low-frequency blur from printed photos or paper masks.
- **Chromatic Reflection Check**: Color channel balance analysis to detect phone, tablet, and monitor screen reflection artifacts.
- **Dynamic Motion & Blink Verification**: Real-time facial micro-motion checks during active class scan mode.

### 🗑️ Granular Attendance Deletion (Admin Portal)
- **Particular Student Deletion**: Delete attendance for a specific student by Roll Number with optional Date / Subject filters.
- **Particular Batch Deletion**: Purge attendance for an entire class batch (Branch + Section) with single-click `TODAY` quick filters.
- **Dual-Store Synchronization**: Instantly deletes matching records from both SQLite Database (`smartclass.db`) and CSV audit sheets (`data/attendance_records/`).
- **Security Confirmation & Audit Trails**: Every deletion requires Admin password re-authentication and is permanently logged in the Enterprise Security Audit Trail.

### 🔒 Role-Based Access Control & Section Isolation
- **Dual-Tier Authentication**: Secure role isolation for **Faculty (Teachers)** and **Institutional Administrators**.
- **Section & Branch Isolation**: Teachers are restricted to scanning attendance only for students enrolled in their assigned degree, year, branch, and section.
- **Brute-Force Lockout Defense**: Progressive lockout defense against repeated failed password attempts.
- **Admin Master Key Verification**: Institutional authorization key required to register administrator accounts.

### 📊 Administrative Command Center & Audit Suite
- **Faculty Management**: Allot subjects, reassign faculty, reset credentials, promote/demote administrator rights.
- **Student Directory & Section Transfers**: Real-time roster search, batch student enrollment, section transfers, and deletion.
- **Curriculum Matrix**: Comprehensive mappings between courses, semesters, branches, sections, and faculty members.
- **HMAC Cryptographic Signing**: Every recorded attendance entry is cryptographically hashed with SHA-256 HMAC signatures to prevent tampering.
- **Automated Database Backups**: One-click SQLite snapshots and system health diagnostics.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **GUI & UI Design** | CustomTkinter (Dark Mode, Responsive Kiosk Layout) |
| **Face Detection** | OpenCV YuNet Deep Neural Network (`face_detection_yunet_2023mar.onnx`) |
| **Face Embeddings** | DeepFace (FaceNet512 Architecture) |
| **Computer Vision** | OpenCV (`cv2`), NumPy, PIL |
| **Database & Storage**| SQLite3, Pandas, Pickle |
| **Security & Audits** | Argon2 / PBKDF2 Hashing, HMAC-SHA256, Integrity Checksums |

---

## 📂 Project Structure

```text
SmartClassVision/
├── data/                       # Local database, unknown face captures, embeddings
│   ├── attendance/             # Auto-generated daily attendance CSV sheets
│   ├── backups/                # SQLite database snapshots
│   ├── students/               # Enrolled student face capture datasets
│   └── smartclass.db           # Master SQLite relational database
├── src/                        # Core application modules
│   ├── anti_spoof.py           # Texture, reflection, and liveness analysis
│   ├── attendance_logic.py     # Real-time multi-shot attendance capture engine
│   ├── database.py             # SQLite schema, HMAC signing, RBAC, and queries
│   ├── detector.py             # YOLOv8 face detector wrapper
│   ├── recognizer.py           # FaceNet512 embedding extraction and training
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

> ⚠️ **Security Notice**: Change the default administrator password immediately after initial login via the top session bar. Default Admin Master Key for creating new admin accounts: `SmartClass@Admin#2026`.

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

