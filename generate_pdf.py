import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(54, 750, "SmartClass Vision - Project Documentation & Technical Specification")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 742, 612 - 54, 742)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 36, page_text)
        self.drawString(54, 36, "SmartClass Vision System Documentation")
        self.line(54, 48, 612 - 54, 48)
        self.restoreState()

def generate_pdf(filename="SmartClass_Vision_Project_Documentation.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=64,
        bottomMargin=64
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0f172a'),
        alignment=1,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#2563eb'),
        alignment=1,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=12,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#2563eb'),
        spaceBefore=8,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1e293b')
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white
    )

    story = []

    story.append(Paragraph("SmartClass Vision", title_style))
    story.append(Paragraph("Automated AI Face Recognition Attendance & Classroom Governance System", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563eb'), spaceBefore=0, spaceAfter=12))

    meta_data = [
        [
            Paragraph("<b>Repository:</b> github.com/sandeepsagar18/Smart_Ai_class", table_cell_style),
            Paragraph("<b>Release:</b> v0.2 Production", table_cell_style)
        ],
        [
            Paragraph("<b>Platform:</b> Windows / Desktop Application", table_cell_style),
            Paragraph("<b>Runtime:</b> Python 3.10+ / CustomTkinter", table_cell_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[3.6 * inch, 3.4 * inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("1. Executive Overview & Problem Statement", h1_style))
    story.append(Paragraph(
        "<b>SmartClass Vision</b> is a computer vision solution designed to automate classroom attendance and eliminate proxy attendance. Traditional attendance workflows (manual roll calls, sign-in paper sheets, and RFID badge swipes) are prone to proxy marking, administrative burden, and human error. SmartClass Vision provides fast multi-face detection, biometric identification, anti-spoofing liveness verification, and role-based access control (RBAC).",
        body_style
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("2. Machine Learning & Deep Learning Architecture", h1_style))
    story.append(Paragraph(
        "The system incorporates a two-stage deep learning pipeline combining convolutional neural network (CNN) face detection with deep metric learning:",
        body_style
    ))

    ml_data = [
        [
            Paragraph("Module", table_header_style),
            Paragraph("Model / Algorithm", table_header_style),
            Paragraph("ML / DL Mechanism", table_header_style),
            Paragraph("Output", table_header_style)
        ],
        [
            Paragraph("<b>Face Detection</b>", table_cell_style),
            Paragraph("Ultralytics YOLOv8n", table_cell_style),
            Paragraph("Single-stage Deep CNN object detector. Detects and tracks faces across varying lighting and classroom angles.", table_cell_style),
            Paragraph("Bounding boxes [x1, y1, x2, y2] & cropped faces", table_cell_style)
        ],
        [
            Paragraph("<b>Biometric Embedding</b>", table_cell_style),
            Paragraph("FaceNet512 (DeepFace)", table_cell_style),
            Paragraph("Deep Metric Learning trained on Triplet Loss. Maps facial geometry into a dense 512-dimensional Euclidean hyperspace.", table_cell_style),
            Paragraph("512-D continuous floating-point vector", table_cell_style)
        ],
        [
            Paragraph("<b>Face Identification</b>", table_cell_style),
            Paragraph("Cosine Distance Metric", table_cell_style),
            Paragraph("Computes Cosine Similarity: <i>cos(u, v) = (u . v) / (||u|| ||v||)</i>. Compares live embedding against saved student vectors. Threshold: &lt; 0.25.", table_cell_style),
            Paragraph("Roll Number & Match Confidence %", table_cell_style)
        ],
        [
            Paragraph("<b>Anti-Spoofing Guard</b>", table_cell_style),
            Paragraph("Laplacian Filter & Chroma Mask", table_cell_style),
            Paragraph("Analyzes Laplacian frequency variance (detects paper blur / screen moire) and YCrCb/HSV skin locus balance (detects display glare).", table_cell_style),
            Paragraph("Liveness score (Live Human vs Fake)", table_cell_style)
        ]
    ]

    ml_table = Table(ml_data, colWidths=[1.3 * inch, 1.4 * inch, 2.8 * inch, 1.5 * inch])
    ml_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(ml_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("3. Functional Modules & Security Features", h1_style))
    story.append(Paragraph("<b>A. Role-Isolated Authentication Architecture:</b>", h2_style))
    story.append(Paragraph("- <b>Teacher Portal:</b> Contains Teacher Login and Create Teacher account. Keeps classroom operations clean and free of administrative controls.", bullet_style))
    story.append(Paragraph("- <b>Admin Portal:</b> Protected interface providing Admin Login and Create Admin account, gated by an institutional Master Authorization Key.", bullet_style))
    story.append(Paragraph("- <b>Brute-Force Lockout Defense:</b> Automatically locks an account after 5 consecutive failed password attempts.", bullet_style))
    story.append(Paragraph("- <b>Session Auto-Lock:</b> Automatically locks active classroom terminals after 10 minutes of inactivity.", bullet_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>B. Interactive Student Registration & Profile Directory:</b>", h2_style))
    story.append(Paragraph("- <b>Multi-Angle Capture:</b> Directs students to look straight, turn left, turn right, and tilt up/down to store a 5-shot training dataset.", bullet_style))
    story.append(Paragraph("- <b>Student Profile Modal:</b> Searching by Roll Number opens a verified Student Profile Card showing the captured face photo, roll number, name, degree, branch, section, and enrollment status.", bullet_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>C. Batch Class Attendance Engine:</b>", h2_style))
    story.append(Paragraph("- <b>Section Isolation:</b> Restricts scanning strictly to students enrolled in the teacher's selected degree, year, branch, and section.", bullet_style))
    story.append(Paragraph("- <b>Temporal Multi-Shot Verification:</b> Validates identity over multiple frames to avoid false-positive attendance marks.", bullet_style))
    story.append(Paragraph("- <b>Cryptographic HMAC-SHA256 Signatures:</b> Every generated attendance sheet is signed with SHA-256 HMAC checksums to ensure file integrity.", bullet_style))

    story.append(Spacer(1, 10))

    story.append(Paragraph("4. Technology Stack", h1_style))
    tech_data = [
        [Paragraph("Layer", table_header_style), Paragraph("Technology", table_header_style), Paragraph("Role", table_header_style)],
        [Paragraph("GUI Framework", table_cell_style), Paragraph("CustomTkinter, Tkinter", table_cell_style), Paragraph("Desktop interface with dark mode and kiosk layout", table_cell_style)],
        [Paragraph("Computer Vision", table_cell_style), Paragraph("OpenCV (cv2), Pillow (PIL)", table_cell_style), Paragraph("Real-time webcam stream, DirectShow capture, face crops", table_cell_style)],
        [Paragraph("Deep Learning", table_cell_style), Paragraph("PyTorch, TensorFlow, DeepFace, YOLOv8", table_cell_style), Paragraph("Face detection inference and FaceNet512 512-D embeddings", table_cell_style)],
        [Paragraph("Database", table_cell_style), Paragraph("SQLite3, Pandas, Pickle", table_cell_style), Paragraph("Master database, attendance exports, binary embedding storage", table_cell_style)],
        [Paragraph("Security", table_cell_style), Paragraph("HMAC-SHA256, Salted Hashes", table_cell_style), Paragraph("Argon2/PBKDF2 style hashing, attendance file tamper detection", table_cell_style)]
    ]
    tech_table = Table(tech_data, colWidths=[1.5 * inch, 2.2 * inch, 3.3 * inch])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f766e')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("5. Default Credentials & Quick Reference", h1_style))
    cred_data = [
        [Paragraph("Item", table_header_style), Paragraph("Value", table_header_style), Paragraph("Description", table_header_style)],
        [Paragraph("Default Admin Account", table_cell_style), Paragraph("<b>ID:</b> ADMIN01<br/><b>Password:</b> admin123", table_cell_style), Paragraph("Full admin command portal, faculty allotments, diagnostics", table_cell_style)],
        [Paragraph("Admin Master Auth Key", table_cell_style), Paragraph("<code>SmartClass@Admin#2026</code>", table_cell_style), Paragraph("Required for creating administrator accounts", table_cell_style)],
        [Paragraph("Quick Launch Script", table_cell_style), Paragraph("<code>run.bat</code> or <code>python gui.py</code>", table_cell_style), Paragraph("Starts the desktop application within the virtual environment", table_cell_style)]
    ]
    cred_table = Table(cred_data, colWidths=[1.8 * inch, 2.4 * inch, 2.8 * inch])
    cred_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#475569')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(cred_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print("PDF Successfully Generated: " + filename)

if __name__ == "__main__":
    generate_pdf("D:\\smart_ai\\SmartClassVision\\SmartClass_Vision_Project_Documentation.pdf")
